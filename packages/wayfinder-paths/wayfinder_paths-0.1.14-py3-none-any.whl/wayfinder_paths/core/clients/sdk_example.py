"""
SDK Usage Examples

Demonstrates how to use the SDK with custom client implementations.
Use cases: mocks for testing, caching layers, alternative endpoints, rate limiting.
"""

from typing import Any

from wayfinder_paths.core.clients.ClientManager import ClientManager
from wayfinder_paths.core.clients.TokenClient import TokenClient


class CachedTokenClient:
    """Token client with in-memory caching"""

    def __init__(self):
        self._cache: dict[str, dict[str, Any]] = {}
        self._default_client = TokenClient()

    async def get_token_details(
        self, token_id: str, force_refresh: bool = False
    ) -> dict[str, Any]:
        cache_key = f"token_{token_id}"
        if not force_refresh and cache_key in self._cache:
            return self._cache[cache_key]
        data = await self._default_client.get_token_details(token_id, force_refresh)
        self._cache[cache_key] = data
        return data

    async def get_gas_token(self, chain_code: str) -> dict[str, Any]:
        return await self._default_client.get_gas_token(chain_code)


class MockHyperlendClient:
    """Mock client for testing"""

    async def get_stable_markets(
        self,
        *,
        required_underlying_tokens: float | None = None,
        buffer_bps: int | None = None,
        min_buffer_tokens: float | None = None,
    ) -> dict[str, Any]:
        return {
            "markets": {
                "0xMockToken": {
                    "symbol": "USDC",
                    "symbol_canonical": "usdc",
                    "display_symbol": "USDC",
                    "reserve": {},
                    "decimals": 6,
                    "headroom": 1000000000000,
                    "supply_cap": 5000000000000,
                }
            },
            "notes": [],
        }

    async def get_assets_view(
        self,
        *,
        user_address: str,
    ) -> dict[str, Any]:
        return {
            "block_number": 12345,
            "user": user_address,
            "native_balance_wei": 0,
            "native_balance": 0.0,
            "assets": [],
            "account_data": {
                "total_collateral_base": 0,
                "total_debt_base": 0,
                "available_borrows_base": 0,
                "current_liquidation_threshold": 0,
                "ltv": 0,
                "health_factor_wad": 0,
                "health_factor": 0.0,
            },
            "base_currency_info": {
                "marketReferenceCurrencyUnit": 100000000,
                "marketReferenceCurrencyPriceInUsd": 100000000,
                "networkBaseTokenPriceInUsd": 0,
                "networkBaseTokenPriceDecimals": 8,
            },
        }

    async def get_market_entry(
        self,
        *,
        token: str,
    ) -> dict[str, Any]:
        return {
            "symbol": "USDC",
            "symbol_canonical": "usdc",
            "display_symbol": "USDC",
            "reserve": {},
        }

    async def get_lend_rate_history(
        self,
        *,
        token: str,
        lookback_hours: int,
        force_refresh: bool | None = None,
    ) -> dict[str, Any]:
        return {
            "history": [],
        }


async def example_sdk_usage():
    """Direct client injection - inject only what you customize"""

    custom_token_client = CachedTokenClient()
    custom_hyperlend_client = MockHyperlendClient()

    ClientManager(
        clients={
            "token": custom_token_client,
            "hyperlend": custom_hyperlend_client,
        },
        skip_auth=True,
    )
    pass
