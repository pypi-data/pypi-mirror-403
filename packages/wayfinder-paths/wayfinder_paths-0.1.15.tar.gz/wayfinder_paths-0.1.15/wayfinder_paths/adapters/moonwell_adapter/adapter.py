"""
Moonwell Adapter for lending, borrowing, and collateral management on Moonwell protocol.

This adapter provides functionality for interacting with Moonwell on Base chain,
including supplying/withdrawing collateral, borrowing/repaying, and claiming rewards.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Literal

from eth_utils import to_checksum_address

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.clients.TokenClient import TokenClient
from wayfinder_paths.core.constants.base import DEFAULT_TRANSACTION_TIMEOUT
from wayfinder_paths.core.constants.erc20_abi import ERC20_ABI
from wayfinder_paths.core.constants.moonwell_abi import (
    COMPTROLLER_ABI,
    MTOKEN_ABI,
    REWARD_DISTRIBUTOR_ABI,
    WETH_ABI,
)
from wayfinder_paths.core.services.base import Web3Service

# Moonwell Base chain addresses
MOONWELL_DEFAULTS = {
    # mToken addresses
    "m_usdc": "0xEdc817A28E8B93B03976FBd4a3dDBc9f7D176c22",
    "m_weth": "0x628ff693426583D9a7FB391E54366292F509D457",
    "m_wsteth": "0x627Fe393Bc6EdDA28e99AE648fD6fF362514304b",
    # Underlying token addresses
    "usdc": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "weth": "0x4200000000000000000000000000000000000006",
    "wsteth": "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452",
    # Protocol addresses
    "reward_distributor": "0xe9005b078701e2a0948d2eac43010d35870ad9d2",
    "comptroller": "0xfbb21d0380bee3312b33c4353c8936a0f13ef26c",
    # WELL token address on Base
    "well_token": "0xA88594D404727625A9437C3f886C7643872296AE",
}

# Base chain ID
BASE_CHAIN_ID = 8453

# Mantissa for collateral factor calculations (1e18)
MANTISSA = 10**18

# Seconds per year for APY calculations
SECONDS_PER_YEAR = 365 * 24 * 60 * 60

# Collateral factor cache TTL (1 hour - rarely changes, governance controlled)
CF_CACHE_TTL = 3600

# Default retry settings for rate-limited RPCs
DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY = 3.0  # seconds

# Compound-style Failure(uint256,uint256,uint256) topic0
FAILURE_EVENT_TOPIC0 = (
    "0x45b96fe442630264581b197e84bbada861235052c5a1aadfff9ea4e40a969aa0"
)


def _is_rate_limit_error(error: Exception | str) -> bool:
    """Check if an error is a rate limit (429) error."""
    error_str = str(error)
    return "429" in error_str or "Too Many Requests" in error_str


async def _retry_with_backoff(
    coro_factory,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
):
    """Retry an async operation with exponential backoff on rate limit errors.

    Args:
        coro_factory: A callable that returns a new coroutine each time.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds (doubles each retry).

    Returns:
        The result of the coroutine if successful.

    Raises:
        The last exception if all retries fail.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except Exception as exc:
            last_error = exc
            if _is_rate_limit_error(exc) and attempt < max_retries - 1:
                wait_time = base_delay * (2**attempt)
                await asyncio.sleep(wait_time)
                continue
            raise
    raise last_error


def _timestamp_rate_to_apy(rate: float) -> float:
    """Convert a per-second rate to APY."""
    return (1 + rate) ** SECONDS_PER_YEAR - 1


