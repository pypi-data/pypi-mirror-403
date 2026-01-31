"""
Moonwell wstETH Loop Strategy

A leveraged liquid-staking carry on Base that loops USDC → borrow WETH → swap to wstETH → lend wstETH.
The loop repeats while keeping debt as a fraction F of borrow capacity, chosen conservatively
so the position remains safe under a stETH/ETH depeg.
"""

import asyncio
import time
from typing import Any

import httpx
from loguru import logger

from wayfinder_paths.adapters.balance_adapter.adapter import BalanceAdapter
from wayfinder_paths.adapters.brap_adapter.adapter import BRAPAdapter
from wayfinder_paths.adapters.ledger_adapter.adapter import LedgerAdapter
from wayfinder_paths.adapters.moonwell_adapter.adapter import MoonwellAdapter
from wayfinder_paths.adapters.token_adapter.adapter import TokenAdapter
from wayfinder_paths.core.services.base import Web3Service
from wayfinder_paths.core.services.local_token_txn import LocalTokenTxnService
from wayfinder_paths.core.services.web3_service import DefaultWeb3Service
from wayfinder_paths.core.strategies.descriptors import (
    Complexity,
    Directionality,
    Frequency,
    StratDescriptor,
    TokenExposure,
    Volatility,
)
from wayfinder_paths.core.strategies.Strategy import StatusDict, StatusTuple, Strategy
from wayfinder_paths.core.wallets.WalletManager import WalletManager
from wayfinder_paths.policies.enso import ENSO_ROUTER, enso_swap
from wayfinder_paths.policies.erc20 import erc20_spender_for_any_token
from wayfinder_paths.policies.moonwell import (
    M_USDC,
    M_WETH,
    M_WSTETH,
    WETH,
    moonwell_comptroller_enter_markets_or_claim_rewards,
    musdc_mint_or_approve_or_redeem,
    mweth_approve_or_borrow_or_repay,
    mwsteth_approve_or_mint_or_redeem,
    weth_deposit,
)

# Token addresses on Base
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
WSTETH = "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452"

# Token IDs
USDC_TOKEN_ID = "usd-coin-base"
WETH_TOKEN_ID = "l2-standard-bridged-weth-base-base"
WSTETH_TOKEN_ID = "superbridge-bridged-wsteth-base-base"
ETH_TOKEN_ID = "ethereum-base"
WELL_TOKEN_ID = "moonwell-artemis-base"
STETH_TOKEN_ID = "staked-ether-ethereum"

# Base chain ID
BASE_CHAIN_ID = 8453

# Safety parameters
# 0.98 = 2% safety margin when borrowing to avoid hitting exact liquidation threshold
COLLATERAL_SAFETY_FACTOR = 0.98


class SwapOutcomeUnknownError(RuntimeError):
    """Raised when a swap transaction's outcome is unknown (e.g., receipt timeout).

    In this case we must not retry (risk duplicate fills) and should halt the strategy
    so the caller can inspect on-chain state.
    """


