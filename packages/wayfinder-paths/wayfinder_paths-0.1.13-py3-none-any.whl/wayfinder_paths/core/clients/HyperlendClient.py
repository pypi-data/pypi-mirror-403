"""
Hyperlend Client
Provides access to Hyperlend stable markets data via public endpoints.
"""

from __future__ import annotations

from typing import Any, NotRequired, Required, TypedDict

from wayfinder_paths.core.clients.WayfinderClient import WayfinderClient
from wayfinder_paths.core.config import get_api_base_url


class StableMarket(TypedDict):
    """Stable market data structure"""

    chain_id: Required[int]
    token_address: Required[str]
    symbol: Required[str]
    name: Required[str]
    underlying_tokens: Required[float]
    buffer_bps: Required[int]
    min_buffer_tokens: Required[float]
    is_stable_symbol: Required[bool]


class AssetsView(TypedDict):
    """Assets view response structure"""

    chain_id: Required[int]
    user_address: Required[str]
    assets: Required[list[dict[str, Any]]]
    total_value: NotRequired[float | None]


class MarketEntry(TypedDict):
    """Market entry data structure"""

    chain_id: Required[int]
    token_address: Required[str]
    market_data: Required[dict[str, Any]]


class LendRateHistory(TypedDict):
    """Lend rate history response structure"""

    chain_id: Required[int]
    token_address: Required[str]
    lookback_hours: Required[int]
    rates: Required[list[dict[str, Any]]]


class HyperlendClient(WayfinderClient):
    """Client for Hyperlend-related operations"""

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=api_key)
        self.api_base_url = get_api_base_url()

    async def get_stable_markets(
        self,
        *,
        chain_id: int,
        required_underlying_tokens: float | None = None,
        buffer_bps: int | None = None,
        min_buffer_tokens: float | None = None,
        is_stable_symbol: bool | None = None,
    ) -> list[StableMarket]:
        """
        Fetch stable markets from Hyperlend.

        Args:
            chain_id: Chain ID to query markets for
            required_underlying_tokens: Required underlying tokens amount
            buffer_bps: Buffer in basis points
            min_buffer_tokens: Minimum buffer in tokens
            is_stable_symbol: Filter by stable symbol (optional)

        Example:
            GET /api/v1/public/hyperlend/stable-markets/?chain_id=999&required_underlying_tokens=1000.0&buffer_bps=100&min_buffer_tokens=100.0&is_stable_symbol=true

        Returns:
            Dictionary containing stable markets data
        """
        url = f"{self.api_base_url}/public/hyperlend/stable-markets/"
        params: dict[str, Any] = {"chain_id": chain_id}
        if required_underlying_tokens is not None:
            params["required_underlying_tokens"] = required_underlying_tokens
        if buffer_bps is not None:
            params["buffer_bps"] = buffer_bps
        if min_buffer_tokens is not None:
            params["min_buffer_tokens"] = min_buffer_tokens
        if is_stable_symbol is not None:
            params["is_stable_symbol"] = "true" if is_stable_symbol else "false"

        response = await self._authed_request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)

    async def get_assets_view(
        self,
        *,
        chain_id: int,
        user_address: str,
    ) -> AssetsView:
        """
        Fetch assets view for a user address from Hyperlend.

        Args:
            chain_id: Chain ID to query assets for
            user_address: User wallet address to query assets for

        Example:
            GET /api/v1/public/hyperlend/assets-view/?chain_id=999&user_address=0x0c737cB5934afCb5B01965141F865F795B324080

        Returns:
            Dictionary containing assets view data
        """
        url = f"{self.api_base_url}/public/hyperlend/assets-view/"
        params: dict[str, Any] = {
            "chain_id": chain_id,
            "user_address": user_address,
        }

        response = await self._authed_request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)

    async def get_market_entry(
        self,
        *,
        chain_id: int,
        token_address: str,
    ) -> MarketEntry:
        """
        Fetch market entry from Hyperlend.

        Args:
            chain_id: Chain ID to query market for
            token_address: Token address to query market for

        Example:
            GET /api/v1/public/hyperlend/market-entry/?chain_id=999&token_address=0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48

        Returns:
            Dictionary containing market entry data
        """
        url = f"{self.api_base_url}/public/hyperlend/market-entry/"
        params: dict[str, Any] = {
            "chain_id": chain_id,
            "token_address": token_address,
        }

        response = await self._authed_request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)

    async def get_lend_rate_history(
        self,
        *,
        chain_id: int,
        token_address: str,
        lookback_hours: int,
    ) -> LendRateHistory:
        """
        Fetch lend rate history from Hyperlend.

        Args:
            chain_id: Chain ID to query rate history for
            token_address: Token address to query rate history for
            lookback_hours: Number of hours to look back for rate history

        Example:
            GET /api/v1/public/hyperlend/lend-rate-history/?chain_id=999&token_address=0x5555555555555555555555555555555555555555&lookback_hours=24

        Returns:
            Dictionary containing lend rate history data
        """
        url = f"{self.api_base_url}/public/hyperlend/lend-rate-history/"
        params: dict[str, Any] = {
            "chain_id": chain_id,
            "token_address": token_address,
            "lookback_hours": lookback_hours,
        }

        response = await self._authed_request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)