class MoonwellAdapter(BaseAdapter):
    """Moonwell adapter for lending/borrowing operations on Base chain."""

    adapter_type = "MOONWELL"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        web3_service: Web3Service | None = None,
        token_client: TokenClient | None = None,
        simulation: bool = False,
    ) -> None:
        super().__init__("moonwell_adapter", config)
        cfg = config or {}
        adapter_cfg = cfg.get("moonwell_adapter") or {}

        self.web3 = web3_service
        self.simulation = simulation
        self.token_client = token_client
        self.token_txn_service = (
            web3_service.token_transactions if web3_service else None
        )

        self.strategy_wallet = cfg.get("strategy_wallet") or {}
        self.chain_id = adapter_cfg.get("chain_id", BASE_CHAIN_ID)
        self.chain_name = "base"

        # Protocol addresses (with config overrides)
        self.comptroller_address = self._checksum(
            adapter_cfg.get("comptroller") or MOONWELL_DEFAULTS["comptroller"]
        )
        self.reward_distributor_address = self._checksum(
            adapter_cfg.get("reward_distributor")
            or MOONWELL_DEFAULTS["reward_distributor"]
        )
        self.well_token = self._checksum(
            adapter_cfg.get("well_token") or MOONWELL_DEFAULTS["well_token"]
        )

        # Token addresses
        self.m_usdc = self._checksum(
            adapter_cfg.get("m_usdc") or MOONWELL_DEFAULTS["m_usdc"]
        )
        self.m_weth = self._checksum(
            adapter_cfg.get("m_weth") or MOONWELL_DEFAULTS["m_weth"]
        )
        self.m_wsteth = self._checksum(
            adapter_cfg.get("m_wsteth") or MOONWELL_DEFAULTS["m_wsteth"]
        )
        self.usdc = self._checksum(adapter_cfg.get("usdc") or MOONWELL_DEFAULTS["usdc"])
        self.weth = self._checksum(adapter_cfg.get("weth") or MOONWELL_DEFAULTS["weth"])
        self.wsteth = self._checksum(
            adapter_cfg.get("wsteth") or MOONWELL_DEFAULTS["wsteth"]
        )

        # Collateral factor cache: mtoken -> (value, timestamp)
        self._cf_cache: dict[str, tuple[float, float]] = {}

    # ------------------------------------------------------------------ #
    # Public API - Lending Operations                                     #
    # ------------------------------------------------------------------ #

    def _tx_pinned_block(self, result: Any) -> int | None:
        if isinstance(result, dict):
            return (
                result.get("confirmed_block_number")
                or result.get("block_number")
                or (result.get("receipt", {}) or {}).get("blockNumber")
            )
        return None

    def _as_bytes(self, value: Any) -> bytes | None:
        if value is None:
            return None
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)
        if hasattr(value, "hex"):
            try:
                hex_str = value.hex()
                if isinstance(hex_str, str):
                    if hex_str.startswith("0x"):
                        return bytes.fromhex(hex_str[2:])
                    return bytes.fromhex(hex_str)
            except Exception:
                return None
        if isinstance(value, str):
            v = value
            if v.startswith("0x"):
                v = v[2:]
            try:
                return bytes.fromhex(v)
            except Exception:
                return None
        return None

    def _failure_event_details(
        self, result: Any, contract_address: str
    ) -> dict[str, int] | None:
        if not isinstance(result, dict):
            return None

        receipt = (
            result.get("receipt") if isinstance(result.get("receipt"), dict) else {}
        )
        logs = receipt.get("logs") if isinstance(receipt, dict) else None
        if not isinstance(logs, list):
            return None

        addr_l = str(contract_address or "").lower()
        for log in logs:
            if not isinstance(log, dict):
                continue
            if str(log.get("address") or "").lower() != addr_l:
                continue
            topics = log.get("topics") or []
            if not topics:
                continue
            topic0_bytes = self._as_bytes(topics[0])
            if not topic0_bytes:
                continue
            if topic0_bytes.hex() != FAILURE_EVENT_TOPIC0.lower().removeprefix("0x"):
                continue

            data_b = self._as_bytes(log.get("data"))
            if not data_b or len(data_b) < 96:
                return {"error": 0, "info": 0, "detail": 0}

            return {
                "error": int.from_bytes(data_b[0:32], "big"),
                "info": int.from_bytes(data_b[32:64], "big"),
                "detail": int.from_bytes(data_b[64:96], "big"),
            }

        return None

    async def lend(
        self,
        *,
        mtoken: str,
        underlying_token: str,
        amount: int,
    ) -> tuple[bool, Any]:
        """Supply tokens to Moonwell by minting mTokens.

        Note: mint() returns an error code and can emit Failure without reverting.
        We verify success by checking that the mToken balance increased.
        """
        strategy = self._strategy_address()
        amount = int(amount)
        if amount <= 0:
            return False, "amount must be positive"

        mtoken = self._checksum(mtoken)
        underlying_token = self._checksum(underlying_token)

        mtoken_bal_before = None
        if self.web3 and not self.simulation:
            try:
                web3 = self.web3.get_web3(self.chain_id)
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
                mtoken_bal_before = await mtoken_contract.functions.balanceOf(
                    strategy
                ).call()
            except Exception:
                mtoken_bal_before = None

        # Approve mToken to spend underlying tokens
        approved = await self._ensure_allowance(
            token_address=underlying_token,
            owner=strategy,
            spender=mtoken,
            amount=amount,
        )
        if not approved[0]:
            return approved

        # Mint mTokens (supply underlying)
        tx = await self._encode_call(
            target=mtoken,
            abi=MTOKEN_ABI,
            fn_name="mint",
            args=[amount],
            from_address=strategy,
        )
        result = await self._execute(tx)

        if not result[0] or not self.web3 or self.simulation:
            return result

        if isinstance(result[1], dict):
            failure = self._failure_event_details(result[1], mtoken)
            if failure is not None:
                return (
                    False,
                    f"Mint failed (Failure event): error={failure['error']} info={failure['info']} detail={failure['detail']}",
                )

        if mtoken_bal_before is None:
            return result

        try:
            pinned_block = self._tx_pinned_block(result[1])
            block_id = pinned_block if pinned_block is not None else "latest"

            web3 = self.web3.get_web3(self.chain_id)
            mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
            mtoken_bal_after = await mtoken_contract.functions.balanceOf(strategy).call(
                block_identifier=block_id
            )
            if int(mtoken_bal_after) <= int(mtoken_bal_before):
                return (
                    False,
                    f"Mint verification failed: mToken balance did not increase (before={mtoken_bal_before}, after={mtoken_bal_after})",
                )
        except Exception:
            # If verification fails due to RPC/ABI issues, keep original result.
            return result

        return result

    async def unlend(
        self,
        *,
        mtoken: str,
        amount: int,
    ) -> tuple[bool, Any]:
        """Withdraw tokens from Moonwell by redeeming mTokens.

        Note: redeem() returns an error code and can emit Failure without reverting.
        We verify success by checking that either:
          - underlying wallet balance increased, or
          - mToken wallet balance decreased.
        """
        strategy = self._strategy_address()
        amount = int(amount)
        if amount <= 0:
            return False, "amount must be positive"

        mtoken = self._checksum(mtoken)

        mtoken_bal_before = None
        underlying_addr = None
        underlying_bal_before = None

        if self.web3 and not self.simulation:
            try:
                web3 = self.web3.get_web3(self.chain_id)
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)

                # Snapshot balances for verification.
                mtoken_bal_before = await mtoken_contract.functions.balanceOf(
                    strategy
                ).call()
                try:
                    underlying_addr = (
                        await mtoken_contract.functions.underlying().call()
                    )
                except Exception:
                    underlying_addr = None
                if underlying_addr:
                    underlying_contract = web3.eth.contract(
                        address=to_checksum_address(underlying_addr),
                        abi=ERC20_ABI,
                    )
                    underlying_bal_before = (
                        await underlying_contract.functions.balanceOf(strategy).call()
                    )
            except Exception:
                mtoken_bal_before = None
                underlying_addr = None
                underlying_bal_before = None

        # Redeem mTokens for underlying
        tx = await self._encode_call(
            target=mtoken,
            abi=MTOKEN_ABI,
            fn_name="redeem",
            args=[amount],
            from_address=strategy,
        )
        result = await self._execute(tx)

        if not result[0] or not self.web3 or self.simulation:
            return result

        if isinstance(result[1], dict):
            failure = self._failure_event_details(result[1], mtoken)
            if failure is not None:
                return (
                    False,
                    f"Redeem failed (Failure event): error={failure['error']} info={failure['info']} detail={failure['detail']}",
                )

        if mtoken_bal_before is None:
            return result

        try:
            pinned_block = self._tx_pinned_block(result[1])
            block_id = pinned_block if pinned_block is not None else "latest"

            web3 = self.web3.get_web3(self.chain_id)
            mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
            mtoken_bal_after = await mtoken_contract.functions.balanceOf(strategy).call(
                block_identifier=block_id
            )

            underlying_bal_after = None
            if underlying_addr:
                underlying_contract = web3.eth.contract(
                    address=to_checksum_address(underlying_addr),
                    abi=ERC20_ABI,
                )
                underlying_bal_after = await underlying_contract.functions.balanceOf(
                    strategy
                ).call(block_identifier=block_id)

            mtoken_decreased = int(mtoken_bal_after) < int(mtoken_bal_before)
            underlying_increased = (
                underlying_bal_before is not None
                and underlying_bal_after is not None
                and int(underlying_bal_after) > int(underlying_bal_before)
            )

            if not mtoken_decreased and not underlying_increased:
                return (
                    False,
                    "Redeem verification failed: no observed balance change "
                    f"(mtoken before={mtoken_bal_before}, after={mtoken_bal_after}; "
                    f"underlying before={underlying_bal_before}, after={underlying_bal_after})",
                )
        except Exception:
            return result

        return result

    # ------------------------------------------------------------------ #
    # Public API - Borrowing Operations                                   #
    # ------------------------------------------------------------------ #

    async def borrow(
        self,
        *,
        mtoken: str,
        amount: int,
    ) -> tuple[bool, Any]:
        """Borrow tokens from Moonwell.

        Note: Moonwell/Compound borrow() returns an error code, not a boolean.
        Even if the transaction succeeds (status=1), the borrow may have failed
        if the return value is non-zero. We verify success by checking that
        the borrow balance actually increased.
        """
        from loguru import logger

        strategy = self._strategy_address()
        amount = int(amount)
        if amount <= 0:
            return False, "amount must be positive"

        mtoken = self._checksum(mtoken)

        # Get borrow balance before the transaction for verification
        borrow_before = 0
        if self.web3:
            try:
                web3 = self.web3.get_web3(self.chain_id)
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)

                borrow_before = await mtoken_contract.functions.borrowBalanceStored(
                    strategy
                ).call()

                # Simulate borrow to check for errors before submitting
                try:
                    borrow_return = await mtoken_contract.functions.borrow(amount).call(
                        {"from": strategy}
                    )
                    if borrow_return != 0:
                        logger.warning(
                            f"Borrow simulation returned error code {borrow_return}. "
                            "Codes: 3=COMPTROLLER_REJECTION, 9=INVALID_ACCOUNT_PAIR, "
                            "14=INSUFFICIENT_LIQUIDITY"
                        )
                except Exception as call_err:
                    logger.debug(f"Borrow simulation failed: {call_err}")

            except Exception as e:
                logger.warning(f"Failed to get pre-borrow balance: {e}")

        tx = await self._encode_call(
            target=mtoken,
            abi=MTOKEN_ABI,
            fn_name="borrow",
            args=[amount],
            from_address=strategy,
        )
        result = await self._execute(tx)

        if not result[0]:
            return result

        # Verify the borrow actually succeeded by checking balance increased
        if self.web3:
            try:
                pinned_block = None
                if isinstance(result[1], dict):
                    pinned_block = (
                        result[1].get("confirmed_block_number")
                        or result[1].get("block_number")
                        or (result[1].get("receipt", {}) or {}).get("blockNumber")
                    )
                block_id = pinned_block if pinned_block is not None else "latest"

                web3 = self.web3.get_web3(self.chain_id)
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
                borrow_after = await mtoken_contract.functions.borrowBalanceStored(
                    strategy
                ).call(block_identifier=block_id)

                # Borrow balance should have increased by approximately the amount
                # Allow for some interest accrual
                expected_increase = amount * 0.99  # Allow 1% tolerance for interest
                actual_increase = borrow_after - borrow_before

                if actual_increase < expected_increase:
                    from loguru import logger

                    logger.error(
                        f"Borrow verification failed: balance only increased by "
                        f"{actual_increase} (expected ~{amount}). "
                        f"Moonwell likely returned an error code. "
                        f"Before: {borrow_before}, After: {borrow_after}"
                    )
                    return (
                        False,
                        f"Borrow failed: balance did not increase as expected. "
                        f"Before: {borrow_before}, After: {borrow_after}, Expected: +{amount}",
                    )
            except Exception as e:
                from loguru import logger

                logger.warning(f"Could not verify borrow balance: {e}")
                # Continue with the original result if verification fails

        return result

    async def repay(
        self,
        *,
        mtoken: str,
        underlying_token: str,
        amount: int,
        repay_full: bool = False,
    ) -> tuple[bool, Any]:
        """Repay borrowed tokens to Moonwell.

        Args:
            mtoken: The mToken address
            underlying_token: The underlying token address (e.g., WETH)
            amount: Amount to repay (used for approval if repay_full=True)
            repay_full: If True, uses type(uint256).max to repay exact debt
        """
        strategy = self._strategy_address()
        amount = int(amount)
        if amount <= 0:
            return False, "amount must be positive"

        mtoken = self._checksum(mtoken)
        underlying_token = self._checksum(underlying_token)

        borrow_before = None
        if self.web3 and not self.simulation:
            try:
                web3 = self.web3.get_web3(self.chain_id)
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
                borrow_before = await mtoken_contract.functions.borrowBalanceStored(
                    strategy
                ).call()
            except Exception:
                borrow_before = None

        # Approve mToken to spend underlying tokens for repayment
        # When repay_full=True, approve the amount we have, Moonwell will use only what's needed
        approved = await self._ensure_allowance(
            token_address=underlying_token,
            owner=strategy,
            spender=mtoken,
            amount=amount,
        )
        if not approved[0]:
            return approved

        # Use max uint256 for full repayment to avoid balance calculation issues
        repay_amount = self.MAX_UINT256 if repay_full else amount

        tx = await self._encode_call(
            target=mtoken,
            abi=MTOKEN_ABI,
            fn_name="repayBorrow",
            args=[repay_amount],
            from_address=strategy,
        )
        result = await self._execute(tx)

        if not result[0] or not self.web3 or self.simulation:
            return result

        if isinstance(result[1], dict):
            failure = self._failure_event_details(result[1], mtoken)
            if failure is not None:
                return (
                    False,
                    f"Repay failed (Failure event): error={failure['error']} info={failure['info']} detail={failure['detail']}",
                )

        if borrow_before is None or int(borrow_before) <= 0:
            return result

        try:
            pinned_block = self._tx_pinned_block(result[1])
            block_id = pinned_block if pinned_block is not None else "latest"

            web3 = self.web3.get_web3(self.chain_id)
            mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
            borrow_after = await mtoken_contract.functions.borrowBalanceStored(
                strategy
            ).call(block_identifier=block_id)

            if repay_full:
                # Full repayment should clear the borrow balance (allow 1 wei dust).
                if int(borrow_after) > 1:
                    return (
                        False,
                        f"Repay verification failed: repay_full did not clear debt (before={borrow_before}, after={borrow_after})",
                    )
            else:
                if int(borrow_after) >= int(borrow_before):
                    return (
                        False,
                        f"Repay verification failed: borrow balance did not decrease (before={borrow_before}, after={borrow_after})",
                    )
        except Exception:
            return result

        return result

    # ------------------------------------------------------------------ #
    # Public API - Collateral Management                                  #
    # ------------------------------------------------------------------ #

    async def set_collateral(
        self,
        *,
        mtoken: str,
    ) -> tuple[bool, Any]:
        """Enable a market as collateral (enter market).

        Note: enterMarkets returns an array of error codes. We verify success
        by checking if the account has actually entered the market.
        """
        strategy = self._strategy_address()
        mtoken = self._checksum(mtoken)

        tx = await self._encode_call(
            target=self.comptroller_address,
            abi=COMPTROLLER_ABI,
            fn_name="enterMarkets",
            args=[[mtoken]],
            from_address=strategy,
        )
        result = await self._execute(tx)

        if not result[0]:
            return result

        # Verify the market was actually entered
        if self.web3:
            try:
                pinned_block = None
                if isinstance(result[1], dict):
                    pinned_block = (
                        result[1].get("confirmed_block_number")
                        or result[1].get("block_number")
                        or (result[1].get("receipt", {}) or {}).get("blockNumber")
                    )
                block_id = pinned_block if pinned_block is not None else "latest"

                web3 = self.web3.get_web3(self.chain_id)
                comptroller = web3.eth.contract(
                    address=self.comptroller_address, abi=COMPTROLLER_ABI
                )
                is_member = await comptroller.functions.checkMembership(
                    strategy, mtoken
                ).call(block_identifier=block_id)

                if not is_member:
                    from loguru import logger

                    logger.error(
                        f"set_collateral verification failed: account {strategy} "
                        f"is not a member of market {mtoken} after enterMarkets call"
                    )
                    return (
                        False,
                        f"enterMarkets succeeded but account is not a member of market {mtoken}",
                    )
            except Exception as e:
                from loguru import logger

                logger.warning(f"Could not verify market membership: {e}")

        return result

    async def is_market_entered(
        self,
        *,
        mtoken: str,
        account: str | None = None,
    ) -> tuple[bool, bool | str]:
        """Check whether an account has entered a given market (as collateral / borrowing market)."""
        if self.simulation:
            return True, True
        if not self.web3:
            return False, "web3 service not configured"

        try:
            acct = self._checksum(account) if account else self._strategy_address()
            mtoken = self._checksum(mtoken)

            web3 = self.web3.get_web3(self.chain_id)
            comptroller = web3.eth.contract(
                address=self.comptroller_address, abi=COMPTROLLER_ABI
            )
            is_member = await comptroller.functions.checkMembership(acct, mtoken).call()
            return True, bool(is_member)
        except Exception as exc:
            return False, str(exc)

    async def remove_collateral(
        self,
        *,
        mtoken: str,
    ) -> tuple[bool, Any]:
        """Disable a market as collateral (exit market)."""
        strategy = self._strategy_address()
        mtoken = self._checksum(mtoken)

        tx = await self._encode_call(
            target=self.comptroller_address,
            abi=COMPTROLLER_ABI,
            fn_name="exitMarket",
            args=[mtoken],
            from_address=strategy,
        )
        return await self._execute(tx)

    # ------------------------------------------------------------------ #
    # Public API - Rewards                                                #
    # ------------------------------------------------------------------ #

    async def claim_rewards(
        self,
        *,
        min_rewards_usd: float = 0.0,
    ) -> tuple[bool, dict[str, int] | str]:
        """Claim WELL rewards from Moonwell. Skips if below min_rewards_usd threshold."""
        strategy = self._strategy_address()

        # Get outstanding rewards first
        rewards = await self._get_outstanding_rewards(strategy)

        # Skip if no rewards to claim
        if not rewards:
            return True, {}

        # Check minimum threshold if token_client available
        if min_rewards_usd > 0 and self.token_client:
            total_usd = await self._calculate_rewards_usd(rewards)
            if total_usd < min_rewards_usd:
                return True, {}  # Skip claiming, below threshold

        # Claim via comptroller (like reference implementation)
        tx = await self._encode_call(
            target=self.comptroller_address,
            abi=COMPTROLLER_ABI,
            fn_name="claimReward",
            args=[strategy],
            from_address=strategy,
        )
        result = await self._execute(tx)
        if not result[0]:
            return result

        return True, rewards

    async def _get_outstanding_rewards(self, account: str) -> dict[str, int]:
        """Get outstanding rewards for an account across all markets."""
        if not self.web3:
            return {}

        try:
            web3 = self.web3.get_web3(self.chain_id)
            contract = web3.eth.contract(
                address=self.reward_distributor_address, abi=REWARD_DISTRIBUTOR_ABI
            )

            # Call getOutstandingRewardsForUser(user)
            all_rewards = await contract.functions.getOutstandingRewardsForUser(
                account
            ).call()

            rewards: dict[str, int] = {}
            for mtoken_data in all_rewards:
                # mtoken_data is (mToken, [(rewardToken, totalReward, supplySide, borrowSide)])
                if len(mtoken_data) >= 2:
                    token_rewards = mtoken_data[1] if len(mtoken_data) > 1 else []
                    for reward_info in token_rewards:
                        if len(reward_info) >= 2:
                            token_addr = reward_info[0]
                            total_reward = reward_info[1]
                            if total_reward > 0:
                                key = f"{self.chain_name}_{token_addr}"
                                rewards[key] = rewards.get(key, 0) + total_reward
            return rewards
        except Exception:
            return {}

    async def _calculate_rewards_usd(self, rewards: dict[str, int]) -> float:
        """Calculate total USD value of rewards."""
        if not self.token_client:
            return 0.0

        total_usd = 0.0
        for token_key, amount in rewards.items():
            try:
                token_data = await self.token_client.get_token_details(token_key)
                if token_data:
                    price = token_data.get("price_usd") or token_data.get("price", 0)
                    decimals = token_data.get("decimals", 18)
                    total_usd += (amount / (10**decimals)) * price
            except Exception:
                pass
        return total_usd

    # ------------------------------------------------------------------ #
    # Public API - Position & Market Data                                 #
    # ------------------------------------------------------------------ #

    async def get_pos(
        self,
        *,
        mtoken: str,
        account: str | None = None,
        include_usd: bool = False,
        max_retries: int = 3,
        block_identifier: int | str | None = None,
    ) -> tuple[bool, dict[str, Any] | str]:
        """Get position data (balances, rewards) for an account in a market.

        Args:
            mtoken: The mToken address
            account: Account to query (defaults to strategy wallet)
            include_usd: Whether to include USD values
            max_retries: Number of retry attempts
            block_identifier: Block to query at. Can be:
                - int: specific block number (for pinning to tx block)
                - "safe": OP Stack safe block (data posted to L1)
                - None/"latest": current head (default)

        Includes retry logic with exponential backoff for rate-limited RPCs.
        """
        if not self.web3:
            return False, "web3 service not configured"

        mtoken = self._checksum(mtoken)
        account = self._checksum(account) if account else self._strategy_address()
        block_id = block_identifier if block_identifier is not None else "latest"

        bal = exch = borrow = underlying = rewards = None
        last_error = ""

        for attempt in range(max_retries):
            try:
                web3 = self.web3.get_web3(self.chain_id)
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
                rewards_contract = web3.eth.contract(
                    address=self.reward_distributor_address, abi=REWARD_DISTRIBUTOR_ABI
                )

                # Fetch data sequentially to avoid overwhelming rate-limited public RPCs
                # (parallel fetch would make 5 simultaneous calls per position)
                bal = await mtoken_contract.functions.balanceOf(account).call(
                    block_identifier=block_id
                )
                exch = await mtoken_contract.functions.exchangeRateStored().call(
                    block_identifier=block_id
                )
                borrow = await mtoken_contract.functions.borrowBalanceStored(
                    account
                ).call(block_identifier=block_id)
                underlying = await mtoken_contract.functions.underlying().call(
                    block_identifier=block_id
                )
                rewards = await rewards_contract.functions.getOutstandingRewardsForUser(
                    mtoken, account
                ).call(block_identifier=block_id)
                break  # Success, exit retry loop
            except Exception as exc:
                last_error = str(exc)
                if "429" in last_error or "Too Many Requests" in last_error:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** (attempt + 1)  # 2, 4, 8 seconds
                        await asyncio.sleep(wait_time)
                        continue
                return False, last_error
        else:
            # All retries exhausted
            return False, last_error

        try:
            # Process rewards
            reward_balances = self._process_rewards(rewards)

            # Build balances dict
            mtoken_key = f"{self.chain_name}_{mtoken}"
            underlying_key = f"{self.chain_name}_{underlying}"

            balances: dict[str, int] = {mtoken_key: bal}
            balances.update(reward_balances)

            if borrow > 0:
                balances[underlying_key] = -borrow

            result: dict[str, Any] = {
                "balances": balances,
                "mtoken_balance": bal,
                "underlying_balance": (bal * exch) // MANTISSA,
                "borrow_balance": borrow,
                "exchange_rate": exch,
                "underlying_token": underlying,
            }

            # Calculate USD values if requested and token_client available
            if include_usd and self.token_client:
                usd_balances = await self._calculate_usd_balances(
                    balances, underlying_key, exch
                )
                result["usd_balances"] = usd_balances

            return True, result
        except Exception as exc:
            return False, str(exc)

    def _process_rewards(self, rewards: list) -> dict[str, int]:
        """Process rewards tuple into dict mapping token keys to amounts."""
        result: dict[str, int] = {}
        for reward_info in rewards:
            if len(reward_info) >= 2:
                token_addr = reward_info[0]
                total_reward = reward_info[1]
                if total_reward > 0:
                    key = f"{self.chain_name}_{token_addr}"
                    result[key] = total_reward
        return result

    async def _calculate_usd_balances(
        self, balances: dict[str, int], underlying_key: str, _exchange_rate: int
    ) -> dict[str, float | None]:
        """Calculate USD values for balances."""
        if not self.token_client:
            return {}

        # Fetch token data for all tokens
        tokens = set(balances.keys()) | {underlying_key}
        token_data: dict[str, dict | None] = {}
        for token_key in tokens:
            try:
                token_data[token_key] = await self.token_client.get_token_details(
                    token_key
                )
            except Exception:
                token_data[token_key] = None

        # Calculate USD values
        usd_balances: dict[str, float | None] = {}
        for token_key, bal in balances.items():
            data = token_data.get(token_key)
            if data:
                price = data.get("price_usd") or data.get("price")
                if price is not None:
                    decimals = data.get("decimals", 18)
                    usd_balances[token_key] = (bal / (10**decimals)) * price
                else:
                    usd_balances[token_key] = None
            else:
                usd_balances[token_key] = None

        return usd_balances

    async def get_collateral_factor(
        self,
        *,
        mtoken: str,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> tuple[bool, float | str]:
        """Get the collateral factor for a market as decimal (e.g., 0.75 for 75%).

        Uses a 1-hour cache since collateral factors rarely change (governance controlled).
        Includes retry logic with exponential backoff for rate-limited RPCs.
        """
        if not self.web3:
            return False, "web3 service not configured"

        mtoken = self._checksum(mtoken)

        # Check cache first
        now = time.time()
        if mtoken in self._cf_cache:
            cached_value, cached_time = self._cf_cache[mtoken]
            if now - cached_time < CF_CACHE_TTL:
                return True, cached_value

        last_error = ""
        for attempt in range(max_retries):
            try:
                web3 = self.web3.get_web3(self.chain_id)
                contract = web3.eth.contract(
                    address=self.comptroller_address, abi=COMPTROLLER_ABI
                )

                # markets() returns (isListed, collateralFactorMantissa)
                result = await contract.functions.markets(mtoken).call()
                is_listed, collateral_factor_mantissa = result

                if not is_listed:
                    return False, f"Market {mtoken} is not listed"

                # Convert from mantissa to decimal
                collateral_factor = collateral_factor_mantissa / MANTISSA

                # Cache the result
                self._cf_cache[mtoken] = (collateral_factor, now)

                return True, collateral_factor
            except Exception as exc:
                last_error = str(exc)
                if _is_rate_limit_error(exc) and attempt < max_retries - 1:
                    wait_time = DEFAULT_BASE_DELAY * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue
                return False, last_error

        return False, last_error

    async def get_apy(
        self,
        *,
        mtoken: str,
        apy_type: Literal["supply", "borrow"] = "supply",
        include_rewards: bool = True,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> tuple[bool, float | str]:
        """Get supply or borrow APY for a market, optionally including WELL rewards.

        Includes retry logic with exponential backoff for rate-limited RPCs.
        """
        if not self.web3:
            return False, "web3 service not configured"

        mtoken = self._checksum(mtoken)

        last_error = ""
        for attempt in range(max_retries):
            try:
                web3 = self.web3.get_web3(self.chain_id)
                mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
                reward_distributor = web3.eth.contract(
                    address=self.reward_distributor_address, abi=REWARD_DISTRIBUTOR_ABI
                )

                # Get base rate (sequential to avoid rate limits)
                if apy_type == "supply":
                    rate_per_timestamp = (
                        await mtoken_contract.functions.supplyRatePerTimestamp().call()
                    )
                    mkt_config = await reward_distributor.functions.getAllMarketConfigs(
                        mtoken
                    ).call()
                    total_value = await mtoken_contract.functions.totalSupply().call()
                else:
                    rate_per_timestamp = (
                        await mtoken_contract.functions.borrowRatePerTimestamp().call()
                    )
                    mkt_config = await reward_distributor.functions.getAllMarketConfigs(
                        mtoken
                    ).call()
                    total_value = await mtoken_contract.functions.totalBorrows().call()

                # Convert rate per second to APY
                rate = rate_per_timestamp / MANTISSA
                apy = _timestamp_rate_to_apy(rate)

                # Add WELL rewards APY if requested and token_client available
                if include_rewards and self.token_client and total_value > 0:
                    rewards_apr = await self._calculate_rewards_apr(
                        mtoken, mkt_config, total_value, apy_type
                    )
                    apy += rewards_apr

                return True, apy
            except Exception as exc:
                last_error = str(exc)
                if _is_rate_limit_error(exc) and attempt < max_retries - 1:
                    wait_time = DEFAULT_BASE_DELAY * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue
                return False, last_error

        return False, last_error

    async def _calculate_rewards_apr(
        self,
        mtoken: str,
        mkt_config: list,
        total_value: int,
        apy_type: str,
    ) -> float:
        """Calculate WELL rewards APR for a market."""
        if not self.token_client:
            return 0.0

        try:
            # Find WELL token config
            well_config = None
            for config in mkt_config:
                if len(config) >= 6 and config[1].lower() == self.well_token.lower():
                    well_config = config
                    break

            if not well_config:
                return 0.0

            # Get emission rate (supply or borrow)
            # Config format: (mToken, rewardToken, owner, emissionCap, supplyEmissionsPerSec, borrowEmissionsPerSec, ...)
            if apy_type == "supply":
                well_rate = well_config[4]  # supplyEmissionsPerSec
            else:
                well_rate = well_config[5]  # borrowEmissionsPerSec
                # Borrow rewards are shown as negative in some implementations
                if well_rate < 0:
                    well_rate = -well_rate

            if well_rate == 0:
                return 0.0

            # Get underlying token for decimals
            web3 = self.web3.get_web3(self.chain_id)
            mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)
            underlying_addr = await mtoken_contract.functions.underlying().call()

            # Get prices
            well_key = f"{self.chain_name}_{self.well_token}"
            underlying_key = f"{self.chain_name}_{underlying_addr}"

            well_data, underlying_data = await asyncio.gather(
                self.token_client.get_token_details(well_key),
                self.token_client.get_token_details(underlying_key),
            )

            well_price = (
                well_data.get("price_usd") or well_data.get("price", 0)
                if well_data
                else 0
            )
            underlying_price = (
                underlying_data.get("price_usd") or underlying_data.get("price", 0)
                if underlying_data
                else 0
            )
            underlying_decimals = (
                underlying_data.get("decimals", 18) if underlying_data else 18
            )

            if not well_price or not underlying_price:
                return 0.0

            # Calculate total value in USD
            total_value_usd = (
                total_value / (10**underlying_decimals)
            ) * underlying_price

            if total_value_usd == 0:
                return 0.0

            # Calculate rewards APR
            # rewards_apr = well_price * emissions_per_second * seconds_per_year / total_value_usd
            rewards_apr = (
                well_price * (well_rate / MANTISSA) * SECONDS_PER_YEAR / total_value_usd
            )

            return rewards_apr
        except Exception:
            return 0.0

    async def get_borrowable_amount(
        self,
        *,
        account: str | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> tuple[bool, int | str]:
        """Get the maximum borrowable amount for an account (USD with 18 decimals).

        Includes retry logic with exponential backoff for rate-limited RPCs.
        """
        if not self.web3:
            return False, "web3 service not configured"

        account = self._checksum(account) if account else self._strategy_address()

        last_error = ""
        for attempt in range(max_retries):
            try:
                web3 = self.web3.get_web3(self.chain_id)
                contract = web3.eth.contract(
                    address=self.comptroller_address, abi=COMPTROLLER_ABI
                )

                # getAccountLiquidity returns (error, liquidity, shortfall)
                (
                    error,
                    liquidity,
                    shortfall,
                ) = await contract.functions.getAccountLiquidity(account).call()

                if error != 0:
                    return False, f"Comptroller error: {error}"

                if shortfall > 0:
                    return False, f"Account has shortfall: {shortfall}"

                return True, liquidity
            except Exception as exc:
                last_error = str(exc)
                if _is_rate_limit_error(exc) and attempt < max_retries - 1:
                    wait_time = DEFAULT_BASE_DELAY * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue
                return False, last_error

        return False, last_error

    async def max_withdrawable_mtoken(
        self,
        *,
        mtoken: str,
        account: str | None = None,
    ) -> tuple[bool, dict[str, Any] | str]:
        """Calculate max mTokens withdrawable without liquidation using binary search."""
        if not self.web3:
            return False, "web3 service not configured"

        mtoken = self._checksum(mtoken)
        account = self._checksum(account) if account else self._strategy_address()

        try:
            web3 = self.web3.get_web3(self.chain_id)
            comptroller = web3.eth.contract(
                address=self.comptroller_address, abi=COMPTROLLER_ABI
            )
            mtoken_contract = web3.eth.contract(address=mtoken, abi=MTOKEN_ABI)

            # Get all needed data in parallel
            bal_raw, exch_raw, cash_raw, m_dec, u_addr = await asyncio.gather(
                mtoken_contract.functions.balanceOf(account).call(),
                mtoken_contract.functions.exchangeRateStored().call(),
                mtoken_contract.functions.getCash().call(),
                mtoken_contract.functions.decimals().call(),
                mtoken_contract.functions.underlying().call(),
            )

            if bal_raw == 0 or exch_raw == 0:
                return True, {
                    "cTokens_raw": 0,
                    "cTokens": 0.0,
                    "underlying_raw": 0,
                    "underlying": 0.0,
                    "bounds_raw": {"collateral_cTokens": 0, "cash_cTokens": 0},
                    "exchangeRate_raw": int(exch_raw),
                    "mToken_decimals": int(m_dec),
                    "underlying_decimals": None,
                }

            # Get underlying decimals
            u_dec = 18  # Default
            if self.token_client:
                try:
                    u_key = f"{self.chain_name}_{u_addr}"
                    u_data = await self.token_client.get_token_details(u_key)
                    if u_data:
                        u_dec = u_data.get("decimals", 18)
                except Exception:
                    pass

            # Binary search: largest cTokens you can redeem without shortfall
            lo, hi = 0, int(bal_raw)
            while lo < hi:
                mid = (lo + hi + 1) // 2
                (
                    err,
                    _liq,
                    short,
                ) = await comptroller.functions.getHypotheticalAccountLiquidity(
                    account, mtoken, mid, 0
                ).call()
                if err != 0:
                    return False, f"Comptroller error {err}"
                if short == 0:
                    lo = mid  # Safe, try more
                else:
                    hi = mid - 1

            c_by_collateral = lo

            # Pool cash bound (convert underlying cash -> cToken capacity)
            c_by_cash = (int(cash_raw) * MANTISSA) // int(exch_raw)

            redeem_c_raw = min(c_by_collateral, int(c_by_cash))

            # Final underlying you actually receive (mirror Solidity floor)
            under_raw = (redeem_c_raw * int(exch_raw)) // MANTISSA

            return True, {
                "cTokens_raw": int(redeem_c_raw),
                "cTokens": redeem_c_raw / (10 ** int(m_dec)),
                "underlying_raw": int(under_raw),
                "underlying": under_raw / (10 ** int(u_dec)),
                "bounds_raw": {
                    "collateral_cTokens": int(c_by_collateral),
                    "cash_cTokens": int(c_by_cash),
                },
                "exchangeRate_raw": int(exch_raw),
                "mToken_decimals": int(m_dec),
                "underlying_decimals": int(u_dec),
                "conversion_factor": redeem_c_raw / under_raw if under_raw > 0 else 0,
            }
        except Exception as exc:
            return False, str(exc)

    # ------------------------------------------------------------------ #
    # Public API - ETH Wrapping                                           #
    # ------------------------------------------------------------------ #

    async def wrap_eth(
        self,
        *,
        amount: int,
    ) -> tuple[bool, Any]:
        """Wrap ETH to WETH."""
        strategy = self._strategy_address()
        amount = int(amount)
        if amount <= 0:
            return False, "amount must be positive"

        tx = await self._encode_call(
            target=self.weth,
            abi=WETH_ABI,
            fn_name="deposit",
            args=[],
            from_address=strategy,
            value=amount,
        )
        return await self._execute(tx)

    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    # Max uint256 for unlimited approvals
    MAX_UINT256 = 2**256 - 1

    async def _ensure_allowance(
        self,
        *,
        token_address: str,
        owner: str,
        spender: str,
        amount: int,
    ) -> tuple[bool, Any]:
        """Ensure token allowance is sufficient, approving if needed.

        Approves for max uint256 to avoid precision issues with exact amounts.
        """
        if not self.token_txn_service:
            return False, "token_txn_service not configured"

        chain = {"id": self.chain_id}
        allowance = await self.token_txn_service.read_erc20_allowance(
            chain, token_address, owner, spender
        )
        if allowance.get("allowance", 0) >= amount:
            return True, {}

        # Approve for max uint256 to avoid precision/timing issues
        build_success, approve_tx = self.token_txn_service.build_erc20_approve(
            chain_id=self.chain_id,
            token_address=token_address,
            from_address=owner,
            spender=spender,
            amount=self.MAX_UINT256,
        )
        if not build_success:
            return False, approve_tx

        result = await self._broadcast_transaction(approve_tx)

        # Small delay after approval to ensure state is propagated on providers/chains
        # where we don't wait for additional confirmations by default.
        if result[0]:
            confirmations = 0
            if isinstance(result[1], dict):
                try:
                    confirmations = int(result[1].get("confirmations") or 0)
                except (TypeError, ValueError):
                    confirmations = 0
            if confirmations == 0:
                await asyncio.sleep(1.0)

        return result

    async def _execute(
        self, tx: dict[str, Any], max_retries: int = DEFAULT_MAX_RETRIES
    ) -> tuple[bool, Any]:
        """Execute a transaction (or return simulation data).

        Includes retry logic with exponential backoff for rate-limited RPCs.
        """
        if self.simulation:
            return True, {"simulation": tx}
        if not self.web3:
            return False, "web3 service not configured"

        last_error = None
        for attempt in range(max_retries):
            try:
                return await self.web3.broadcast_transaction(
                    tx, wait_for_receipt=True, timeout=DEFAULT_TRANSACTION_TIMEOUT
                )
            except Exception as exc:
                last_error = exc
                if _is_rate_limit_error(exc) and attempt < max_retries - 1:
                    wait_time = DEFAULT_BASE_DELAY * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue
                return False, str(exc)

        return False, str(last_error) if last_error else "Max retries exceeded"

    async def _broadcast_transaction(
        self, tx: dict[str, Any], max_retries: int = DEFAULT_MAX_RETRIES
    ) -> tuple[bool, Any]:
        """Broadcast a pre-built transaction.

        Includes retry logic with exponential backoff for rate-limited RPCs.
        """
        if not self.web3:
            return False, "web3 service not configured"

        last_error = None
        for attempt in range(max_retries):
            try:
                return await self.web3.evm_transactions.broadcast_transaction(
                    tx, wait_for_receipt=True, timeout=DEFAULT_TRANSACTION_TIMEOUT
                )
            except Exception as exc:
                last_error = exc
                if _is_rate_limit_error(exc) and attempt < max_retries - 1:
                    wait_time = DEFAULT_BASE_DELAY * (2**attempt)
                    await asyncio.sleep(wait_time)
                    continue
                return False, str(exc)

        return False, str(last_error) if last_error else "Max retries exceeded"

    async def _encode_call(
        self,
        *,
        target: str,
        abi: list[dict[str, Any]],
        fn_name: str,
        args: list[Any],
        from_address: str,
        value: int = 0,
    ) -> dict[str, Any]:
        """Encode a contract call without touching the network."""
        if not self.web3:
            raise ValueError("web3 service not configured")

        web3 = self.web3.get_web3(self.chain_id)
        contract = web3.eth.contract(address=target, abi=abi)

        try:
            tx_data = await getattr(contract.functions, fn_name)(
                *args
            ).build_transaction({"from": from_address})
            data = tx_data["data"]
        except ValueError as exc:
            raise ValueError(f"Failed to encode {fn_name}: {exc}") from exc

        tx: dict[str, Any] = {
            "chainId": int(self.chain_id),
            "from": to_checksum_address(from_address),
            "to": to_checksum_address(target),
            "data": data,
            "value": int(value),
        }
        return tx

    def _strategy_address(self) -> str:
        """Get the strategy wallet address."""
        addr = None
        if isinstance(self.strategy_wallet, dict):
            addr = self.strategy_wallet.get("address") or (
                (self.strategy_wallet.get("evm") or {}).get("address")
            )
        elif isinstance(self.strategy_wallet, str):
            addr = self.strategy_wallet
        if not addr:
            raise ValueError(
                "strategy_wallet address is required for Moonwell operations"
            )
        return to_checksum_address(addr)

    def _checksum(self, address: str | None) -> str:
        """Convert address to checksum format."""
        if not address:
            raise ValueError("Missing required contract address in Moonwell config")
        return to_checksum_address(address)