class MoonwellWstethLoopStrategy(Strategy):
    """Leveraged wstETH yield strategy using Moonwell lending protocol on Base."""

    name = "Moonwell wstETH Loop Strategy"
    description = "Leveraged wstETH yield strategy using Moonwell lending protocol."
    summary = "Loop wstETH on Moonwell for amplified staking yields."

    # Strategy parameters
    # Minimum Base ETH (in ETH) required for gas fees (Base L2)
    MIN_GAS = 0.002
    MAINTENANCE_GAS = MIN_GAS / 10
    # When wrapping ETH to WETH for swaps/repayment, avoid draining gas below this floor.
    # We can dip below MIN_GAS temporarily, but should not wipe the wallet.
    WRAP_GAS_RESERVE = 0.0014
    MIN_USDC_DEPOSIT = 20.0  # Minimum USDC deposit required as initial collateral
    MAX_DEPEG = 0.01  # Maximum allowed stETH depeg threshold (1%)
    MAX_HEALTH_FACTOR = 1.5
    MIN_HEALTH_FACTOR = 1.2
    # Continue levering up if HF is more than this amount above MIN_HEALTH_FACTOR
    HF_LEVER_UP_BUFFER = 0.05  # Lever up if HF > MIN + 0.05 (i.e., > 1.25)
    _MAX_LOOP_LIMIT = 30  # Prevents infinite loops

    # Parameters
    leverage_limit = 10  # Limit on leverage multiplier
    min_withdraw_usd = 2
    max_swap_retries = 3  # Maximum number of swap retry attempts
    swap_slippage_tolerance = 0.005  # Base slippage of 50 bps
    MAX_SLIPPAGE_TOLERANCE = 0.03  # 3% absolute maximum slippage to prevent MEV attacks
    PRICE_STALENESS_THRESHOLD = 300  # 5 minutes - max age for cached prices

    # 50 basis points (0.0050) - minimum leverage gain per loop iteration to continue
    # If marginal gain drops below this, stop looping as gas costs outweigh benefit
    _MIN_LEVERAGE_GAIN_BPS = 50e-4  # 50 bps = 0.50%

    INFO = StratDescriptor(
        description="Leveraged wstETH carry: loops USDC → borrow WETH → swap wstETH → lend. "
        "Depeg-aware sizing with safety factor. ETH-neutral: WETH debt vs wstETH collateral.",
        summary="Leveraged wstETH carry on Base with depeg-aware sizing.",
        risk_description=f"Protocol risk is always present when engaging with DeFi strategies, this includes underlying DeFi protocols and Wayfinder itself. Additional risks include weth/wsteth depegging (this strategy tracks the peg and is robust up to {int(MAX_DEPEG * 100)}% depeg). The rate spread between weth borrow and wsteth lend may also turn negative. This will likely only be temporary and is very rare. If this persists manual withdraw may be needed.",
        gas_token_symbol="ETH",
        gas_token_id=ETH_TOKEN_ID,
        deposit_token_id=USDC_TOKEN_ID,
        minimum_net_deposit=20,
        gas_maximum=0.05,
        gas_threshold=0.01,
        volatility=Volatility.LOW,
        volatility_description="APYs can vary significantly but are almost always positive",
        directionality=Directionality.DELTA_NEUTRAL,
        directionality_description="Balances wstETH collateral and WETH debt so ETH delta stays close to flat.",
        complexity=Complexity.MEDIUM,
        complexity_description="Manages recursive lend/borrow loops, peg monitoring, and health-factor controls.",
        token_exposure=TokenExposure.MAJORS,
        token_exposure_description="Risk is concentrated in ETH (wstETH vs WETH) and USDC on Base.",
        frequency=Frequency.LOW,
        frequency_description="Runs every 2 hours but will trade rarely to minimize transaction fees.",
        return_drivers=["leveraged lend APY"],
        config={
            "deposit": {
                "description": "Lend USDC as seed collateral, then execute leverage loop.",
                "parameters": {
                    "main_token_amount": {
                        "type": "float",
                        "unit": "USDC tokens",
                        "description": "Amount of USDC to deposit as initial collateral.",
                        "minimum": 20.0,
                        "examples": ["100.0", "500.0", "1000.0"],
                    },
                    "gas_token_amount": {
                        "type": "float",
                        "unit": "ETH tokens",
                        "description": "Amount of ETH to transfer for gas.",
                        "minimum": 0.0,
                        "recommended": 0.01,
                    },
                },
                "result": "Delta-neutral leveraged wstETH position.",
            },
            "withdraw": {
                "description": "Unwind positions, repay debt, and return funds.",
                "parameters": {},
                "result": "All debt repaid, collateral returned in USDC.",
            },
            "update": {
                "description": "Rebalance positions and manage leverage.",
                "parameters": {},
                "result": "Position maintained at target leverage.",
            },
        },
    )

    def __init__(
        self,
        config: dict | None = None,
        *,
        main_wallet: dict | None = None,
        strategy_wallet: dict | None = None,
        simulation: bool = False,
        web3_service: Web3Service | None = None,
        api_key: str | None = None,
    ):
        super().__init__(api_key=api_key)
        merged_config: dict[str, Any] = dict(config or {})
        if main_wallet is not None:
            merged_config["main_wallet"] = main_wallet
        if strategy_wallet is not None:
            merged_config["strategy_wallet"] = strategy_wallet

        self.config = merged_config
        self.simulation = simulation
        self.web3_service = web3_service

        # Adapter references
        self.balance_adapter: BalanceAdapter | None = None
        self.moonwell_adapter: MoonwellAdapter | None = None
        self.brap_adapter: BRAPAdapter | None = None
        self.token_adapter: TokenAdapter | None = None
        self.ledger_adapter: LedgerAdapter | None = None

        # Token info cache
        self._token_info_cache: dict[str, dict] = {}
        self._token_price_cache: dict[str, float] = {}
        self._token_price_timestamps: dict[str, float] = {}

        try:
            main_wallet_cfg = self.config.get("main_wallet")
            strategy_wallet_cfg = self.config.get("strategy_wallet")

            if not strategy_wallet_cfg or not strategy_wallet_cfg.get("address"):
                raise ValueError(
                    "strategy_wallet not configured. Provide strategy_wallet address in config."
                )

            adapter_config = {
                "main_wallet": main_wallet_cfg or None,
                "strategy_wallet": strategy_wallet_cfg or None,
                "strategy": self.config,
            }

            # Initialize web3_service if not provided
            if self.web3_service is None:
                wallet_provider = WalletManager.get_provider(adapter_config)
                token_transaction_service = LocalTokenTxnService(
                    adapter_config,
                    wallet_provider=wallet_provider,
                )
                web3_service = DefaultWeb3Service(
                    wallet_provider=wallet_provider,
                    evm_transactions=token_transaction_service,
                )
            else:
                web3_service = self.web3_service
                token_transaction_service = web3_service.token_transactions

            # Initialize adapters
            balance = BalanceAdapter(adapter_config, web3_service=web3_service)
            token_adapter = TokenAdapter()
            ledger_adapter = LedgerAdapter()
            brap_adapter = BRAPAdapter(
                web3_service=web3_service,
            )
            moonwell_adapter = MoonwellAdapter(
                adapter_config,
                simulation=self.simulation,
                web3_service=web3_service,
            )

            self.register_adapters(
                [
                    balance,
                    token_adapter,
                    ledger_adapter,
                    brap_adapter,
                    moonwell_adapter,
                    token_transaction_service,
                ]
            )

            self.balance_adapter = balance
            self.token_adapter = token_adapter
            self.ledger_adapter = ledger_adapter
            self.brap_adapter = brap_adapter
            self.moonwell_adapter = moonwell_adapter
            self.web3_service = web3_service

        except Exception as e:
            logger.error(f"Failed to initialize strategy adapters: {e}")
            raise

    def _max_safe_F(self, cf_w: float) -> float:
        """Max safe debt fraction vs borrow capacity under a depeg.

        Let a = 1 - MAX_DEPEG. If the position is sized at par (a=1) with debt
        fraction F = Debt / BorrowCapacity, then after an instantaneous depeg to a
        the borrow capacity shrinks by cf_w * (1-a) * Debt. Requiring Debt to
        remain <= new capacity yields:
            F_max = 1 / (1 + cf_w * (1 - a))

        Returns F_max clipped to [0, 1].
        """
        a = 1 - self.MAX_DEPEG
        if not (0 < a):
            return 0.0
        if not (0 <= cf_w < 1):
            return 0.0

        f_bound = 1.0 / (1.0 + cf_w * (1.0 - a))
        # Extra feasibility guard (usually >1, but keep for safety).
        f_feasible = 1.0 / (cf_w * a) if cf_w > 0 else 1.0
        return max(0.0, min(1.0, min(f_bound, f_feasible, 1.0)))

    def _get_strategy_wallet_address(self) -> str:
        """Get the strategy wallet address."""
        wallet = self.config.get("strategy_wallet", {})
        return wallet.get("address", "")

    def _get_main_wallet_address(self) -> str:
        """Get the main wallet address."""
        wallet = self.config.get("main_wallet", {})
        return wallet.get("address", "")

    async def setup(self):
        """Initialize token info and validate configuration."""
        if self.token_adapter is None:
            raise RuntimeError("Token adapter not initialized.")

        # Pre-fetch token info
        for token_id in [USDC_TOKEN_ID, WETH_TOKEN_ID, WSTETH_TOKEN_ID, ETH_TOKEN_ID]:
            try:
                success, info = await self.token_adapter.get_token(token_id)
                if success:
                    self._token_info_cache[token_id] = info
            except Exception as e:
                logger.warning(f"Failed to fetch token info for {token_id}: {e}")

    async def _get_token_info(self, token_id: str) -> dict:
        """Get token info from cache or fetch it."""
        if token_id in self._token_info_cache:
            return self._token_info_cache[token_id]

        success, info = await self.token_adapter.get_token(token_id)
        if success:
            self._token_info_cache[token_id] = info
            return info
        return {}

    async def _get_token_price(self, token_id: str) -> float:
        """Get token price with staleness check."""
        now = time.time()

        # Check cache with staleness
        if token_id in self._token_price_cache:
            timestamp = self._token_price_timestamps.get(token_id, 0)
            if now - timestamp < self.PRICE_STALENESS_THRESHOLD:
                return self._token_price_cache[token_id]
            else:
                logger.debug(f"Price cache stale for {token_id}, refreshing")

        success, price_data = await self.token_adapter.get_token_price(token_id)
        if success and isinstance(price_data, dict):
            price = price_data.get("current_price", 0.0)
            if price and price > 0:
                self._token_price_cache[token_id] = price
                self._token_price_timestamps[token_id] = now
                return price

        logger.warning(
            f"Failed to get fresh price for {token_id}, success={success}, price_data={price_data}"
        )
        return 0.0

    def _clear_price_cache(self):
        """Clear the price cache to force refresh."""
        self._token_price_cache.clear()
        self._token_price_timestamps.clear()

    async def _get_token_data(self, token_id: str) -> tuple[float, int]:
        """Get price and decimals for a token in one call."""
        price = await self._get_token_price(token_id)
        info = await self._get_token_info(token_id)
        return price, info.get("decimals", 18)

    async def _swap_with_retries(
        self,
        from_token_id: str,
        to_token_id: str,
        amount: int,
        max_retries: int | None = None,
        base_slippage: float | None = None,
        preferred_providers: list[str] | None = None,
    ) -> dict | None:
        """Swap with retries, progressive slippage, and exponential backoff."""
        if max_retries is None:
            max_retries = self.max_swap_retries
        if base_slippage is None:
            base_slippage = self.swap_slippage_tolerance

        last_error: Exception | None = None
        strategy_address = self._get_strategy_wallet_address()

        # Always balance-check swap inputs to avoid on-chain reverts from stale/rounded values.
        try:
            wallet_balance = await self._get_balance_raw(
                token_id=from_token_id,
                wallet_address=strategy_address,
            )
            if from_token_id == ETH_TOKEN_ID:
                reserve = int(self.WRAP_GAS_RESERVE * 10**18)
                wallet_balance = max(0, wallet_balance - reserve)
            amount = min(int(amount), wallet_balance)
        except Exception as exc:
            logger.warning(f"Failed to check swap balance for {from_token_id}: {exc}")

        if amount <= 0:
            logger.warning(
                f"Swap skipped: no available balance for {from_token_id} (post-reserve)"
            )
            return None

        # Wrap ETH to WETH before swapping - direct ETH swaps get bad fills
        if from_token_id == ETH_TOKEN_ID:
            logger.info(f"Wrapping {amount / 10**18:.6f} ETH to WETH before swap")
            wrap_success, wrap_msg = await self.moonwell_adapter.wrap_eth(amount=amount)
            if not wrap_success:
                logger.error(f"Failed to wrap ETH to WETH: {wrap_msg}")
                return None
            from_token_id = WETH_TOKEN_ID

        def _is_unknown_outcome_message(msg: str) -> bool:
            m = (msg or "").lower()
            return (
                "transaction pending" in m
                or "dropped/unknown" in m
                or "not in the chain after" in m
                or "no receipt after" in m
            )

        for i in range(max_retries):
            # Cap slippage at MAX_SLIPPAGE_TOLERANCE to prevent MEV attacks
            slippage = min(base_slippage * (i + 1), self.MAX_SLIPPAGE_TOLERANCE)
            try:
                success, result = await self.brap_adapter.swap_from_token_ids(
                    from_token_id=from_token_id,
                    to_token_id=to_token_id,
                    from_address=strategy_address,
                    amount=str(amount),
                    slippage=slippage,
                    preferred_providers=preferred_providers,
                )
                if success and result:
                    logger.info(
                        f"Swap succeeded on attempt {i + 1} with slippage {slippage * 100:.1f}%"
                    )
                    # Ensure result is a dict with to_amount
                    if isinstance(result, dict):
                        return result
                    return {"to_amount": result if isinstance(result, int) else 0}

                # Do not retry when the transaction outcome is unknown (pending/dropped).
                # Retrying swaps can create nonce gaps or duplicate fills.
                if isinstance(result, str) and _is_unknown_outcome_message(result):
                    raise SwapOutcomeUnknownError(result)

                last_error = Exception(str(result))
                logger.warning(
                    f"Swap attempt {i + 1}/{max_retries} returned unsuccessful: {result}"
                )
            except SwapOutcomeUnknownError:
                raise
            except Exception as e:
                if _is_unknown_outcome_message(str(e)):
                    raise SwapOutcomeUnknownError(str(e)) from e
                last_error = e
                logger.warning(
                    f"Swap attempt {i + 1}/{max_retries} failed with slippage "
                    f"{slippage * 100:.1f}%: {e}"
                )
            if i < max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2**i)

        logger.error(
            f"All {max_retries} swap attempts failed. Last error: {last_error}"
        )
        return None

    def _parse_balance(self, raw: Any) -> int:
        """Parse balance value to integer, handling various formats."""
        if raw is None:
            return 0
        if isinstance(raw, dict):
            raw = raw.get("balance", 0)
        try:
            return int(raw)
        except (ValueError, TypeError):
            try:
                return int(float(raw))
            except (ValueError, TypeError):
                return 0

    def _token_address_for_id(self, token_id: str) -> str | None:
        if token_id == ETH_TOKEN_ID:
            return None
        if token_id == USDC_TOKEN_ID:
            return USDC
        if token_id == WETH_TOKEN_ID:
            return WETH
        if token_id == WSTETH_TOKEN_ID:
            return WSTETH
        return None

    async def _get_balance_raw(
        self,
        *,
        token_id: str,
        wallet_address: str,
        block_identifier: int | str | None = None,
    ) -> int:
        """Read a wallet balance directly from chain (falls back to adapter in simulation).

        Args:
            token_id: Token identifier (e.g., WETH_TOKEN_ID)
            wallet_address: Address to query balance for
            block_identifier: Block to query at. Can be:
                - int: specific block number (for pinning to tx block)
                - "safe": OP Stack safe block (data posted to L1)
                - None/"latest": current head (default)
        """
        if not token_id or not wallet_address:
            return 0

        # Tests/simulations patch adapters; avoid RPC calls there.
        if self.simulation or self.web3_service is None:
            if self.balance_adapter is None:
                return 0
            success, raw = await self.balance_adapter.get_balance(
                query=token_id,
                wallet_address=wallet_address,
            )
            return self._parse_balance(raw) if success else 0

        token_address = self._token_address_for_id(token_id)
        if token_id != ETH_TOKEN_ID and not token_address:
            # Try to resolve address via token metadata (not a balance read).
            if self.token_adapter is not None:
                try:
                    success, info = await self.token_adapter.get_token(token_id)
                    if success and isinstance(info, dict):
                        token_address = info.get("address") or None
                except Exception as exc:
                    logger.warning(
                        f"Failed to resolve token address for {token_id}: {exc}"
                    )

        if token_id != ETH_TOKEN_ID and not token_address:
            # Do not fall back to API balances for execution-critical paths.
            logger.warning(
                f"Unknown token address for {token_id}; skipping balance read"
            )
            return 0

        try:
            ok, bal = await self.balance_adapter.get_balance(
                query=token_id,
                wallet_address=wallet_address,
            )
            return int(bal) if ok else 0
        except Exception as exc:
            logger.warning(f"On-chain balance read failed for {token_id}: {exc}")
            return 0

    def _normalize_usd_value(self, raw: Any) -> float:
        """Normalize a USD value that may be 18-decimal scaled (Compound/Moonwell style).

        Moonwell's Comptroller `getAccountLiquidity` returns USD with 18 decimals as an int.
        Some mocks may return a float already in USD.
        """
        if raw is None:
            return 0.0

        # Preserve int-ness check before coercion: ints are assumed 1e18-scaled.
        is_int = isinstance(raw, int) and not isinstance(raw, bool)
        try:
            val = float(raw)
        except (ValueError, TypeError):
            return 0.0

        if is_int:
            return val / 1e18

        # Defensive: if a float looks like a 1e18-scaled value, de-scale it.
        return val / 1e18 if val > 1e12 else val

    def _mtoken_amount_for_underlying(
        self, withdraw_info: dict[str, Any], underlying_raw: int
    ) -> int:
        """Convert desired underlying (raw) to mToken amount (raw), capped by max withdrawable."""
        if underlying_raw <= 0:
            return 0

        max_ctokens = int(withdraw_info.get("cTokens_raw", 0) or 0)
        if max_ctokens <= 0:
            return 0

        exchange_rate_raw = int(withdraw_info.get("exchangeRate_raw", 0) or 0)
        conversion_factor = withdraw_info.get("conversion_factor", 0) or 0

        if exchange_rate_raw > 0:
            # underlying = cTokens * exchangeRate / 1e18  =>  cTokens = ceil(underlying*1e18 / exchangeRate)
            ctokens_needed = (
                int(underlying_raw) * 10**18 + exchange_rate_raw - 1
            ) // exchange_rate_raw
        else:
            try:
                cf = float(conversion_factor)
            except (TypeError, ValueError):
                cf = 0.0
            ctokens_needed = (
                int(cf * int(underlying_raw)) + 1 if cf > 0 else max_ctokens
            )

        return min(int(ctokens_needed), max_ctokens)

    async def _get_gas_balance(self) -> int:
        """Get ETH balance in strategy wallet (raw wei)."""
        return await self._get_balance_raw(
            token_id=ETH_TOKEN_ID, wallet_address=self._get_strategy_wallet_address()
        )

    async def _get_usdc_balance(self) -> int:
        """Get USDC balance in strategy wallet (raw wei)."""
        return await self._get_balance_raw(
            token_id=USDC_TOKEN_ID, wallet_address=self._get_strategy_wallet_address()
        )

    async def _validate_gas_balance(self) -> tuple[bool, str]:
        """Validate gas balance meets minimum requirements."""
        gas_balance = await self._get_gas_balance()
        main_gas = await self._get_balance_raw(
            token_id=ETH_TOKEN_ID, wallet_address=self._get_main_wallet_address()
        )
        total_gas = gas_balance + main_gas

        if total_gas < int(self.MIN_GAS * 10**18):
            return (
                False,
                f"Need at least {self.MIN_GAS} Base ETH for gas. You have: {total_gas / 10**18:.6f}",
            )
        return (True, "Gas balance validated")

    async def _validate_usdc_deposit(
        self, usdc_amount: float
    ) -> tuple[bool, str, float]:
        """Validate USDC deposit amount."""
        actual_balance = await self._get_balance_raw(
            token_id=USDC_TOKEN_ID, wallet_address=self._get_main_wallet_address()
        )

        token_info = await self._get_token_info(USDC_TOKEN_ID)
        decimals = token_info.get("decimals", 6)
        available_usdc = actual_balance / (10**decimals)

        usdc_amount = min(usdc_amount, available_usdc)

        if usdc_amount < self.MIN_USDC_DEPOSIT:
            return (
                False,
                f"Minimum deposit is {self.MIN_USDC_DEPOSIT} USDC. Available: {available_usdc:.2f}",
                usdc_amount,
            )
        return (True, "USDC deposit amount validated", usdc_amount)

    async def _check_quote_profitability(self) -> tuple[bool, str]:
        """Check if the quote APY is profitable."""
        quote = await self.quote()
        if quote.get("apy", 0) < 0:
            return (
                False,
                "APYs and ratios are not profitable at the moment, aborting deposit",
            )
        return (True, "Quote is profitable")

    async def _transfer_usdc_to_vault(self, usdc_amount: float) -> tuple[bool, str]:
        """Transfer USDC from main wallet to vault wallet."""
        (
            success,
            msg,
        ) = await self.balance_adapter.move_from_main_wallet_to_strategy_wallet(
            USDC_TOKEN_ID, usdc_amount
        )
        if not success:
            return (False, f"Depositing USDC into vault wallet failed: {msg}")
        return (True, "USDC transferred to vault")

    async def _transfer_gas_to_vault(self) -> tuple[bool, str]:
        """Transfer gas from main wallet to vault if needed."""
        vault_gas = await self._get_gas_balance()
        if vault_gas < int(self.MIN_GAS * 10**18):
            needed_gas = self.MIN_GAS - vault_gas / 10**18
            (
                success,
                msg,
            ) = await self.balance_adapter.move_from_main_wallet_to_strategy_wallet(
                ETH_TOKEN_ID, needed_gas
            )
            if not success:
                return (False, f"Depositing gas into strategy wallet failed: {msg}")
        return (True, "Gas transferred to strategy")

    async def _balance_weth_debt(self) -> tuple[bool, str]:
        """Balance WETH debt if it exceeds wstETH collateral for delta-neutrality."""
        # Get wstETH position (can be zero; missing collateral is a common recovery case)
        wsteth_underlying = 0
        wsteth_pos_result = await self.moonwell_adapter.get_pos(mtoken=M_WSTETH)
        if wsteth_pos_result[0] and isinstance(wsteth_pos_result[1], dict):
            wsteth_pos = wsteth_pos_result[1]
            wsteth_underlying = int(wsteth_pos.get("underlying_balance", 0) or 0)
        else:
            # Treat as 0 collateral and proceed conservatively (we still may have WETH debt).
            logger.warning(
                f"Failed to fetch wstETH position; treating as 0 for debt balancing: {wsteth_pos_result[1]}"
            )

        # Get WETH debt value
        weth_pos_result = await self.moonwell_adapter.get_pos(mtoken=M_WETH)
        if not weth_pos_result[0]:
            return (True, "No WETH debt to balance")

        weth_pos = weth_pos_result[1]
        weth_debt = weth_pos.get("borrow_balance", 0)

        if weth_debt == 0:
            return (True, "No WETH debt to balance")

        # Get prices and decimals
        weth_price, weth_decimals = await self._get_token_data(WETH_TOKEN_ID)
        if not weth_price or weth_price <= 0:
            return (False, "WETH price unavailable; cannot balance debt safely")

        wsteth_price, wsteth_decimals = await self._get_token_data(WSTETH_TOKEN_ID)
        if wsteth_underlying > 0 and (not wsteth_price or wsteth_price <= 0):
            return (False, "wstETH price unavailable; cannot balance debt safely")
        # If wstETH collateral is zero, we don't need wstETH price to proceed.
        wsteth_price = float(wsteth_price or 0.0)

        wsteth_value = (wsteth_underlying / 10**wsteth_decimals) * wsteth_price
        weth_debt_value = (weth_debt / 10**weth_decimals) * weth_price

        # Check if we're imbalanced (debt > collateral)
        excess_debt_value = weth_debt_value - wsteth_value
        if excess_debt_value <= 0:
            return (True, "WETH debt is balanced with wstETH collateral")

        logger.warning(
            f"WETH debt exceeds wstETH collateral by ${excess_debt_value:.2f}. Rebalancing..."
        )

        excess_debt_wei = int(excess_debt_value / weth_price * 10**weth_decimals)
        repaid = 0

        # Step 1: Try using wallet WETH
        wallet_weth = await self._get_balance_raw(
            token_id=WETH_TOKEN_ID, wallet_address=self._get_strategy_wallet_address()
        )
        if wallet_weth > 0:
            repay_amt = min(wallet_weth, excess_debt_wei - repaid)
            success, _ = await self.moonwell_adapter.repay(
                mtoken=M_WETH,
                underlying_token=WETH,
                amount=repay_amt,
            )
            if success:
                repaid += repay_amt
                logger.info(f"Repaid {repay_amt / 10**18:.6f} WETH from wallet")

        if repaid >= excess_debt_wei:
            return (
                True,
                f"Balanced debt by repaying {repaid / 10**18:.6f} WETH from wallet",
            )

        # Step 2: Try wrapping wallet ETH → WETH and repaying (within gas reserve)
        wallet_eth = await self._get_balance_raw(
            token_id=ETH_TOKEN_ID, wallet_address=self._get_strategy_wallet_address()
        )
        gas_reserve = int(self.WRAP_GAS_RESERVE * 10**18)
        usable_eth = max(0, wallet_eth - gas_reserve)
        if usable_eth > 0:
            wrap_amt = min(usable_eth, excess_debt_wei - repaid)
            try:
                wrap_success, wrap_msg = await self.moonwell_adapter.wrap_eth(
                    amount=wrap_amt
                )
                if not wrap_success:
                    logger.warning(f"Failed to wrap ETH for repayment: {wrap_msg}")
                else:
                    weth_after = await self._get_balance_raw(
                        token_id=WETH_TOKEN_ID,
                        wallet_address=self._get_strategy_wallet_address(),
                    )
                    repay_amt = min(weth_after, excess_debt_wei - repaid)
                    if repay_amt > 0:
                        repay_success, _ = await self.moonwell_adapter.repay(
                            mtoken=M_WETH,
                            underlying_token=WETH,
                            amount=repay_amt,
                        )
                        if repay_success:
                            repaid += repay_amt
                            logger.info(
                                f"Wrapped and repaid {repay_amt / 10**18:.6f} ETH (as WETH)"
                            )

                # Try topping up gas back to MIN_GAS if we dipped below it (non-critical).
                topup_success, topup_msg = await self._transfer_gas_to_vault()
                if not topup_success:
                    logger.warning(f"Gas top-up failed (non-critical): {topup_msg}")
            except Exception as e:
                logger.warning(f"Failed to wrap ETH and repay: {e}")

        if repaid >= excess_debt_wei:
            return (True, f"Balanced debt by repaying {repaid / 10**18:.6f} WETH")

        # Step 3: Try swapping wallet USDC to WETH and repaying
        remaining_to_repay = excess_debt_wei - repaid
        remaining_value = (remaining_to_repay / 10**weth_decimals) * weth_price

        wallet_usdc = await self._get_balance_raw(
            token_id=USDC_TOKEN_ID, wallet_address=self._get_strategy_wallet_address()
        )
        if wallet_usdc > 0 and remaining_to_repay > 0:
            usdc_price, usdc_decimals = await self._get_token_data(USDC_TOKEN_ID)
            wallet_usdc_value = (wallet_usdc / 10**usdc_decimals) * usdc_price

            if wallet_usdc_value >= self.min_withdraw_usd:
                # Swap enough USDC to cover remaining debt (with 2% buffer)
                needed_usdc_value = min(remaining_value * 1.02, wallet_usdc_value)
                needed_usdc = int(needed_usdc_value / usdc_price * 10**usdc_decimals)
                amount_to_swap = min(needed_usdc, wallet_usdc)
                try:
                    swap_result = await self._swap_with_retries(
                        from_token_id=USDC_TOKEN_ID,
                        to_token_id=WETH_TOKEN_ID,
                        amount=amount_to_swap,
                    )
                    if swap_result:
                        # Use actual post-swap WETH balance to avoid relying on quoted to_amount.
                        weth_after = await self._get_balance_raw(
                            token_id=WETH_TOKEN_ID,
                            wallet_address=self._get_strategy_wallet_address(),
                        )
                        repay_amt = min(weth_after, excess_debt_wei - repaid)
                        if repay_amt > 0:
                            success, _ = await self.moonwell_adapter.repay(
                                mtoken=M_WETH,
                                underlying_token=WETH,
                                amount=repay_amt,
                            )
                            if success:
                                repaid += repay_amt
                                logger.info(
                                    f"Swapped wallet USDC and repaid {repay_amt / 10**18:.6f} WETH"
                                )
                except SwapOutcomeUnknownError as exc:
                    return (
                        False,
                        f"Swap outcome unknown while swapping wallet USDC for repayment: {exc}",
                    )
                except Exception as e:
                    logger.warning(f"Failed to swap wallet USDC for repayment: {e}")

        if repaid >= excess_debt_wei:
            return (True, f"Balanced debt by repaying {repaid / 10**18:.6f} WETH")

        # Step 4: Unlend USDC collateral, swap to WETH, and repay
        remaining_to_repay = excess_debt_wei - repaid
        remaining_value = (remaining_to_repay / 10**weth_decimals) * weth_price

        usdc_withdraw_result = await self.moonwell_adapter.max_withdrawable_mtoken(
            mtoken=M_USDC
        )
        if usdc_withdraw_result[0]:
            withdraw_info = usdc_withdraw_result[1]
            underlying_raw = withdraw_info.get("underlying_raw", 0)

            usdc_price, usdc_decimals = await self._get_token_data(USDC_TOKEN_ID)
            usdc_value = (underlying_raw / 10**usdc_decimals) * usdc_price

            if usdc_value > self.min_withdraw_usd:
                # Calculate how much USDC to unlock
                needed_usdc_value = min(remaining_value * 1.02, usdc_value)  # 2% buffer
                needed_usdc = int(needed_usdc_value / usdc_price * 10**usdc_decimals)
                mtoken_amt = self._mtoken_amount_for_underlying(
                    withdraw_info, needed_usdc
                )

                try:
                    success, _ = await self.moonwell_adapter.unlend(
                        mtoken=M_USDC, amount=mtoken_amt
                    )
                    if success:
                        # Swap only what we actually have in-wallet (avoid balance-based reverts).
                        wallet_usdc_after = await self._get_balance_raw(
                            token_id=USDC_TOKEN_ID,
                            wallet_address=self._get_strategy_wallet_address(),
                        )
                        amount_to_swap = min(wallet_usdc_after, needed_usdc)
                        if amount_to_swap <= 0:
                            raise Exception("No USDC available to swap after unlending")
                        # Swap USDC to WETH
                        swap_result = await self._swap_with_retries(
                            from_token_id=USDC_TOKEN_ID,
                            to_token_id=WETH_TOKEN_ID,
                            amount=amount_to_swap,
                        )
                        if swap_result:
                            weth_after = await self._get_balance_raw(
                                token_id=WETH_TOKEN_ID,
                                wallet_address=self._get_strategy_wallet_address(),
                            )
                            repay_amt = min(weth_after, excess_debt_wei - repaid)
                            if repay_amt > 0:
                                repay_success, _ = await self.moonwell_adapter.repay(
                                    mtoken=M_WETH,
                                    underlying_token=WETH,
                                    amount=repay_amt,
                                )
                                if repay_success:
                                    repaid += repay_amt
                                    logger.info(
                                        f"Unlent USDC, swapped and repaid {repay_amt / 10**18:.6f} WETH"
                                    )
                except SwapOutcomeUnknownError as exc:
                    return (
                        False,
                        f"Swap outcome unknown while unlocking USDC for repayment: {exc}",
                    )
                except Exception as e:
                    logger.warning(f"Failed to unlock USDC and swap for repayment: {e}")

        if repaid >= excess_debt_wei * 0.95:  # Allow 5% tolerance
            return (True, f"Balanced debt by repaying {repaid / 10**18:.6f} WETH")

        return (
            False,
            f"Could only repay {repaid / 10**18:.6f} of {excess_debt_wei / 10**18:.6f} excess WETH debt",
        )

    async def _complete_unpaired_weth_borrow(self) -> tuple[bool, str]:
        """If we have WETH debt but insufficient wstETH collateral, try to complete the loop.

        This is the common "failed swap" recovery state:
        - Debt exists on Moonwell (borrowed WETH),
        - wstETH collateral is missing/low,
        - The borrowed value is still sitting in the wallet as WETH and/or native ETH.

        We prefer swapping wallet WETH → wstETH and lending it (to restore the intended position)
        before considering debt repayment.
        """
        # Read positions
        wsteth_pos_result, weth_pos_result = await asyncio.gather(
            self.moonwell_adapter.get_pos(mtoken=M_WSTETH),
            self.moonwell_adapter.get_pos(mtoken=M_WETH),
        )
        if not weth_pos_result[0]:
            return (True, "No WETH debt to complete")

        weth_debt = int((weth_pos_result[1] or {}).get("borrow_balance", 0) or 0)
        if weth_debt <= 0:
            return (True, "No WETH debt to complete")

        wsteth_underlying = 0
        if wsteth_pos_result[0]:
            wsteth_underlying = int(
                (wsteth_pos_result[1] or {}).get("underlying_balance", 0) or 0
            )

        # Determine whether we're meaningfully unpaired.
        # Prefer price-based comparison, but allow a strict fallback for the common case:
        # wstETH collateral is literally 0 after a failed swap.
        wsteth_price, wsteth_decimals = await self._get_token_data(WSTETH_TOKEN_ID)
        weth_price, weth_decimals = await self._get_token_data(WETH_TOKEN_ID)

        deficit_usd: float | None = None
        if wsteth_price and wsteth_price > 0 and weth_price and weth_price > 0:
            wsteth_value = (wsteth_underlying / 10**wsteth_decimals) * wsteth_price
            weth_debt_value = (weth_debt / 10**weth_decimals) * weth_price
            deficit_usd = weth_debt_value - wsteth_value

            # Small deficits are just rounding; ignore.
            if deficit_usd <= max(1.0, float(self.min_withdraw_usd)):
                return (True, "wstETH collateral already roughly matches WETH debt")
        elif wsteth_underlying > 0:
            # If we already have some wstETH collateral but cannot price it, don't guess.
            return (True, "Price unavailable; skipping unpaired borrow completion")

        strategy_address = self._get_strategy_wallet_address()

        # Check for loose wstETH first - lend it before swapping anything
        wallet_wsteth = await self._get_balance_raw(
            token_id=WSTETH_TOKEN_ID, wallet_address=strategy_address
        )
        if wallet_wsteth > 0:
            logger.info(
                f"Found {wallet_wsteth / 10**18:.6f} loose wstETH in wallet, lending first"
            )
            lend_success, lend_msg = await self.moonwell_adapter.lend(
                mtoken=M_WSTETH,
                underlying_token=WSTETH,
                amount=int(wallet_wsteth),
            )
            if lend_success:
                # Recalculate deficit after lending
                wsteth_pos_result = await self.moonwell_adapter.get_pos(mtoken=M_WSTETH)
                if wsteth_pos_result[0]:
                    wsteth_underlying = int(
                        (wsteth_pos_result[1] or {}).get("underlying_balance", 0) or 0
                    )
                    if (
                        wsteth_price
                        and wsteth_price > 0
                        and weth_price
                        and weth_price > 0
                    ):
                        wsteth_value = (
                            wsteth_underlying / 10**wsteth_decimals
                        ) * wsteth_price
                        weth_debt_value = (weth_debt / 10**weth_decimals) * weth_price
                        deficit_usd = weth_debt_value - wsteth_value
                        if deficit_usd <= max(1.0, float(self.min_withdraw_usd)):
                            return (
                                True,
                                "Loose wstETH lent; collateral now matches debt",
                            )
            else:
                logger.warning(f"Failed to lend loose wstETH: {lend_msg}")

        wallet_weth = await self._get_balance_raw(
            token_id=WETH_TOKEN_ID, wallet_address=strategy_address
        )
        wallet_eth = await self._get_balance_raw(
            token_id=ETH_TOKEN_ID, wallet_address=strategy_address
        )

        gas_reserve = int(self.WRAP_GAS_RESERVE * 10**18)
        usable_eth = max(0, wallet_eth - gas_reserve)

        # Target WETH input needed.
        # If we couldn't price, fall back to swapping up to the debt amount when collateral is 0.
        if deficit_usd is None:
            target_weth_in = int(weth_debt)
        else:
            # Add 0.5% buffer for slippage/fees, but never exceed debt.
            target_weth_in = (
                int(deficit_usd / weth_price * 10**weth_decimals / (1 - 0.005)) + 1
            )
            target_weth_in = min(int(target_weth_in), int(weth_debt))

        available_weth_like = int(wallet_weth) + int(usable_eth)
        if available_weth_like <= 0:
            return (False, "No wallet WETH/ETH available to complete the loop")

        amount_to_source = min(int(target_weth_in), int(available_weth_like))
        if amount_to_source <= 0:
            return (True, "No meaningful WETH amount available to swap to wstETH")

        wsteth_before = await self._get_balance_raw(
            token_id=WSTETH_TOKEN_ID, wallet_address=strategy_address
        )

        remaining = int(amount_to_source)

        # Swap wallet WETH first (ERC20 path).
        # Prefer enso/aerodrome for WETH→wstETH - LiFi gets bad fills
        weth_to_swap = min(int(wallet_weth), int(remaining))
        if weth_to_swap > 0:
            swap_res = await self._swap_with_retries(
                from_token_id=WETH_TOKEN_ID,
                to_token_id=WSTETH_TOKEN_ID,
                amount=weth_to_swap,
                preferred_providers=["aerodrome", "enso"],
            )
            if swap_res is None:
                logger.warning(
                    "WETH→wstETH swap failed during unpaired borrow completion"
                )
            remaining -= int(weth_to_swap)

        # Then swap native ETH (borrowed WETH often arrives as ETH on Base in practice).
        # Prefer enso/aerodrome for ETH→wstETH - LiFi gets bad fills
        eth_to_swap = min(int(usable_eth), int(remaining))
        if eth_to_swap > 0:
            swap_res = await self._swap_with_retries(
                from_token_id=ETH_TOKEN_ID,
                to_token_id=WSTETH_TOKEN_ID,
                amount=eth_to_swap,
                preferred_providers=["aerodrome", "enso"],
            )
            if swap_res is None:
                logger.warning(
                    "ETH→wstETH swap failed during unpaired borrow completion"
                )

        wsteth_after = await self._get_balance_raw(
            token_id=WSTETH_TOKEN_ID, wallet_address=strategy_address
        )
        received = max(0, int(wsteth_after) - int(wsteth_before))
        if received <= 0:
            return (
                False,
                "Swap to wstETH produced no wstETH; will fall back to debt balancing",
            )

        success, msg = await self.moonwell_adapter.lend(
            mtoken=M_WSTETH,
            underlying_token=WSTETH,
            amount=received,
        )
        if not success:
            return (False, f"Lending wstETH failed: {msg}")

        await self.moonwell_adapter.set_collateral(mtoken=M_WSTETH)
        return (
            True,
            f"Completed unpaired borrow by lending {received / 10**18:.6f} wstETH",
        )

    async def _convert_excess_eth_to_usdc(self) -> tuple[bool, str]:
        """Convert excess native ETH (above MIN_GAS) into USDC to be redeployed."""
        strategy_address = self._get_strategy_wallet_address()
        eth_bal = await self._get_balance_raw(
            token_id=ETH_TOKEN_ID, wallet_address=strategy_address
        )

        keep_wei = int(self.MIN_GAS * 10**18)
        excess = int(eth_bal) - int(keep_wei)
        # Avoid dust conversions; 0.001 ETH is already plenty of gas on Base.
        min_excess = int(0.001 * 10**18)
        if excess <= min_excess:
            return (True, "No excess ETH to convert")

        # Wrap excess ETH to WETH (so swaps are ERC20-based and allowance-friendly).
        weth_before = await self._get_balance_raw(
            token_id=WETH_TOKEN_ID, wallet_address=strategy_address
        )
        wrap_success, wrap_msg = await self.moonwell_adapter.wrap_eth(amount=excess)
        if not wrap_success:
            return (False, f"Wrap ETH→WETH failed: {wrap_msg}")

        weth_after = await self._get_balance_raw(
            token_id=WETH_TOKEN_ID, wallet_address=strategy_address
        )
        wrapped = max(0, int(weth_after) - int(weth_before))
        if wrapped <= 0:
            return (False, "ETH→WETH wrap produced no WETH")

        swap_result = await self._swap_with_retries(
            from_token_id=WETH_TOKEN_ID,
            to_token_id=USDC_TOKEN_ID,
            amount=wrapped,
        )
        if swap_result is None:
            return (False, "WETH→USDC swap failed when converting excess ETH")

        return (True, "Converted excess ETH to USDC")

    async def _convert_spot_wsteth_to_usdc(self) -> tuple[bool, str]:
        """Convert wallet (spot) wstETH into USDC so it can be redeployed.

        This never touches native ETH, so it cannot drain gas.
        """
        strategy_address = self._get_strategy_wallet_address()
        wsteth_raw = await self._get_balance_raw(
            token_id=WSTETH_TOKEN_ID, wallet_address=strategy_address
        )
        if wsteth_raw <= 0:
            return (True, "No wallet wstETH to convert")

        # Avoid dust conversions.
        wsteth_price, wsteth_decimals = await self._get_token_data(WSTETH_TOKEN_ID)
        if not wsteth_price or wsteth_price <= 0:
            return (True, "wstETH price unavailable; skipping wallet wstETH conversion")
        usd_value = (wsteth_raw / 10**wsteth_decimals) * wsteth_price
        if usd_value < float(self.min_withdraw_usd):
            return (True, "Wallet wstETH below threshold; skipping conversion")

        swap_result = await self._swap_with_retries(
            from_token_id=WSTETH_TOKEN_ID,
            to_token_id=USDC_TOKEN_ID,
            amount=int(wsteth_raw),
        )
        if swap_result is None:
            return (False, "wstETH→USDC swap failed")

        return (True, f"Converted wallet wstETH (~${usd_value:.2f}) to USDC")

    async def _sweep_token_balances(
        self,
        target_token_id: str,
        exclude: set[str] | None = None,
        min_usd_value: float = 1.0,
    ) -> tuple[bool, str]:
        """Sweep miscellaneous tokens above min_usd_value to target token."""
        if exclude is None:
            exclude = set()

        # Always exclude gas token and target
        exclude.add(ETH_TOKEN_ID)
        exclude.add(target_token_id)

        tokens_to_check = [USDC_TOKEN_ID, WETH_TOKEN_ID, WSTETH_TOKEN_ID, WELL_TOKEN_ID]
        total_swept_usd = 0.0
        swept_count = 0

        for token_id in tokens_to_check:
            if token_id in exclude:
                continue

            balance = await self._get_balance_raw(
                token_id=token_id, wallet_address=self._get_strategy_wallet_address()
            )
            if balance <= 0:
                continue

            price, decimals = await self._get_token_data(token_id)
            usd_value = (balance / 10**decimals) * price

            if usd_value < min_usd_value:
                continue

            try:
                swap_result = await self._swap_with_retries(
                    from_token_id=token_id,
                    to_token_id=target_token_id,
                    amount=balance,
                )
                if swap_result:
                    total_swept_usd += usd_value
                    swept_count += 1
                    logger.info(
                        f"Swept {balance / 10**decimals:.6f} {token_id} "
                        f"(${usd_value:.2f}) to {target_token_id}"
                    )
            except Exception as e:
                logger.warning(f"Failed to sweep {token_id}: {e}")

        if swept_count == 0:
            return (True, "No tokens to sweep")

        return (True, f"Swept {swept_count} tokens totaling ${total_swept_usd:.2f}")

    async def deposit(
        self, main_token_amount: float = 0.0, gas_token_amount: float = 0.0
    ) -> StatusTuple:
        """Deposit USDC and execute leverage loop."""
        self._clear_price_cache()

        # Validate deposit amount is positive
        if main_token_amount <= 0:
            return (False, "Deposit amount must be positive")

        # Check quote profitability
        success, message = await self._check_quote_profitability()
        if not success:
            return (False, message)

        # Validate USDC deposit amount
        success, message, validated_amount = await self._validate_usdc_deposit(
            main_token_amount
        )
        if not success:
            return (False, message)
        usdc_amount = validated_amount

        # Validate gas balance
        success, message = await self._validate_gas_balance()
        if not success:
            return (False, message)

        # Transfer gas to vault wallet first (if this fails, USDC stays in main wallet)
        success, message = await self._transfer_gas_to_vault()
        if not success:
            return (False, message)

        # Transfer USDC to vault wallet
        success, message = await self._transfer_usdc_to_vault(usdc_amount)
        if not success:
            return (False, message)

        # Execute the leverage loop via update
        return await self.update()

    async def _get_collateral_factors(self) -> tuple[float, float]:
        """Fetch both collateral factors (USDC and wstETH), using adapter cache.

        Returns (cf_usdc, cf_wsteth).
        """
        cf_u_result, cf_w_result = await asyncio.gather(
            self.moonwell_adapter.get_collateral_factor(mtoken=M_USDC),
            self.moonwell_adapter.get_collateral_factor(mtoken=M_WSTETH),
        )
        cf_u = cf_u_result[1] if cf_u_result[0] else 0.0
        cf_w = cf_w_result[1] if cf_w_result[0] else 0.0
        return cf_u, cf_w

    async def _get_current_leverage(
        self,
        positions: tuple[dict, dict] | None = None,
    ) -> tuple[float, float, float]:
        """Returns (usdc_lend_value, wsteth_lend_value, current_leverage).

        Args:
            positions: Optional (total_bals, total_usd_bals) from _aggregate_positions().
                       If provided, skips position fetches.
        """
        # Use provided positions or fetch them
        if positions is not None:
            _total_bals, totals_usd = positions
            usdc_key = f"Base_{M_USDC}"
            wsteth_key = f"Base_{M_WSTETH}"
            usdc_lend_value = float(totals_usd.get(usdc_key, 0.0))
            wsteth_lend_value = float(totals_usd.get(wsteth_key, 0.0))
        else:
            wsteth_result = await self.moonwell_adapter.get_pos(mtoken=M_WSTETH)
            usdc_result = await self.moonwell_adapter.get_pos(mtoken=M_USDC)

            # Get prices/decimals
            wsteth_price, wsteth_decimals = await self._get_token_data(WSTETH_TOKEN_ID)
            usdc_price, usdc_decimals = await self._get_token_data(USDC_TOKEN_ID)

            # Calculate wstETH lend value (may not exist yet)
            wsteth_lend_value = 0.0
            if wsteth_result[0]:
                wsteth_pos = wsteth_result[1]
                wsteth_underlying = wsteth_pos.get("underlying_balance", 0)
                wsteth_lend_value = (
                    wsteth_underlying / 10**wsteth_decimals
                ) * wsteth_price

            # Calculate USDC lend value
            usdc_lend_value = 0.0
            if usdc_result[0]:
                usdc_pos = usdc_result[1]
                usdc_underlying = usdc_pos.get("underlying_balance", 0)
                usdc_lend_value = (usdc_underlying / 10**usdc_decimals) * usdc_price

        initial_leverage = (
            wsteth_lend_value / usdc_lend_value + 1 if usdc_lend_value else 0
        )

        return (usdc_lend_value, wsteth_lend_value, initial_leverage)

    async def _aggregate_positions(self) -> tuple[dict, dict]:
        """Aggregate positions from all Moonwell markets. Returns (total_bals, total_usd_bals).

        Note: Position fetches are done sequentially to avoid overwhelming public RPCs
        with too many parallel requests (each get_pos makes 5 RPC calls).
        """
        mtoken_list = [M_USDC, M_WETH, M_WSTETH]
        underlying_list = [USDC, WETH, WSTETH]

        # Sequential fetch for positions with delays to avoid rate limiting on public RPCs
        # Each get_pos makes 5 sequential RPC calls; adding delays between positions
        # helps the rate limiter recover (Base public RPC has aggressive limits)
        positions = []
        for mtoken in mtoken_list:
            pos = await self.moonwell_adapter.get_pos(mtoken=mtoken)
            positions.append(pos)
            # 2s delay between positions for public RPC
            await asyncio.sleep(2.0)

        # Token data can be fetched in parallel (uses cache, minimal RPC)
        token_data = await asyncio.gather(
            self._get_token_data(USDC_TOKEN_ID),
            self._get_token_data(WETH_TOKEN_ID),
            self._get_token_data(WSTETH_TOKEN_ID),
        )

        total_bals: dict[str, float] = {}
        total_usd_bals: dict[str, float] = {}

        for i, mtoken in enumerate(mtoken_list):
            success, pos = positions[i]
            if not success:
                logger.warning(f"get_pos failed for {mtoken}: {pos}")
                continue

            price, decimals = token_data[i]
            underlying_addr = underlying_list[i]

            underlying_bal = pos.get("underlying_balance", 0)
            borrow_bal = pos.get("borrow_balance", 0)

            key_mtoken = f"Base_{mtoken}"
            key_underlying = f"Base_{underlying_addr}"

            # Store underlying as positive if lent
            if underlying_bal > 0:
                total_bals[key_mtoken] = underlying_bal
                total_usd_bals[key_mtoken] = (underlying_bal / 10**decimals) * price

            # Store borrow as negative
            if borrow_bal > 0:
                total_bals[key_underlying] = -borrow_bal
                total_usd_bals[key_underlying] = -(borrow_bal / 10**decimals) * price

        return total_bals, total_usd_bals

    async def compute_ltv(
        self,
        total_usd_bals: dict,
        collateral_factors: tuple[float, float] | None = None,
    ) -> float:
        """Compute loan-to-value ratio.

        LTV = Debt / (cf_u * C_u + cf_s * C_s)

        Args:
            total_usd_bals: USD balances from _aggregate_positions().
            collateral_factors: Optional (cf_usdc, cf_wsteth) tuple.
                                If provided, skips collateral factor fetches.
        """
        # Get debt (WETH borrow)
        weth_key = f"Base_{WETH}"
        debt_usd = abs(float(total_usd_bals.get(weth_key, 0.0)))

        # Get collateral values
        usdc_key = f"Base_{M_USDC}"
        wsteth_key = f"Base_{M_WSTETH}"
        usdc_collateral = float(total_usd_bals.get(usdc_key, 0.0))
        wsteth_collateral = float(total_usd_bals.get(wsteth_key, 0.0))

        # Use provided collateral factors or fetch them
        if collateral_factors is not None:
            cf_u, cf_s = collateral_factors
        else:
            cf_u, cf_s = await self._get_collateral_factors()

        capacity = cf_u * usdc_collateral + cf_s * wsteth_collateral

        if capacity <= 0:
            return float("nan")

        return debt_usd / capacity

    async def _can_withdraw_token(
        self,
        total_usd_bals: dict[str, float],
        withdraw_token_id: str,
        withdraw_token_usd_val: float,
        *,
        collateral_factors: tuple[float, float] | None = None,
    ) -> bool:
        """Simulate withdrawing collateral and check resulting HF stays >= MIN_HEALTH_FACTOR."""
        current_val = float(total_usd_bals.get(withdraw_token_id, 0.0))
        if withdraw_token_usd_val <= 0:
            return True
        if withdraw_token_usd_val > current_val:
            return False

        simulated_bals = dict(total_usd_bals)
        simulated_bals[withdraw_token_id] = current_val - withdraw_token_usd_val

        new_ltv = await self.compute_ltv(simulated_bals, collateral_factors)
        if new_ltv == 0:
            return True
        if not new_ltv or new_ltv != new_ltv:
            return False

        new_hf = 1.0 / new_ltv
        return new_hf >= self.MIN_HEALTH_FACTOR

    async def _get_steth_apy(self) -> float | None:
        """Fetch wstETH APY from Lido API."""
        url = "https://eth-api.lido.fi/v1/protocol/steth/apr/sma"
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()

            apy = data.get("data", {}).get("smaApr", None)
            if apy:
                return apy / 100
        except Exception as e:
            logger.warning(f"Failed to fetch stETH APY: {e}")
        return None

    async def quote(self) -> dict:
        """Calculate projected APY for the strategy."""
        # Get APYs and collateral factors in parallel
        (
            usdc_apy_result,
            weth_apy_result,
            wsteth_apy,
            cf_u_result,
            cf_w_result,
        ) = await asyncio.gather(
            self.moonwell_adapter.get_apy(mtoken=M_USDC, apy_type="supply"),
            self.moonwell_adapter.get_apy(mtoken=M_WETH, apy_type="borrow"),
            self._get_steth_apy(),
            self.moonwell_adapter.get_collateral_factor(mtoken=M_USDC),
            self.moonwell_adapter.get_collateral_factor(mtoken=M_WSTETH),
        )

        usdc_lend_apy = usdc_apy_result[1] if usdc_apy_result[0] else 0.0
        weth_borrow_apy = weth_apy_result[1] if weth_apy_result[0] else 0.0
        wsteth_lend_apy = wsteth_apy or 0.0

        if not wsteth_lend_apy:
            return {
                "apy": 0,
                "information": "Failed to get Lido wstETH APY",
                "data": {},
            }

        cf_u = cf_u_result[1] if cf_u_result[0] else 0.0
        cf_w = cf_w_result[1] if cf_w_result[0] else 0.0

        if not cf_u or cf_u <= 0:
            return {"apy": 0, "information": "Invalid collateral factor", "data": {}}

        # Calculate target borrow and leverage
        denominator = self.MIN_HEALTH_FACTOR - cf_w
        if denominator <= 0:
            return {"apy": 0, "information": "Invalid health factor params", "data": {}}
        target_borrow = cf_u / denominator
        total_apy = target_borrow * (wsteth_lend_apy - weth_borrow_apy) + usdc_lend_apy
        total_leverage = target_borrow + 1

        return {
            "apy": total_apy,
            "information": f"Strategy would return {total_apy * 100:.2f}% APY with leverage of {total_leverage:.2f}x",
            "data": {
                "rates": {
                    "usdc_lend": usdc_lend_apy,
                    "wsteth_lend": wsteth_lend_apy,
                    "weth_borrow": weth_borrow_apy,
                },
                "leverage_achievable": total_leverage,
                "apy_achievable": total_apy,
            },
        }

    async def _atomic_deposit_iteration(self, borrow_amt_wei: int) -> int:
        """One atomic iteration: borrow WETH → swap wstETH → lend. Returns wstETH lent."""
        safe_borrow_amt = int(borrow_amt_wei * COLLATERAL_SAFETY_FACTOR)
        strategy_address = self._get_strategy_wallet_address()

        # Snapshot balances so we can detect whether the borrow surfaced as native ETH or WETH.
        # (On Base, some integrations auto-unwrap borrowed WETH to native ETH.)
        eth_before, weth_before = await asyncio.gather(
            self._get_balance_raw(
                token_id=ETH_TOKEN_ID, wallet_address=strategy_address
            ),
            self._get_balance_raw(
                token_id=WETH_TOKEN_ID, wallet_address=strategy_address
            ),
        )

        # Step 1: Borrow (debt is WETH-denominated)
        success, borrow_result = await self.moonwell_adapter.borrow(
            mtoken=M_WETH, amount=safe_borrow_amt
        )
        if not success:
            raise Exception(f"Borrow failed: {borrow_result}")

        # Extract block number from transaction result for block-pinned reads
        tx_block: int | None = None
        if isinstance(borrow_result, dict):
            tx_block = borrow_result.get("block_number") or (
                borrow_result.get("receipt", {}).get("blockNumber")
            )

        logger.info(
            f"Borrowed {safe_borrow_amt / 10**18:.6f} WETH (may arrive as ETH) "
            f"in block {tx_block}"
        )

        # Use block-pinned reads to check balances at the transaction's block
        # This avoids stale reads from RPC indexing lag on L2s like Base
        eth_delta = 0
        weth_delta = 0
        eth_after = 0
        weth_after = 0
        for attempt in range(5):
            if attempt > 0:
                # Exponential backoff: 1, 2, 4, 8 seconds
                await asyncio.sleep(2 ** (attempt - 1))

            # Read at the specific block where the borrow occurred
            eth_after, weth_after = await asyncio.gather(
                self._get_balance_raw(
                    token_id=ETH_TOKEN_ID,
                    wallet_address=strategy_address,
                    block_identifier=tx_block,
                ),
                self._get_balance_raw(
                    token_id=WETH_TOKEN_ID,
                    wallet_address=strategy_address,
                    block_identifier=tx_block,
                ),
            )

            eth_delta = max(0, int(eth_after) - int(eth_before))
            weth_delta = max(0, int(weth_after) - int(weth_before))

            if eth_delta > 0 or weth_delta > 0:
                break
            logger.debug(
                f"Balance check attempt {attempt + 1} at block {tx_block}: "
                f"no delta detected yet, retrying..."
            )

        gas_reserve = int(self.WRAP_GAS_RESERVE * 10**18)
        # Usable ETH is the minimum of what we received (eth_delta) and what's available after gas reserve
        usable_eth = min(eth_delta, max(0, int(eth_after) - gas_reserve))

        logger.debug(
            f"Post-borrow balances: ETH delta={eth_delta / 10**18:.6f}, "
            f"WETH delta={weth_delta / 10**18:.6f}, usable_eth={usable_eth / 10**18:.6f}"
        )

        # Always swap WETH (not ETH directly) - ETH swaps get bad fills.
        # If borrow arrived as native ETH, wrap it first.
        weth_bal = int(weth_after)

        if eth_delta > 0 and usable_eth > 0:
            # Borrow arrived as native ETH - wrap it first
            wrap_amt = min(int(safe_borrow_amt), int(usable_eth))
            logger.info(
                f"Borrow arrived as native ETH, wrapping {wrap_amt / 10**18:.6f} ETH to WETH"
            )
            wrap_success, wrap_msg = await self.moonwell_adapter.wrap_eth(
                amount=wrap_amt
            )
            if not wrap_success:
                raise Exception(f"Wrap ETH→WETH failed: {wrap_msg}")
            # WETH wrapping is 1:1, so we know exactly how much we have now
            # (avoids stale RPC reads after the wrap tx)
            weth_bal = int(weth_after) + wrap_amt
            logger.info(f"Post-wrap WETH balance (calculated): {weth_bal / 10**18:.6f}")
        elif weth_delta > 0:
            logger.info(f"Borrow arrived as WETH: {weth_delta / 10**18:.6f}")
        elif eth_delta == 0 and weth_delta == 0:
            # Borrow succeeded but balance reads are stale - assume it arrived as ETH
            # and try to wrap what we can (this is common on Base L2)
            available_eth = max(0, int(eth_after) - gas_reserve)
            if available_eth > 0:
                wrap_amt = min(int(safe_borrow_amt), available_eth)
                logger.warning(
                    f"Balance delta not detected but borrow succeeded. "
                    f"Assuming ETH arrival, wrapping {wrap_amt / 10**18:.6f} ETH"
                )
                wrap_success, wrap_msg = await self.moonwell_adapter.wrap_eth(
                    amount=wrap_amt
                )
                if not wrap_success:
                    raise Exception(f"Wrap ETH→WETH failed: {wrap_msg}")
                # WETH wrapping is 1:1, so we know exactly how much we have now
                weth_bal = int(weth_after) + wrap_amt
                logger.info(
                    f"Post-wrap WETH balance (calculated): {weth_bal / 10**18:.6f}"
                )

        amount_to_swap = min(int(safe_borrow_amt), int(weth_bal))

        if amount_to_swap <= 0:
            raise Exception(
                f"No WETH available to swap after borrowing (weth_bal={weth_bal})"
            )

        # Step 2: Swap WETH to wstETH with retries
        # Prefer enso/aerodrome for WETH→wstETH - LiFi gets bad fills
        swap_result = await self._swap_with_retries(
            from_token_id=WETH_TOKEN_ID,
            to_token_id=WSTETH_TOKEN_ID,
            amount=amount_to_swap,
            preferred_providers=["aerodrome", "enso"],
        )
        if swap_result is None:
            # Roll back: repay the borrowed amount to remain delta-neutral.
            try:
                # Prefer repaying directly with the borrowed WETH.
                weth_bal = await self._get_balance_raw(
                    token_id=WETH_TOKEN_ID, wallet_address=strategy_address
                )

                wrap_amt = 0
                if weth_bal < safe_borrow_amt:
                    # If the borrow surfaced as native ETH (or WETH was otherwise reduced),
                    # attempt to wrap ETH for the shortfall while preserving gas.
                    eth_bal = await self._get_balance_raw(
                        token_id=ETH_TOKEN_ID, wallet_address=strategy_address
                    )
                    gas_reserve = int(self.WRAP_GAS_RESERVE * 10**18)
                    available_for_wrap = max(0, eth_bal - gas_reserve)
                    shortfall = safe_borrow_amt - weth_bal
                    wrap_amt = min(shortfall, available_for_wrap)
                    if wrap_amt > 0:
                        wrap_success, wrap_msg = await self.moonwell_adapter.wrap_eth(
                            amount=wrap_amt
                        )
                        if not wrap_success:
                            raise Exception(f"Wrap ETH→WETH failed: {wrap_msg}")

                        weth_bal = await self._get_balance_raw(
                            token_id=WETH_TOKEN_ID, wallet_address=strategy_address
                        )

                repay_amt = min(safe_borrow_amt, weth_bal)
                if repay_amt <= 0:
                    raise Exception("No WETH available to repay the borrow")

                repay_success, repay_msg = await self.moonwell_adapter.repay(
                    mtoken=M_WETH,
                    underlying_token=WETH,
                    amount=repay_amt,
                )
                if not repay_success:
                    raise Exception(f"Repay failed: {repay_msg}")

                if repay_amt < safe_borrow_amt:
                    logger.warning(
                        f"Swap failed; only repaid {repay_amt / 10**18:.6f} of "
                        f"{safe_borrow_amt / 10**18:.6f} WETH. Position may be imbalanced."
                    )
                else:
                    logger.warning("Swap failed after retries. Borrow undone.")
            except Exception as repay_exc:
                raise Exception(
                    f"Swap failed after retries and reverting borrow failed: {repay_exc}. "
                    "Position may no longer be delta-neutral!"
                ) from repay_exc
            raise Exception("Atomic deposit failed at swap step after all retries")

        # Parse to_amount from swap result (may be int or string)
        raw_to_amount = (
            swap_result.get("to_amount", 0) if isinstance(swap_result, dict) else 0
        )
        try:
            to_amount_wei = int(raw_to_amount) if raw_to_amount else 0
        except (ValueError, TypeError):
            to_amount_wei = 0

        # Get actual wstETH balance
        wsteth_success, wsteth_bal_raw = await self.balance_adapter.get_balance(
            query=WSTETH_TOKEN_ID, wallet_address=self._get_strategy_wallet_address()
        )
        if not wsteth_success:
            raise Exception("Failed to get wstETH balance after swap")
        wsteth_bal = self._parse_balance(wsteth_bal_raw)

        # Use the smaller of balance check and swap result to avoid over-lending
        lend_amt_wei = (
            min(to_amount_wei, wsteth_bal) if wsteth_bal > 0 else to_amount_wei
        )

        # If swap produced 0 wstETH, rollback the borrow
        if lend_amt_wei <= 0:
            logger.warning("Swap resulted in 0 wstETH. Rolling back borrow...")
            try:
                # Get WETH balance to repay (swap may have returned WETH or nothing)
                weth_bal = await self._get_balance_raw(
                    token_id=WETH_TOKEN_ID, wallet_address=strategy_address
                )
                if weth_bal > 0:
                    repay_amt = min(weth_bal, safe_borrow_amt)
                    await self.moonwell_adapter.repay(
                        mtoken=M_WETH,
                        underlying_token=WETH,
                        amount=repay_amt,
                    )
                    logger.info(f"Rolled back: repaid {repay_amt / 10**18:.6f} WETH")
            except Exception as rollback_exc:
                raise Exception(
                    f"Swap produced 0 wstETH and rollback failed: {rollback_exc}. "
                    "Position may have excess WETH debt!"
                ) from rollback_exc
            raise Exception(
                "Swap resulted in 0 wstETH to lend. Borrow was rolled back."
            )

        # Step 3: Lend wstETH
        mwsteth_before = 0
        minted_mwsteth = 0
        try:
            mwsteth_pos_before = await self.moonwell_adapter.get_pos(mtoken=M_WSTETH)
            if mwsteth_pos_before[0] and isinstance(mwsteth_pos_before[1], dict):
                mwsteth_before = int(
                    (mwsteth_pos_before[1] or {}).get("mtoken_balance", 0) or 0
                )
        except Exception:  # noqa: BLE001
            mwsteth_before = 0

        try:
            success, msg = await self.moonwell_adapter.lend(
                mtoken=M_WSTETH,
                underlying_token=WSTETH,
                amount=lend_amt_wei,
            )
            if not success:
                raise Exception(f"Lend failed: {msg}")

            # Track minted mTokens so we can redeem the correct amount on rollback.
            try:
                mwsteth_pos_after = await self.moonwell_adapter.get_pos(mtoken=M_WSTETH)
                if mwsteth_pos_after[0] and isinstance(mwsteth_pos_after[1], dict):
                    mwsteth_after = int(
                        (mwsteth_pos_after[1] or {}).get("mtoken_balance", 0) or 0
                    )
                    minted_mwsteth = max(0, int(mwsteth_after) - int(mwsteth_before))
            except Exception:  # noqa: BLE001
                minted_mwsteth = 0

            set_coll_success, set_coll_msg = await self.moonwell_adapter.set_collateral(
                mtoken=M_WSTETH
            )
            if not set_coll_success:
                # Must redeem mTokens (not underlying) since wstETH is now in protocol, not wallet.
                to_redeem = minted_mwsteth
                if to_redeem <= 0:
                    # Fallback: redeem whatever balance we can see (best-effort).
                    mwsteth_pos = await self.moonwell_adapter.get_pos(mtoken=M_WSTETH)
                    if mwsteth_pos[0] and isinstance(mwsteth_pos[1], dict):
                        to_redeem = int(
                            (mwsteth_pos[1] or {}).get("mtoken_balance", 0) or 0
                        )
                if to_redeem > 0:
                    await self.moonwell_adapter.unlend(
                        mtoken=M_WSTETH, amount=to_redeem
                    )
                raise Exception(
                    f"set_collateral failed: {set_coll_msg}. Lend reversed."
                )
            logger.info(f"Lent {lend_amt_wei / 10**18:.6f} wstETH")

        except Exception as lend_exc:
            # Roll back: swap wstETH back to WETH and repay (only if we have wstETH)
            try:
                # Ensure wstETH is in the wallet (redeem minted mwstETH if needed).
                rollback_wsteth = await self._get_balance_raw(
                    token_id=WSTETH_TOKEN_ID, wallet_address=strategy_address
                )
                if rollback_wsteth <= 0 and minted_mwsteth > 0:
                    await self.moonwell_adapter.unlend(
                        mtoken=M_WSTETH, amount=minted_mwsteth
                    )
                    rollback_wsteth = await self._get_balance_raw(
                        token_id=WSTETH_TOKEN_ID, wallet_address=strategy_address
                    )

                if rollback_wsteth > 0:
                    (
                        revert_success,
                        revert_result,
                    ) = await self.brap_adapter.swap_from_token_ids(
                        from_token_id=WSTETH_TOKEN_ID,
                        to_token_id=WETH_TOKEN_ID,
                        from_address=strategy_address,
                        amount=str(rollback_wsteth),
                    )
                    if revert_success and revert_result:
                        weth_after = await self._get_balance_raw(
                            token_id=WETH_TOKEN_ID, wallet_address=strategy_address
                        )
                        repay_amt = min(weth_after, safe_borrow_amt)
                        if repay_amt > 0:
                            await self.moonwell_adapter.repay(
                                mtoken=M_WETH,
                                underlying_token=WETH,
                                amount=repay_amt,
                            )
                else:
                    logger.warning(
                        f"Lend failed but no wstETH to rollback. Lend error: {lend_exc}"
                    )
            except Exception as revert_exc:
                raise Exception(
                    f"Lend failed: {lend_exc} and revert failed: {revert_exc}"
                ) from revert_exc
            raise Exception(
                f"Deposit to wstETH failed and was reverted: {lend_exc}"
            ) from lend_exc

        return lend_amt_wei

    async def partial_liquidate(self, usd_value: float) -> StatusTuple:
        """Create USDC liquidity in the strategy wallet by safely redeeming collateral."""
        self._clear_price_cache()

        if usd_value <= 0:
            raise ValueError(f"usd_value must be positive, got {usd_value}")

        strategy_address = self._get_strategy_wallet_address()

        usdc_info = await self._get_token_info(USDC_TOKEN_ID)
        usdc_decimals = usdc_info.get("decimals", 6)

        # (1) Check current USDC in wallet
        usdc_raw = await self._get_usdc_balance()
        current_usdc = usdc_raw / (10**usdc_decimals)
        if current_usdc >= usd_value:
            target_raw = int(usd_value * (10**usdc_decimals))
            available = min(usdc_raw, target_raw) / (10**usdc_decimals)
            return (
                True,
                f"Partial liquidation not needed. Available: {available:.2f} USDC",
            )

        missing = usd_value - current_usdc

        # (2) Fetch Moonwell positions and collateral factors
        (_totals_token, total_usd_bals), collateral_factors = await asyncio.gather(
            self._aggregate_positions(),
            self._get_collateral_factors(),
        )

        key_wsteth = f"Base_{M_WSTETH}"
        key_weth = f"Base_{WETH}"
        key_usdc = f"Base_{M_USDC}"

        wsteth_usd = float(total_usd_bals.get(key_wsteth, 0.0))
        weth_debt_usd = abs(float(total_usd_bals.get(key_weth, 0.0)))

        # (2a) If wstETH collateral exceeds WETH debt, redeem some wstETH and swap to USDC
        if missing > 0 and wsteth_usd > weth_debt_usd:
            unlend_usd = min(missing, wsteth_usd - weth_debt_usd)
            if await self._can_withdraw_token(
                total_usd_bals,
                key_wsteth,
                unlend_usd,
                collateral_factors=collateral_factors,
            ):
                wsteth_price = await self._get_token_price(WSTETH_TOKEN_ID)
                if not wsteth_price or wsteth_price <= 0:
                    return (False, "Invalid wstETH price")

                wsteth_info = await self._get_token_info(WSTETH_TOKEN_ID)
                wsteth_decimals = wsteth_info.get("decimals", 18)

                token_qty = unlend_usd / wsteth_price
                unlend_underlying_raw = int(token_qty * (10**wsteth_decimals))

                if unlend_underlying_raw > 0:
                    mwsteth_res = await self.moonwell_adapter.max_withdrawable_mtoken(
                        mtoken=M_WSTETH
                    )
                    if mwsteth_res[0]:
                        withdraw_info = mwsteth_res[1]
                        max_ctokens = int(withdraw_info.get("cTokens_raw", 0))
                        exchange_rate_raw = int(
                            withdraw_info.get("exchangeRate_raw", 0)
                        )
                        conversion_factor = float(
                            withdraw_info.get("conversion_factor", 0) or 0
                        )

                        if max_ctokens > 0:
                            if exchange_rate_raw > 0:
                                # underlying = cTokens * exchangeRate / 1e18
                                ctokens_needed = (
                                    unlend_underlying_raw * 10**18
                                    + exchange_rate_raw
                                    - 1
                                ) // exchange_rate_raw
                            elif conversion_factor > 0:
                                ctokens_needed = (
                                    int(conversion_factor * unlend_underlying_raw) + 1
                                )
                            else:
                                ctokens_needed = max_ctokens

                            ctokens_to_redeem = min(int(ctokens_needed), max_ctokens)
                            if ctokens_to_redeem > 0:
                                success, msg = await self.moonwell_adapter.unlend(
                                    mtoken=M_WSTETH, amount=ctokens_to_redeem
                                )
                                if not success:
                                    return (
                                        False,
                                        f"Failed to redeem mwstETH for partial liquidation: {msg}",
                                    )

                                # Swap withdrawn wstETH → USDC
                                wsteth_wallet_raw = await self._get_balance_raw(
                                    token_id=WSTETH_TOKEN_ID,
                                    wallet_address=strategy_address,
                                )
                                amount_to_swap = min(
                                    wsteth_wallet_raw, unlend_underlying_raw
                                )
                                if amount_to_swap > 0:
                                    swap_res = await self._swap_with_retries(
                                        from_token_id=WSTETH_TOKEN_ID,
                                        to_token_id=USDC_TOKEN_ID,
                                        amount=amount_to_swap,
                                    )
                                    if swap_res is None:
                                        # Restore collateral if swap fails
                                        restore_amt = min(
                                            amount_to_swap, wsteth_wallet_raw
                                        )
                                        if restore_amt > 0:
                                            await self.moonwell_adapter.lend(
                                                mtoken=M_WSTETH,
                                                underlying_token=WSTETH,
                                                amount=restore_amt,
                                            )
                                            await self.moonwell_adapter.set_collateral(
                                                mtoken=M_WSTETH
                                            )

        # (3) Re-check wallet USDC balance
        usdc_raw = await self._get_balance_raw(
            token_id=USDC_TOKEN_ID, wallet_address=strategy_address
        )
        current_usdc = usdc_raw / (10**usdc_decimals)

        # (4) If still short, redeem USDC collateral directly
        if current_usdc < usd_value:
            # Refresh Moonwell balances after any prior redemptions/swaps.
            (_totals_token, total_usd_bals) = await self._aggregate_positions()

            missing_usdc = usd_value - current_usdc
            available_usdc = float(total_usd_bals.get(key_usdc, 0.0))

            if missing_usdc > 0 and available_usdc > 0:
                unlend_usdc = min(missing_usdc, available_usdc)
                if await self._can_withdraw_token(
                    total_usd_bals,
                    key_usdc,
                    unlend_usdc,
                    collateral_factors=collateral_factors,
                ):
                    unlend_underlying_raw = int(unlend_usdc * (10**usdc_decimals))
                    if unlend_underlying_raw > 0:
                        musdc_res = await self.moonwell_adapter.max_withdrawable_mtoken(
                            mtoken=M_USDC
                        )
                        if not musdc_res[0]:
                            return (
                                False,
                                f"Failed to compute withdrawable mUSDC: {musdc_res[1]}",
                            )
                        withdraw_info = musdc_res[1]
                        max_ctokens = int(withdraw_info.get("cTokens_raw", 0))
                        exchange_rate_raw = int(
                            withdraw_info.get("exchangeRate_raw", 0)
                        )
                        conversion_factor = float(
                            withdraw_info.get("conversion_factor", 0) or 0
                        )

                        if max_ctokens > 0:
                            if exchange_rate_raw > 0:
                                ctokens_needed = (
                                    unlend_underlying_raw * 10**18
                                    + exchange_rate_raw
                                    - 1
                                ) // exchange_rate_raw
                            elif conversion_factor > 0:
                                ctokens_needed = (
                                    int(conversion_factor * unlend_underlying_raw) + 1
                                )
                            else:
                                ctokens_needed = max_ctokens

                            ctokens_to_redeem = min(int(ctokens_needed), max_ctokens)
                            if ctokens_to_redeem > 0:
                                success, msg = await self.moonwell_adapter.unlend(
                                    mtoken=M_USDC, amount=ctokens_to_redeem
                                )
                                if not success:
                                    return (
                                        False,
                                        f"Failed to redeem mUSDC for partial liquidation: {msg}",
                                    )

        # (5) Final available USDC (capped to target)
        usdc_raw = await self._get_balance_raw(
            token_id=USDC_TOKEN_ID, wallet_address=strategy_address
        )
        target_raw = int(usd_value * (10**usdc_decimals))
        final_raw = min(usdc_raw, target_raw)

        if final_raw <= 0:
            return (False, "Partial liquidation produced no USDC")

        final_usdc = final_raw / (10**usdc_decimals)
        if final_raw < target_raw:
            return (
                True,
                f"Partial liquidation completed. Available: {final_usdc:.2f} USDC (requested {usd_value:.2f})",
            )
        return (
            True,
            f"Partial liquidation completed. Available: {final_usdc:.2f} USDC",
        )

    async def _execute_deposit_loop(self, usdc_amount: float) -> tuple[bool, Any, int]:
        """Execute the recursive leverage loop."""
        token_info = await self._get_token_info(USDC_TOKEN_ID)
        decimals = token_info.get("decimals", 6)
        initial_deposit = int(usdc_amount * 10**decimals)

        # Fetch prices and collateral factors in parallel (use cache, minimal RPC)
        wsteth_price, weth_price, collateral_factors = await asyncio.gather(
            self._get_token_price(WSTETH_TOKEN_ID),
            self._get_token_price(WETH_TOKEN_ID),
            self._get_collateral_factors(),
        )

        # Fetch position separately to avoid overwhelming public RPC
        weth_pos = await self.moonwell_adapter.get_pos(mtoken=M_WETH)

        current_borrowed_value = 0.0
        if weth_pos[0]:
            borrow_bal = weth_pos[1].get("borrow_balance", 0)
            current_borrowed_value = (borrow_bal / 10**18) * weth_price

        # Lend USDC and enable as collateral
        success, msg = await self.moonwell_adapter.lend(
            mtoken=M_USDC,
            underlying_token=USDC,
            amount=initial_deposit,
        )
        if not success:
            return (False, f"Initial USDC lend failed: {msg}", 0)

        await self.moonwell_adapter.set_collateral(mtoken=M_USDC)
        logger.info(f"Deposited {usdc_amount:.2f} USDC as initial collateral")

        # Get current leverage (positions changed after lend, must re-fetch)
        (
            usdc_lend_value,
            wsteth_lend_value,
            initial_leverage,
        ) = await self._get_current_leverage()

        return await self._loop_wsteth(
            wsteth_price=wsteth_price,
            weth_price=weth_price,
            current_borrowed_value=current_borrowed_value,
            initial_leverage=initial_leverage,
            usdc_lend_value=usdc_lend_value,
            wsteth_lend_value=wsteth_lend_value,
            collateral_factors=collateral_factors,
        )

    async def _loop_wsteth(
        self,
        wsteth_price: float,
        weth_price: float,
        current_borrowed_value: float,
        initial_leverage: float,
        usdc_lend_value: float,
        wsteth_lend_value: float,
        collateral_factors: tuple[float, float] | None = None,
    ) -> tuple[bool, Any, int]:
        """Execute leverage loop until target health factor reached.

        Args:
            collateral_factors: Optional (cf_usdc, cf_wsteth) tuple.
                                If provided, skips collateral factor fetches.
        """
        # Ensure USDC and wstETH markets are entered as collateral before borrowing
        # This is idempotent - if already entered, Moonwell just returns success
        if usdc_lend_value > 0:
            set_coll_result = await self.moonwell_adapter.set_collateral(mtoken=M_USDC)
            if not set_coll_result[0]:
                logger.warning(
                    f"Failed to ensure USDC collateral: {set_coll_result[1]}"
                )
                return (
                    False,
                    f"Failed to enable USDC as collateral: {set_coll_result[1]}",
                    0,
                )

        if wsteth_lend_value > 0:
            set_coll_result = await self.moonwell_adapter.set_collateral(
                mtoken=M_WSTETH
            )
            if not set_coll_result[0]:
                logger.warning(
                    f"Failed to ensure wstETH collateral: {set_coll_result[1]}"
                )
                # This is less critical - we can continue if wstETH collateral fails

        # Enter M_WETH market to allow borrowing from it
        # In Compound v2/Moonwell, you must be in a market to borrow from it
        # (enterMarkets enables both collateral usage AND borrowing)
        set_weth_result = await self.moonwell_adapter.set_collateral(mtoken=M_WETH)
        if not set_weth_result[0]:
            logger.warning(f"Failed to enter M_WETH market: {set_weth_result[1]}")
            return (
                False,
                f"Failed to enter M_WETH market for borrowing: {set_weth_result[1]}",
                0,
            )
        logger.info("Entered M_WETH market to enable borrowing")

        # Use provided collateral factors or fetch them
        if collateral_factors is not None:
            cf_u, cf_w = collateral_factors
        else:
            cf_u, cf_w = await self._get_collateral_factors()

        # Calculate depeg-aware max safe leverage fraction
        max_safe_f = self._max_safe_F(cf_w)

        # Guard against division by zero/negative denominator
        denominator = self.MIN_HEALTH_FACTOR + 0.001 - cf_w
        if denominator <= 0:
            logger.warning(
                f"Cannot calculate target borrow: cf_w ({cf_w:.3f}) >= MIN_HF ({self.MIN_HEALTH_FACTOR})"
            )
            return (False, initial_leverage, -1)

        # Calculate target borrow value
        target_borrow_value = (
            usdc_lend_value * cf_u / denominator - current_borrowed_value
        )

        if target_borrow_value < 0:
            return (False, initial_leverage, -1)

        # Track wstETH added THIS session (starts at 0), not total position
        session_wsteth_lend_value = 0.0
        total_wsteth_lend_value = wsteth_lend_value
        raw_leverage_limit = (
            (current_borrowed_value + target_borrow_value) / usdc_lend_value + 1
            if usdc_lend_value
            else 0
        )

        # Apply depeg-aware leverage cap
        max_safe_leverage = max_safe_f * usdc_lend_value + 1 if usdc_lend_value else 0
        leverage_limit = min(raw_leverage_limit, max_safe_leverage, self.leverage_limit)

        leverage_tracker: list[float] = [initial_leverage]

        for i in range(self._MAX_LOOP_LIMIT):
            # Get borrowable amount (returns USD with 18 decimals)
            borrowable_result = await self.moonwell_adapter.get_borrowable_amount()
            if not borrowable_result[0]:
                logger.warning("Failed to get borrowable amount")
                break

            if not weth_price or weth_price <= 0:
                logger.warning("Invalid WETH price; breaking loop")
                break

            borrowable_usd = self._normalize_usd_value(borrowable_result[1])
            if borrowable_usd <= self.min_withdraw_usd:
                logger.info("No additional borrowing possible; breaking loop")
                break

            weth_info = await self._get_token_info(WETH_TOKEN_ID)
            weth_decimals = weth_info.get("decimals", 18)
            # Convert USD to WETH wei: (USD / price) * 10^decimals
            max_borrow_wei = int(borrowable_usd / weth_price * 10**weth_decimals)

            # remaining_value is how much more we need to borrow/lend THIS session
            remaining_value = target_borrow_value - session_wsteth_lend_value
            remaining_wei = int(remaining_value / weth_price * 10**weth_decimals) + 1

            if remaining_value < 2:
                logger.info(
                    f"Target reached: borrowed/lent ${session_wsteth_lend_value:.2f} of ${target_borrow_value:.2f} target"
                )
                break

            # Scale up for swap slippage
            optimal_this_iter = int(remaining_wei / (1 - 0.005))
            borrow_amt_wei = min(optimal_this_iter, max_borrow_wei)

            current_leverage = leverage_tracker[-1]
            logger.info(
                f"Current leverage {current_leverage:.2f}x. "
                f"Borrowing {borrow_amt_wei / 10**weth_decimals:.6f} WETH"
            )

            try:
                lend_amt_wei = await self._atomic_deposit_iteration(borrow_amt_wei)
            except Exception as e:
                logger.error(f"Deposit iteration aborted: {e}")
                return (False, f"deposit iteration {i + 1} failed: {e}", i)

            wsteth_info = await self._get_token_info(WSTETH_TOKEN_ID)
            wsteth_decimals = wsteth_info.get("decimals", 18)

            lend_value_this_iter = wsteth_price * lend_amt_wei / 10**wsteth_decimals
            session_wsteth_lend_value += lend_value_this_iter
            total_wsteth_lend_value += lend_value_this_iter
            leverage_tracker.append(total_wsteth_lend_value / usdc_lend_value + 1)

            # Stop if max leverage or marginal gain < threshold (diminishing returns vs gas cost)
            if (leverage_tracker[-1] > leverage_limit) or (
                len(leverage_tracker) > 1
                and leverage_tracker[-1] / leverage_tracker[-2] - 1
                < self._MIN_LEVERAGE_GAIN_BPS
            ):
                logger.info(
                    f"Finished loop, final leverage: {leverage_tracker[-1]:.2f}"
                )
                break

        if len(leverage_tracker) == 1:
            return (False, leverage_tracker[-1], 0)

        return (True, leverage_tracker[-1], len(leverage_tracker) - 1)

    async def update(self) -> StatusTuple:
        """Rebalance positions. Runs deposit loop only if HF > MAX_HEALTH_FACTOR."""
        self._clear_price_cache()

        # Best-effort top-up if we dipped below MIN_GAS (non-critical).
        topup_success, topup_msg = await self._transfer_gas_to_vault()
        if not topup_success:
            logger.warning(f"Gas top-up failed (non-critical): {topup_msg}")

        gas_amt = await self._get_gas_balance()
        if gas_amt < int(self.MAINTENANCE_GAS * 10**18):
            return (
                False,
                f"Less than {self.MAINTENANCE_GAS} ETH in strategy wallet. Please transfer more gas.",
            )

        # Recovery: if a previous loop borrowed WETH but failed to swap/lend, complete it first.
        try:
            completed, msg = await self._complete_unpaired_weth_borrow()
            if not completed:
                logger.warning(
                    f"Unpaired borrow completion failed (will continue): {msg}"
                )
        except Exception as exc:
            return (False, f"Failed while completing unpaired borrow: {exc}")

        # Balance WETH debt first (critical for delta-neutrality)
        balance_success, balance_msg = await self._balance_weth_debt()
        if not balance_success:
            return (
                False,
                f"Failed to balance WETH debt: {balance_msg}. Consider calling withdraw to unwind safely.",
            )

        # If we are holding excess native ETH, convert it into USDC so it can be redeployed.
        try:
            converted, msg = await self._convert_excess_eth_to_usdc()
            if not converted:
                logger.warning(f"Excess ETH conversion failed (non-critical): {msg}")
        except SwapOutcomeUnknownError as exc:
            return (False, f"Swap outcome unknown while converting excess ETH: {exc}")
        except Exception as exc:
            logger.warning(f"Excess ETH conversion raised (non-critical): {exc}")

        # Fetch positions and collateral factors in parallel (single fetch for update)
        positions_task = self._aggregate_positions()
        cf_task = self._get_collateral_factors()
        (totals_token, totals_usd), collateral_factors = await asyncio.gather(
            positions_task, cf_task
        )

        # Compute health factor using pre-fetched data
        ltv = await self.compute_ltv(totals_usd, collateral_factors=collateral_factors)
        hf = (1 / ltv) if ltv and ltv > 0 and not (ltv != ltv) else float("inf")

        # Check if we need to deleverage
        if hf < self.MIN_HEALTH_FACTOR:
            cf_u, cf_w = collateral_factors

            usdc_key = f"Base_{M_USDC}"
            weth_key = f"Base_{WETH}"

            c_u = totals_usd.get(usdc_key, 0)
            debt = abs(totals_usd.get(weth_key, 0))

            repay_usd = debt - (cf_u * c_u) / (self.MIN_HEALTH_FACTOR + 1e-4 - cf_w)
            weth_price = await self._get_token_price(WETH_TOKEN_ID)

            repay_amt = int(repay_usd / weth_price * 10**18) + 1
            success, msg = await self._repay_debt_loop(target_repaid=repay_amt)

            if not success:
                return (
                    False,
                    f"Health factor is {hf:.2f} which is dangerous. Deleveraging failed: {msg}",
                )
            return (success, msg)

        # Claim rewards if above threshold
        await self.moonwell_adapter.claim_rewards(min_rewards_usd=self.MIN_USDC_DEPOSIT)

        # Check profitability
        success, msg = await self._check_quote_profitability()
        if not success:
            return (False, msg)

        # If we have idle wallet wstETH (spot long), convert it to USDC so it can be redeployed
        # via the leverage loop. This does not affect native ETH gas.
        try:
            converted, conv_msg = await self._convert_spot_wsteth_to_usdc()
            if not converted:
                logger.warning(
                    f"Wallet wstETH conversion failed (non-critical): {conv_msg}"
                )
        except SwapOutcomeUnknownError as exc:
            return (
                False,
                f"Swap outcome unknown while converting wallet wstETH: {exc}",
            )
        except Exception as exc:
            logger.warning(f"Wallet wstETH conversion raised (non-critical): {exc}")

        # Get USDC balance in wallet
        usdc_balance_wei = await self._get_usdc_balance()
        token_info = await self._get_token_info(USDC_TOKEN_ID)
        decimals = token_info.get("decimals", 6)
        usdc_balance = usdc_balance_wei / 10**decimals

        # Get lend values from already-fetched aggregate positions
        usdc_key = f"Base_{M_USDC}"
        wsteth_key = f"Base_{M_WSTETH}"
        usdc_lend_value = totals_usd.get(usdc_key, 0)
        wsteth_lend_value = totals_usd.get(wsteth_key, 0)
        initial_leverage = (
            wsteth_lend_value / usdc_lend_value + 1 if usdc_lend_value else 0
        )

        # If we have meaningful USDC in-wallet, redeploy it regardless of current HF.
        if usdc_balance >= self.MIN_USDC_DEPOSIT:
            success, final_leverage, n_loops = await self._execute_deposit_loop(
                usdc_balance
            )
            if not success:
                return (
                    False,
                    f"Redeploy loop failed: {final_leverage} after {n_loops} successful loops",
                )
            return (
                True,
                f"Redeployed {usdc_balance:.2f} USDC to {final_leverage:.2f}x with {n_loops} loops",
            )

        # Lever-up when HF is significantly above target (MIN_HEALTH_FACTOR).
        # Only skip if HF is close enough to target (within HF_LEVER_UP_BUFFER).
        lever_up_threshold = self.MIN_HEALTH_FACTOR + self.HF_LEVER_UP_BUFFER
        if hf <= lever_up_threshold:
            return (
                True,
                f"HF={hf:.3f} <= target+buffer({lever_up_threshold:.2f}); no action needed.",
            )

        # Use 95% threshold to handle rounding/slippage from deposit
        min_lend_threshold = self.MIN_USDC_DEPOSIT * 0.95
        if (
            usdc_balance < self.MIN_USDC_DEPOSIT
            and usdc_lend_value < min_lend_threshold
        ):
            return (
                False,
                f"No USDC lent ({usdc_lend_value:.2f}) and not enough in wallet ({usdc_balance:.2f}). Deposit funds.",
            )

        if usdc_balance < self.MIN_USDC_DEPOSIT:
            # Lever-up path - use pre-fetched data
            wsteth_price = await self._get_token_price(WSTETH_TOKEN_ID)
            weth_price = await self._get_token_price(WETH_TOKEN_ID)

            weth_key = f"Base_{WETH}"
            current_borrowed_value = abs(totals_usd.get(weth_key, 0))

            success, final_leverage, n_loops = await self._loop_wsteth(
                wsteth_price=wsteth_price,
                weth_price=weth_price,
                current_borrowed_value=current_borrowed_value,
                initial_leverage=initial_leverage,
                usdc_lend_value=usdc_lend_value,
                wsteth_lend_value=wsteth_lend_value,
                collateral_factors=collateral_factors,
            )
            if not success:
                return (
                    False,
                    f"Leverage was {initial_leverage:.2f}x; adjustment failed. "
                    f"Final: {final_leverage} after {n_loops} loops",
                )
            return (
                True,
                f"Adjusted leverage from {initial_leverage:.2f}x to {final_leverage:.2f}x "
                f"via {n_loops} loops",
            )

        # Full redeposit loop
        success, final_leverage, n_loops = await self._execute_deposit_loop(
            usdc_balance
        )
        if not success:
            return (
                False,
                f"Loop failed: {final_leverage} after {n_loops} successful loops",
            )
        return (
            True,
            f"Executed redeposit loop to {final_leverage:.2f}x with {n_loops} loops",
        )

    async def _repay_debt_loop(
        self, target_repaid: int | None = None
    ) -> tuple[bool, str]:
        """Iteratively repay debt."""
        total_repaid = 0

        if target_repaid is not None and target_repaid < 0:
            return (False, "Target repay was negative")

        for _ in range(self._MAX_LOOP_LIMIT * 2):
            # Get current debt
            pos_result = await self.moonwell_adapter.get_pos(mtoken=M_WETH)
            if not pos_result[0]:
                break

            current_debt = pos_result[1].get("borrow_balance", 0)
            if current_debt < 1:
                break

            # Attempt repayment
            try:
                repaid = await self._safe_repay(current_debt)
            except SwapOutcomeUnknownError as exc:
                return (False, f"Swap outcome unknown during debt repayment: {exc}")
            if repaid == 0:
                break

            total_repaid += repaid

            if target_repaid is not None and total_repaid >= target_repaid:
                return (True, f"Repaid {total_repaid} > {target_repaid} target")

        # Check remaining debt
        pos_result = await self.moonwell_adapter.get_pos(mtoken=M_WETH)
        if not pos_result[0]:
            return (False, "Failed to check remaining debt after repayment")

        remaining_debt = pos_result[1].get("borrow_balance", 0)

        if remaining_debt > 0:
            return (
                False,
                f"Could not repay all debt. Remaining: {remaining_debt / 10**18:.6f} WETH",
            )

        return (True, "Debt repayment completed")

    async def _emergency_eth_repayment(self, debt: int) -> tuple[bool, str]:
        """Emergency fallback to repay debt using available ETH."""
        gas_balance = await self._get_gas_balance()
        # Reserve for gas: base reserve + buffer for wrap + repay tx gas
        tx_gas_buffer = int(0.001 * 10**18)  # ~0.001 ETH for wrap + repay txs
        gas_buffer = int(self.WRAP_GAS_RESERVE * 10**18) + tx_gas_buffer

        logger.debug(
            f"Emergency repay check: gas_balance={gas_balance / 10**18:.6f}, "
            f"gas_buffer={gas_buffer / 10**18:.6f}, debt={debt / 10**18:.6f}"
        )

        if gas_balance > gas_buffer:
            available_eth = gas_balance - gas_buffer
            repay_amt = min(available_eth, debt)

            try:
                wrap_success, wrap_msg = await self.moonwell_adapter.wrap_eth(
                    amount=repay_amt
                )
                if not wrap_success:
                    logger.warning(f"Emergency wrap failed: {wrap_msg}")
                    return (False, f"Wrap failed: {wrap_msg}")

                # Only use repay_full=True when we have enough to cover full debt
                can_repay_full = repay_amt >= debt
                success, _ = await self.moonwell_adapter.repay(
                    mtoken=M_WETH,
                    underlying_token=WETH,
                    amount=repay_amt,
                    repay_full=can_repay_full,
                )
                if success:
                    logger.info(f"Emergency repayment: {repay_amt / 10**18:.6f} WETH")
                    return (True, f"Emergency repaid {repay_amt}")
                else:
                    logger.warning("Emergency repayment transaction failed")
                    return (False, "Repay transaction failed")
            except Exception as e:
                logger.warning(f"Emergency ETH repayment failed: {e}")
                return (False, str(e))

        return (False, "Insufficient ETH for emergency repayment")

    async def _repay_weth(self, amount: int, remaining_debt: int) -> int:
        """Repay WETH debt. Returns amount actually repaid."""
        if amount <= 0:
            return 0
        repay_amt = min(amount, remaining_debt)
        success, _ = await self.moonwell_adapter.repay(
            mtoken=M_WETH,
            underlying_token=WETH,
            amount=repay_amt,
            repay_full=(repay_amt >= remaining_debt),
        )
        return repay_amt if success else 0

    async def _swap_to_weth_and_repay(
        self, token_id: str, amount: int, remaining_debt: int
    ) -> int:
        """Swap token to WETH and repay. Returns amount repaid."""
        swap_result = await self._swap_with_retries(
            from_token_id=token_id, to_token_id=WETH_TOKEN_ID, amount=amount
        )
        if not swap_result:
            return 0

        # Use swap quote amount as minimum expected, retry balance read until we see it
        expected_weth = int(swap_result.get("to_amount") or 0)
        addr = self._get_strategy_wallet_address()
        weth_bal = 0

        for attempt in range(5):
            weth_bal = await self._get_balance_raw(
                token_id=WETH_TOKEN_ID, wallet_address=addr
            )
            if weth_bal >= expected_weth * 0.95 or weth_bal > 0:
                break
            logger.debug(
                f"WETH balance read {weth_bal}, expected ~{expected_weth}, retrying..."
            )
            await asyncio.sleep(1 + attempt)

        if weth_bal <= 0:
            logger.warning(
                f"WETH balance still 0 after swap, using estimate {expected_weth}"
            )
            weth_bal = expected_weth

        return await self._repay_weth(weth_bal, remaining_debt)

    async def _safe_repay(self, debt_to_repay: int) -> int:
        """Attempt repayment using all available assets. Returns total amount repaid."""
        if debt_to_repay < 1:
            return 0

        repaid = 0
        addr = self._get_strategy_wallet_address()

        # 1. Use wallet WETH directly
        weth_bal = await self._get_balance_raw(
            token_id=WETH_TOKEN_ID, wallet_address=addr
        )
        if weth_bal > 0:
            repaid += await self._repay_weth(weth_bal, debt_to_repay - repaid)
            if repaid >= debt_to_repay:
                return repaid

        # 2. Wrap ETH (above gas reserve) and repay
        eth_bal = await self._get_balance_raw(
            token_id=ETH_TOKEN_ID, wallet_address=addr
        )
        gas_reserve = int((self.WRAP_GAS_RESERVE + 0.0005) * 10**18)
        usable_eth = max(0, eth_bal - gas_reserve)
        if usable_eth > 0:
            wrap_amt = min(usable_eth, debt_to_repay - repaid)
            wrap_ok, _ = await self.moonwell_adapter.wrap_eth(amount=wrap_amt)
            if wrap_ok:
                weth_bal = await self._get_balance_raw(
                    token_id=WETH_TOKEN_ID, wallet_address=addr
                )
                repaid += await self._repay_weth(weth_bal, debt_to_repay - repaid)
                if repaid >= debt_to_repay:
                    return repaid

        # 3. Swap wallet assets (wstETH, USDC) to WETH and repay
        weth_price, weth_dec = await self._get_token_data(WETH_TOKEN_ID)
        if not weth_price or weth_price <= 0:
            return repaid

        for token_id in [WSTETH_TOKEN_ID, USDC_TOKEN_ID]:
            remaining = debt_to_repay - repaid
            if remaining <= 0:
                return repaid

            bal = await self._get_balance_raw(token_id=token_id, wallet_address=addr)
            if bal <= 0:
                continue

            price, dec = await self._get_token_data(token_id)
            if not price or price <= 0:
                continue

            bal_usd = (bal / 10**dec) * price
            if bal_usd < self.min_withdraw_usd:
                continue

            # Swap only what's needed (with 2% slippage buffer)
            needed_usd = (remaining / 10**weth_dec) * weth_price * 1.02
            needed_raw = int(needed_usd / price * 10**dec) + 1
            swap_amt = min(bal, needed_raw)

            logger.info(
                f"Swapping {swap_amt / 10**dec:.6f} {token_id} to WETH for repayment"
            )
            repaid += await self._swap_to_weth_and_repay(
                token_id, swap_amt, debt_to_repay - repaid
            )

        # 4. Unlend collateral, swap to WETH, and repay
        for mtoken, token_id in [(M_WSTETH, WSTETH_TOKEN_ID), (M_USDC, USDC_TOKEN_ID)]:
            remaining = debt_to_repay - repaid
            if remaining <= 0:
                return repaid

            withdraw_result = await self.moonwell_adapter.max_withdrawable_mtoken(
                mtoken=mtoken
            )
            if not withdraw_result[0]:
                continue

            withdraw_info = withdraw_result[1]
            underlying_raw = withdraw_info.get("underlying_raw", 0)
            if underlying_raw < 1:
                continue

            price, dec = await self._get_token_data(token_id)
            if not price or price <= 0:
                continue

            avail_raw = int(underlying_raw * COLLATERAL_SAFETY_FACTOR)
            avail_usd = (avail_raw / 10**dec) * price
            if avail_usd <= self.min_withdraw_usd:
                continue

            # Calculate needed amount with buffer
            remaining_usd = (remaining / 10**weth_dec) * weth_price
            target_usd = max(remaining_usd * 1.02, float(self.min_withdraw_usd))
            needed_raw = int(target_usd / price * 10**dec) + 1
            unlend_raw = min(avail_raw, needed_raw)

            mtoken_amt = self._mtoken_amount_for_underlying(withdraw_info, unlend_raw)
            if mtoken_amt <= 0:
                continue

            success, _ = await self.moonwell_adapter.unlend(
                mtoken=mtoken, amount=mtoken_amt
            )
            if not success:
                continue

            # Swap what we unlended
            bal = await self._get_balance_raw(token_id=token_id, wallet_address=addr)
            swap_amt = min(bal, unlend_raw)
            if swap_amt <= 0:
                continue

            logger.info(f"Swapping {swap_amt / 10**dec:.6f} unlent {token_id} to WETH")
            amt_repaid = await self._swap_to_weth_and_repay(
                token_id, swap_amt, remaining
            )
            if amt_repaid > 0:
                repaid += amt_repaid
            else:
                # Swap failed - re-lend to restore position
                logger.warning(f"Swap failed for {token_id}, re-lending")
                underlying = WSTETH if mtoken == M_WSTETH else USDC
                relend_bal = await self._get_balance_raw(
                    token_id=token_id, wallet_address=addr
                )
                if relend_bal > 0:
                    await self.moonwell_adapter.lend(
                        mtoken=mtoken, underlying_token=underlying, amount=relend_bal
                    )

        # Emergency fallback: use available ETH when nothing else worked
        if repaid == 0 and debt_to_repay > 0:
            success, _ = await self._emergency_eth_repayment(debt_to_repay)
            if success:
                pos_result = await self.moonwell_adapter.get_pos(mtoken=M_WETH)
                if pos_result[0]:
                    new_debt = pos_result[1].get("borrow_balance", 0)
                    repaid = debt_to_repay - new_debt
                    logger.info(
                        f"Emergency repayment succeeded: {repaid / 10**18:.6f} WETH"
                    )

        return repaid

    async def withdraw(self, amount: float | None = None) -> StatusTuple:
        """Withdraw funds. If amount is None, withdraws all.

        Logic:
        1. Liquidate any Moonwell positions to USDC (if any exist)
        2. Transfer any USDC > 0 to main wallet (regardless of step 1)
        """
        self._clear_price_cache()

        # Step 1: Liquidate Moonwell positions if any exist
        totals_token, totals_usd = await self._aggregate_positions()
        has_positions = len(totals_token) > 0

        if has_positions:
            # Sweep misc tokens to WETH first (helps with repayment)
            await self._sweep_token_balances(
                target_token_id=WETH_TOKEN_ID,
                exclude={USDC_TOKEN_ID, WSTETH_TOKEN_ID},
            )

            # Execute debt repayment loop
            success, message = await self._repay_debt_loop()
            if not success:
                return (False, message)

            # Unlend and convert remaining positions to USDC
            await self._unlend_remaining_positions()

        # Always sweep any remaining tokens to USDC (catches WETH, wstETH, WELL even without positions)
        await self._sweep_token_balances(
            target_token_id=USDC_TOKEN_ID,
            exclude={ETH_TOKEN_ID},  # Keep gas token
        )

        # Step 2: Transfer any USDC to main wallet
        usdc_balance = await self._get_balance_raw(
            token_id=USDC_TOKEN_ID, wallet_address=self._get_strategy_wallet_address()
        )

        if usdc_balance <= 0:
            return (False, "No USDC to withdraw.")

        token_info = await self._get_token_info(USDC_TOKEN_ID)
        decimals = token_info.get("decimals", 6)
        usdc_amount = usdc_balance / 10**decimals

        (
            success,
            msg,
        ) = await self.balance_adapter.move_from_strategy_wallet_to_main_wallet(
            USDC_TOKEN_ID, usdc_amount
        )
        if not success:
            return (False, f"USDC transfer failed: {msg}")

        # Step 3: Transfer remaining gas to main wallet (keep reserve for tx fee)
        gas_transferred = 0.0
        gas_balance = await self._get_balance_raw(
            token_id=ETH_TOKEN_ID, wallet_address=self._get_strategy_wallet_address()
        )
        tx_fee_reserve = int(0.0002 * 10**18)  # Reserve 0.0002 ETH for tx fee
        transferable_gas = gas_balance - tx_fee_reserve
        if transferable_gas > 0:
            gas_amount = transferable_gas / 10**18
            (
                gas_success,
                gas_msg,
            ) = await self.balance_adapter.move_from_strategy_wallet_to_main_wallet(
                ETH_TOKEN_ID, gas_amount
            )
            if gas_success:
                gas_transferred = gas_amount
            else:
                logger.warning(f"Gas transfer failed (non-critical): {gas_msg}")

        return (
            True,
            f"Withdrew {usdc_amount:.2f} USDC and {gas_transferred:.6f} ETH to main wallet",
        )

    async def _unlend_remaining_positions(self) -> None:
        """Unlend remaining collateral and convert to USDC."""
        # Unlend remaining wstETH
        wsteth_pos = await self.moonwell_adapter.get_pos(mtoken=M_WSTETH)
        if wsteth_pos[0]:
            mtoken_bal = wsteth_pos[1].get("mtoken_balance", 0)
            if mtoken_bal > 0:
                await self.moonwell_adapter.unlend(mtoken=M_WSTETH, amount=mtoken_bal)
                # Swap to USDC with retries
                wsteth_bal = await self._get_balance_raw(
                    token_id=WSTETH_TOKEN_ID,
                    wallet_address=self._get_strategy_wallet_address(),
                )
                if wsteth_bal > 0:
                    swap_result = await self._swap_with_retries(
                        from_token_id=WSTETH_TOKEN_ID,
                        to_token_id=USDC_TOKEN_ID,
                        amount=wsteth_bal,
                    )
                    if swap_result is None:
                        logger.warning("Failed to swap wstETH to USDC after retries")

        # Unlend remaining USDC
        usdc_pos = await self.moonwell_adapter.get_pos(mtoken=M_USDC)
        if usdc_pos[0]:
            mtoken_bal = usdc_pos[1].get("mtoken_balance", 0)
            if mtoken_bal > 0:
                await self.moonwell_adapter.unlend(mtoken=M_USDC, amount=mtoken_bal)

        # Claim any remaining rewards
        await self.moonwell_adapter.claim_rewards(min_rewards_usd=0)

        # Sweep any remaining tokens to USDC
        await self._sweep_token_balances(
            target_token_id=USDC_TOKEN_ID,
            exclude={ETH_TOKEN_ID},  # Keep gas token
        )

    async def get_peg_diff(self) -> float | dict:
        """Get stETH/ETH peg difference."""
        steth_price = await self._get_token_price(STETH_TOKEN_ID)
        weth_price = await self._get_token_price(WETH_TOKEN_ID)

        if not steth_price or not weth_price or weth_price <= 0:
            return {
                "ok": False,
                "error": f"Bad price data stETH={steth_price}, WETH={weth_price}",
            }

        peg_ratio = steth_price / weth_price
        peg_diff = abs(peg_ratio - 1)

        return peg_diff

    async def _status(self) -> StatusDict:
        """Report strategy status."""
        self._clear_price_cache()

        # Fetch positions and collateral factors in parallel
        (_totals_token, totals_usd), collateral_factors = await asyncio.gather(
            self._aggregate_positions(),
            self._get_collateral_factors(),
        )

        # Calculate LTV and health factor using pre-fetched data
        ltv = await self.compute_ltv(totals_usd, collateral_factors=collateral_factors)
        hf = (1 / ltv) if ltv and ltv > 0 and not (ltv != ltv) else None

        # Get gas balance
        gas_balance = await self._get_gas_balance()

        # Get borrowable amount
        borrowable_result = await self.moonwell_adapter.get_borrowable_amount()
        borrowable_amt_raw = borrowable_result[1] if borrowable_result[0] else 0
        borrowable_amt = self._normalize_usd_value(borrowable_amt_raw)

        # Calculate credit remaining
        weth_key = f"Base_{WETH}"
        total_borrowed = abs(totals_usd.get(weth_key, 0))
        credit_remaining = 1.0
        if (borrowable_amt + total_borrowed) > 0:
            credit_remaining = round(
                borrowable_amt / (borrowable_amt + total_borrowed), 4
            )

        # Get peg diff
        peg_diff = await self.get_peg_diff()

        # Calculate portfolio value
        portfolio_value = sum(
            v for k, v in totals_usd.items() if k != f"Base_{WETH}"
        ) + totals_usd.get(f"Base_{WETH}", 0)

        # Get projected earnings
        quote = await self.quote()

        strategy_status = {
            "current_positions_usd_value": totals_usd,
            "credit_remaining": f"{credit_remaining * 100:.2f}%",
            "LTV": ltv,
            "health_factor": hf,
            "projected_earnings": quote.get("data", {}),
            "steth_eth_peg_difference": peg_diff,
        }

        return StatusDict(
            portfolio_value=portfolio_value,
            net_deposit=0.0,  # Would need ledger integration
            strategy_status=strategy_status,
            gas_available=gas_balance / 10**18,
            gassed_up=gas_balance >= int(self.MAINTENANCE_GAS * 10**18),
        )

    @staticmethod
    async def policies() -> list[str]:
        """Return policy strings used to scope on-chain permissions."""
        return [
            # Moonwell operations
            await musdc_mint_or_approve_or_redeem(),
            await mweth_approve_or_borrow_or_repay(),
            await mwsteth_approve_or_mint_or_redeem(),
            await moonwell_comptroller_enter_markets_or_claim_rewards(),
            await weth_deposit(),
            # Swaps
            erc20_spender_for_any_token(ENSO_ROUTER),
            await enso_swap(),
        ]
