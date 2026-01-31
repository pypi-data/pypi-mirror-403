from __future__ import annotations

from typing import Any

from eth_utils import to_checksum_address

from wayfinder_paths.adapters.ledger_adapter.adapter import LedgerAdapter
from wayfinder_paths.adapters.token_adapter.adapter import TokenAdapter
from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.adapters.models import SWAP
from wayfinder_paths.core.clients.BRAPClient import (
    BRAPClient,
    BRAPQuoteResponse,
)
from wayfinder_paths.core.clients.LedgerClient import TransactionRecord
from wayfinder_paths.core.clients.TokenClient import TokenClient
from wayfinder_paths.core.constants import DEFAULT_SLIPPAGE, ZERO_ADDRESS
from wayfinder_paths.core.utils.erc20_service import (
    build_approve_transaction,
    get_token_allowance,
)
from wayfinder_paths.core.utils.transaction import send_transaction

_NEEDS_CLEAR_APPROVAL = {
    (1, "0xdac17f958d2ee523a2206206994597c13d831ec7"),
    (137, "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"),
    (56, "0x55d398326f99059ff775485246999027b3197955"),
}


class BRAPAdapter(BaseAdapter):
    adapter_type: str = "BRAP"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        strategy_wallet_signing_callback=None,
    ):
        super().__init__("brap_adapter", config)
        self.strategy_wallet_signing_callback = strategy_wallet_signing_callback
        self.brap_client = BRAPClient()
        self.token_client = TokenClient()
        self.token_adapter = TokenAdapter()
        self.ledger_adapter = LedgerAdapter()

    async def get_swap_quote(
        self,
        from_token_address: str,
        to_token_address: str,
        from_chain_id: int,
        to_chain_id: int,
        from_address: str,
        to_address: str,
        amount: str,
        slippage: float | None = None,
        wayfinder_fee: float | None = None,
    ) -> tuple[bool, BRAPQuoteResponse | str]:
        try:
            data = await self.brap_client.get_quote(
                from_token=from_token_address,
                to_token=to_token_address,
                from_chain=from_chain_id,
                to_chain=to_chain_id,
                from_wallet=from_address,
                from_amount=amount,
            )
            return (True, data)
        except Exception as e:
            self.logger.error(f"Error getting swap quote: {e}")
            return (False, str(e))

    async def get_best_quote(
        self,
        from_token_address: str,
        to_token_address: str,
        from_chain_id: int,
        to_chain_id: int,
        from_address: str,
        to_address: str,
        amount: str,
        slippage: float | None = None,
        wayfinder_fee: float | None = None,
        preferred_providers: list[str] | None = None,
    ) -> tuple[bool, dict[str, Any] | str]:
        try:
            data = await self.brap_client.get_quote(
                from_token=from_token_address,
                to_token=to_token_address,
                from_chain=from_chain_id,
                to_chain=to_chain_id,
                from_wallet=from_address,
                from_amount=amount,
            )

            raw_quotes = data.get("quotes")
            if isinstance(raw_quotes, list):
                all_quotes = raw_quotes
                best_quote = data.get("best_quote") or data.get("best_route")
            else:
                quotes_container = raw_quotes or {}
                all_quotes = quotes_container.get(
                    "all_quotes", []
                ) or quotes_container.get("quotes", [])
                best_quote = (
                    quotes_container.get("best_quote")
                    or data.get("best_quote")
                    or data.get("best_route")
                )

            # If preferred providers specified, select by provider preference
            if preferred_providers and all_quotes:
                selected_quote = self._select_quote_by_provider(
                    all_quotes, preferred_providers
                )
                if selected_quote:
                    return (True, selected_quote)
                # Fall through to best_quote if no preferred provider found

            if not best_quote:
                return (False, "No quotes available")

            return (True, best_quote)
        except Exception as e:
            self.logger.error(f"Error getting best quote: {e}")
            return (False, str(e))

    def _select_quote_by_provider(
        self,
        quotes: list[dict[str, Any]],
        preferred_providers: list[str],
    ) -> dict[str, Any] | None:
        # Normalize preferred providers to lowercase for case-insensitive matching
        preferred_lower = [p.lower() for p in preferred_providers]

        provider_quotes: dict[str, list[dict[str, Any]]] = {}
        for quote in quotes:
            # Provider name might be in different fields depending on BRAP response structure
            provider = (
                quote.get("provider")
                or quote.get("provider_name")
                or quote.get("source")
                or quote.get("protocol")
                or ""
            ).lower()
            if provider:
                if provider not in provider_quotes:
                    provider_quotes[provider] = []
                provider_quotes[provider].append(quote)

        # Select first matching provider in preference order
        for pref in preferred_lower:
            if pref in provider_quotes:
                provider_list = provider_quotes[pref]
                best_for_provider = max(
                    provider_list, key=lambda q: int(q.get("output_amount", 0) or 0)
                )
                self.logger.info(f"Selected quote from preferred provider: {pref}")
                return best_for_provider

        # Log available providers for debugging
        available = list(provider_quotes.keys())
        self.logger.warning(
            f"No preferred provider found. Wanted: {preferred_providers}, Available: {available}"
        )
        return None

    async def calculate_swap_fees(
        self,
        from_token_address: str,
        to_token_address: str,
        from_chain_id: int,
        to_chain_id: int,
        amount: str,
        slippage: float | None = None,
    ) -> tuple[bool, Any]:
        try:
            success, quote_data = await self.get_swap_quote(
                from_token_address=from_token_address,
                to_token_address=to_token_address,
                from_chain_id=from_chain_id,
                to_chain_id=to_chain_id,
                from_address="0x0000000000000000000000000000000000000000",
                to_address="0x0000000000000000000000000000000000000000",
                amount=amount,
                slippage=slippage,
            )

            if not success:
                return (False, quote_data)

            best_quote = quote_data.get("best_quote")

            if not best_quote:
                return (False, "No quote available for fee calculation")

            fee_estimate = best_quote.get("fee_estimate", {})
            fees = {
                "input_amount": best_quote.get("input_amount", 0),
                "output_amount": best_quote.get("output_amount", 0),
                "gas_fee": best_quote.get("gas_estimate") or 0,
                "bridge_fee": 0,
                "protocol_fee": fee_estimate.get("fee_total_usd", 0),
                "total_fee": fee_estimate.get("fee_total_usd", 0),
                "slippage": 0,
                "price_impact": best_quote.get("quote", {}).get("priceImpact", 0),
            }

            return (True, fees)
        except Exception as e:
            self.logger.error(f"Error calculating swap fees: {e}")
            return (False, str(e))

    async def compare_routes(
        self,
        from_token_address: str,
        to_token_address: str,
        from_chain_id: int,
        to_chain_id: int,
        amount: str,
        slippage: float | None = None,
    ) -> tuple[bool, Any]:
        try:
            data = await self.brap_client.get_quote(
                from_token=from_token_address,
                to_token=to_token_address,
                from_chain=from_chain_id,
                to_chain=to_chain_id,
                from_wallet="0x0000000000000000000000000000000000000000",
                from_amount=amount,
            )

            raw_quotes = data.get("quotes")
            if isinstance(raw_quotes, list):
                all_quotes = raw_quotes
                best_quote = data.get("best_quote") or data.get("best_route")
            else:
                quotes = raw_quotes or {}
                all_quotes = quotes.get("all_quotes", []) or quotes.get("quotes", [])
                best_quote = (
                    quotes.get("best_quote")
                    or data.get("best_quote")
                    or data.get("best_route")
                )

            if not all_quotes:
                return (False, "No routes available")

            # Sort quotes by output amount (descending)
            sorted_quotes = sorted(
                all_quotes, key=lambda x: int(x.get("output_amount", 0)), reverse=True
            )

            comparison = {
                "total_routes": len(all_quotes),
                "best_route": best_quote,
                "all_routes": sorted_quotes,
                "route_analysis": {
                    "highest_output": sorted_quotes[0] if sorted_quotes else None,
                    "lowest_fees": (
                        min(
                            all_quotes,
                            key=lambda x: float(
                                x.get("fee_estimate", {}).get("fee_total_usd", 0)
                            ),
                        )
                        if all_quotes
                        else None
                    ),
                    "fastest": (
                        min(all_quotes, key=lambda x: int(x.get("estimated_time", 0)))
                        if all_quotes
                        else None
                    ),
                },
            }

            return (True, comparison)
        except Exception as e:
            self.logger.error(f"Error comparing routes: {e}")
            return (False, str(e))

    async def swap_from_token_ids(
        self,
        from_token_id: str,
        to_token_id: str,
        from_address: str,
        amount: str,
        slippage: float = DEFAULT_SLIPPAGE,
        strategy_name: str | None = None,
        preferred_providers: list[str] | None = None,
    ) -> tuple[bool, Any]:
        from_token = await self.token_client.get_token_details(from_token_id)
        if not from_token:
            return (False, f"From token not found: {from_token_id}")
        to_token = await self.token_client.get_token_details(to_token_id)
        if not to_token:
            return (False, f"To token not found: {to_token_id}")

        success, best_quote = await self.get_best_quote(
            from_token_address=from_token.get("address"),
            to_token_address=to_token.get("address"),
            from_chain_id=(from_token.get("chain") or {}).get("id"),
            to_chain_id=(to_token.get("chain") or {}).get("id"),
            from_address=from_address,
            to_address=from_address,
            amount=amount,
            slippage=slippage,
            preferred_providers=preferred_providers,
        )
        if not success:
            return (False, best_quote)

        return await self.swap_from_quote(
            from_token=from_token,
            to_token=to_token,
            from_address=from_address,
            quote=best_quote,
            strategy_name=strategy_name,
        )

    async def swap_from_quote(
        self,
        from_token: dict[str, Any],
        to_token: dict[str, Any],
        from_address: str,
        quote: dict[str, Any],
        strategy_name: str | None = None,
    ) -> tuple[bool, Any]:
        chain = from_token.get("chain") or {}
        chain_id = self._chain_id(chain)

        calldata = quote.get("calldata") or {}
        transaction = dict(calldata)
        if not transaction or not transaction.get("data"):
            return (False, "Quote missing calldata")
        transaction["chainId"] = chain_id
        if "value" in transaction:
            transaction["value"] = int(transaction["value"])
        # Always set the sender to the strategy wallet for broadcast.
        # (Calldata may include either "from" or "from_address" depending on provider.)
        transaction["from"] = to_checksum_address(from_address)

        def _as_address(value: Any) -> str | None:
            if not isinstance(value, str):
                return None
            v = value.strip()
            if (
                v.startswith("0x")
                and len(v) == 42
                and v.lower() != ZERO_ADDRESS.lower()
            ):
                return v
            return None

        spender = transaction.get("to")

        approve_amount = (
            quote.get("input_amount")
            or quote.get("inputAmount")
            or transaction.get("value")
        )
        token_address = from_token.get("address")
        token_address_l = str(token_address or "").lower()
        is_native = token_address_l in {
            "",
            ZERO_ADDRESS.lower(),
            "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        }
        if token_address and (not is_native) and spender and approve_amount:
            approve_success, approve_response = await self._handle_token_approval(
                chain=chain,
                token_address=from_token.get("address"),
                owner_address=from_address,
                spender_address=spender,
                amount=int(approve_amount),
            )
            if not approve_success:
                return (False, approve_response)

        broadcast_success, broadcast_response = await self._send_tx(transaction)
        self.logger.info(
            f"Swap broadcast result: success={broadcast_success}, "
            f"response={broadcast_response}"
        )
        # Log only key fields to avoid spamming raw HexBytes logs
        if isinstance(broadcast_response, dict):
            tx_hash_log = broadcast_response.get("tx_hash", "unknown")
            block_log = broadcast_response.get("block_number", "unknown")
            status_log = (
                broadcast_response.get("receipt", {}).get("status", "unknown")
                if isinstance(broadcast_response.get("receipt"), dict)
                else "unknown"
            )
            self.logger.info(
                f"Swap broadcast: success={broadcast_success}, tx={tx_hash_log}, block={block_log}, status={status_log}"
            )
        else:
            self.logger.info(f"Swap broadcast: success={broadcast_success}")
        if not broadcast_success:
            return (False, broadcast_response)

        tx_hash = None
        block_number = None
        confirmations = None
        confirmed_block_number = None
        if isinstance(broadcast_response, dict):
            tx_hash = broadcast_response.get("tx_hash") or broadcast_response.get(
                "transaction_hash"
            )
            block_number = broadcast_response.get("block_number")
            confirmations = broadcast_response.get("confirmations")
            confirmed_block_number = broadcast_response.get("confirmed_block_number")

        # Record the swap operation in ledger - but don't let ledger errors fail the swap
        # since the on-chain transaction already succeeded
        try:
            ledger_record = await self._record_swap_operation(
                from_token=from_token,
                to_token=to_token,
                wallet_address=from_address,
                quote=quote,
                broadcast_response=broadcast_response,
                strategy_name=strategy_name,
            )
        except Exception as e:
            self.logger.warning(
                f"Ledger recording failed (swap succeeded on-chain): {e}"
            )
            ledger_record = {}

        result_payload: dict[str, Any] = {
            "from_amount": quote.get("input_amount"),
            "to_amount": quote.get("output_amount"),
            "tx_hash": tx_hash,
            "block_number": block_number,
            "confirmations": confirmations,
            "confirmed_block_number": confirmed_block_number,
        }
        if isinstance(ledger_record, dict):
            result_payload.update(ledger_record)

        return (True, result_payload)

    async def get_bridge_quote(
        self,
        from_token_address: str,
        to_token_address: str,
        from_chain_id: int,
        to_chain_id: int,
        amount: str,
        slippage: float | None = None,
    ) -> tuple[bool, Any]:
        # For BRAP, bridge operations are the same as swap operations
        return await self.get_swap_quote(
            from_token_address=from_token_address,
            to_token_address=to_token_address,
            from_chain_id=from_chain_id,
            to_chain_id=to_chain_id,
            from_address="0x0000000000000000000000000000000000000000",
            to_address="0x0000000000000000000000000000000000000000",
            amount=amount,
            slippage=slippage,
        )

    async def estimate_gas_cost(
        self, from_chain_id: int, to_chain_id: int, operation_type: str = "swap"
    ) -> tuple[bool, Any]:
        try:
            # This is a simplified estimation - in practice, you'd want to
            # query actual gas prices from the chains
            gas_estimates = {
                "ethereum": {"swap": 150000, "bridge": 200000},
                "base": {"swap": 100000, "bridge": 150000},
                "arbitrum": {"swap": 80000, "bridge": 120000},
                "polygon": {"swap": 60000, "bridge": 100000},
            }

            # Map chain IDs to names (simplified)
            chain_names = {
                1: "ethereum",
                8453: "base",
                42161: "arbitrum",
                137: "polygon",
            }

            from_chain = chain_names.get(from_chain_id, "unknown")
            to_chain = chain_names.get(to_chain_id, "unknown")

            from_gas = gas_estimates.get(from_chain, {}).get(operation_type, 100000)
            to_gas = gas_estimates.get(to_chain, {}).get(operation_type, 100000)

            return (
                True,
                {
                    "from_chain": from_chain,
                    "to_chain": to_chain,
                    "from_gas_estimate": from_gas,
                    "to_gas_estimate": to_gas,
                    "total_operations": 2 if from_chain_id != to_chain_id else 1,
                    "operation_type": operation_type,
                },
            )
        except Exception as e:
            self.logger.error(f"Error estimating gas cost: {e}")
            return (False, str(e))

    async def validate_swap_parameters(
        self,
        from_token_address: str,
        to_token_address: str,
        from_chain_id: int,
        to_chain_id: int,
        amount: str,
    ) -> tuple[bool, Any]:
        try:
            validation_errors = []

            # Basic validation
            if not from_token_address or len(from_token_address) != 42:
                validation_errors.append("Invalid from_token_address")

            if not to_token_address or len(to_token_address) != 42:
                validation_errors.append("Invalid to_token_address")

            if from_chain_id <= 0 or to_chain_id <= 0:
                validation_errors.append("Invalid chain IDs")

            try:
                amount_int = int(amount)
                if amount_int <= 0:
                    validation_errors.append("Amount must be positive")
            except (ValueError, TypeError):
                validation_errors.append("Invalid amount format")

            if validation_errors:
                return (False, {"valid": False, "errors": validation_errors})

            # Try to get a quote to validate the swap is possible
            success, quote_data = await self.get_swap_quote(
                from_token_address=from_token_address,
                to_token_address=to_token_address,
                from_chain_id=from_chain_id,
                to_chain_id=to_chain_id,
                from_address="0x0000000000000000000000000000000000000000",
                to_address="0x0000000000000000000000000000000000000000",
                amount=amount,
            )

            if not success:
                validation_errors.append(f"Swap not possible: {quote_data}")
                return (False, {"valid": False, "errors": validation_errors})

            best_quote = (
                quote_data.get("best_quote", {}) if isinstance(quote_data, dict) else {}
            )
            return (
                True,
                {
                    "valid": True,
                    "quote_available": True,
                    "estimated_output": str(best_quote.get("output_amount", 0)),
                },
            )
        except Exception as e:
            self.logger.error(f"Error validating swap parameters: {e}")
            return (False, str(e))

    async def _handle_token_approval(
        self,
        *,
        chain: dict[str, Any],
        token_address: str,
        owner_address: str,
        spender_address: str,
        amount: int,
    ) -> tuple[bool, Any]:
        chain_id = self._chain_id(chain)
        token_checksum = to_checksum_address(token_address)
        owner_checksum = to_checksum_address(owner_address)
        spender_checksum = to_checksum_address(spender_address)

        if (chain_id, token_checksum.lower()) in _NEEDS_CLEAR_APPROVAL:
            allowance = await get_token_allowance(
                token_checksum,
                chain_id,
                owner_checksum,
                spender_checksum,
            )
            if allowance > 0:
                clear_tx = await build_approve_transaction(
                    from_address=owner_checksum,
                    chain_id=chain_id,
                    token_address=token_checksum,
                    spender_address=spender_checksum,
                    amount=0,
                )
                clear_result = await self._send_tx(clear_tx)
                if not clear_result[0]:
                    return clear_result

        approve_tx = await build_approve_transaction(
            from_address=owner_checksum,
            chain_id=chain_id,
            token_address=token_checksum,
            spender_address=spender_checksum,
            amount=int(amount),
        )
        return await self._send_tx(approve_tx)

    async def _send_tx(self, tx: dict[str, Any]) -> tuple[bool, Any]:
        txn_hash = await send_transaction(tx, self.strategy_wallet_signing_callback)
        return True, txn_hash

    async def _record_swap_operation(
        self,
        from_token: dict[str, Any],
        to_token: dict[str, Any],
        wallet_address: str,
        quote: dict[str, Any],
        broadcast_response: dict[str, Any] | Any,
        strategy_name: str | None = None,
    ) -> TransactionRecord | dict[str, Any]:
        from_amount_usd = quote.get("from_amount_usd")
        if from_amount_usd is None:
            from_amount_usd = await self._token_amount_usd(
                from_token, quote.get("input_amount")
            )

        to_amount_usd = quote.get("to_amount_usd")
        if to_amount_usd is None:
            to_amount_usd = await self._token_amount_usd(
                to_token, quote.get("output_amount")
            )

        response = broadcast_response if isinstance(broadcast_response, dict) else {}
        operation_data = SWAP(
            adapter=self.adapter_type,
            from_token_id=str(from_token.get("id")),
            to_token_id=str(to_token.get("id")),
            from_amount=str(quote.get("input_amount")),
            to_amount=str(quote.get("output_amount")),
            from_amount_usd=from_amount_usd or 0,
            to_amount_usd=to_amount_usd or 0,
            transaction_hash=response.get("tx_hash")
            or response.get("transaction_hash"),
            transaction_chain_id=from_token.get("chain_id")
            or (from_token.get("chain") or {}).get("id"),
            transaction_status=response.get("transaction_status"),
            # Don't pass raw receipt - it contains HexBytes that can't be JSON serialized
            transaction_receipt=None,
        )

        try:
            success, ledger_response = await self.ledger_adapter.record_operation(
                wallet_address=wallet_address,
                operation_data=operation_data,
                usd_value=from_amount_usd or 0,
                strategy_name=strategy_name,
            )
            if success:
                return ledger_response
            self.logger.warning(
                "Ledger swap record failed", error=ledger_response, quote=quote
            )
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(f"Ledger swap record raised: {exc}", quote=quote)

        return operation_data.model_dump(mode="json")

    async def _token_amount_usd(
        self, token_info: dict[str, Any], raw_amount: Any
    ) -> float | None:
        if raw_amount is None:
            return None
        success, price_data = await self.token_adapter.get_token_price(
            token_info.get("token_id")
        )
        if not success or not price_data:
            return None
        decimals = token_info.get("decimals") or 18
        return (
            price_data.get("current_price", 0.0)
            * float(raw_amount)
            / 10 ** int(decimals)
        )

    def _chain_id(self, chain: Any) -> int:
        if isinstance(chain, dict):
            chain_id = chain.get("id")
        else:
            chain_id = getattr(chain, "id", None)
        if chain_id is None:
            raise ValueError("Chain ID is required")
        return int(chain_id)
