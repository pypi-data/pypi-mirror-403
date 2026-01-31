"""
Hyperlend Client
Provides access to Hyperlend stable markets data via blockchain endpoints.
"""

from __future__ import annotations

from typing import Any, Required, TypedDict

from wayfinder_paths.core.clients.WayfinderClient import WayfinderClient
from wayfinder_paths.core.config import get_api_base_url


class AssetsView(TypedDict):
    """Assets view response structure"""

    block_number: Required[int]
    user: Required[str]
    native_balance_wei: Required[int]
    native_balance: Required[float]
    assets: Required[list[AssetInfo]]
    account_data: Required[AccountData]
    base_currency_info: Required[BaseCurrencyInfo]


class MarketEntry(TypedDict):
    """Market entry data structure"""

    symbol: Required[str]
    symbol_canonical: Required[str]
    display_symbol: Required[str]
    reserve: Required[dict[str, Any]]


class LendRateHistory(TypedDict):
    """Lend rate history response structure"""

    history: Required[list[RateHistoryEntry]]


class MarketHeadroom(TypedDict):
    """Market headroom data structure"""

    symbol: Required[str]
    symbol_canonical: Required[str]
    display_symbol: Required[str]
    reserve: Required[dict[str, Any]]
    decimals: Required[int]
    headroom: Required[int]
    supply_cap: Required[int]


class StableMarketsHeadroomResponse(TypedDict):
    """Stable markets headroom response structure"""

    markets: Required[dict[str, MarketHeadroom]]
    notes: Required[list[str]]


class RateHistoryEntry(TypedDict):
    """Rate history entry data structure"""

    timestamp_ms: Required[int]
    timestamp: Required[float]
    supply_apr: Required[float]
    supply_apy: Required[float]
    borrow_apr: Required[float]
    borrow_apy: Required[float]
    token: Required[str]
    symbol: Required[str]
    display_symbol: Required[str]


class AssetInfo(TypedDict):
    """Asset information structure"""

    underlying: Required[str]
    symbol: Required[str]
    symbol_canonical: Required[str]
    symbol_display: Required[str]
    decimals: Required[int]
    a_token: Required[str]
    variable_debt_token: Required[str]
    usage_as_collateral_enabled: Required[bool]
    borrowing_enabled: Required[bool]
    is_active: Required[bool]
    is_frozen: Required[bool]
    is_paused: Required[bool]
    is_siloed_borrowing: Required[bool]
    is_stablecoin: Required[bool]
    underlying_wallet_balance: Required[float]
    underlying_wallet_balance_wei: Required[int]
    price_usd: Required[float]
    supply: Required[float]
    variable_borrow: Required[float]
    supply_usd: Required[float]
    variable_borrow_usd: Required[float]
    supply_apr: Required[float]
    supply_apy: Required[float]
    variable_borrow_apr: Required[float]
    variable_borrow_apy: Required[float]


class AccountData(TypedDict):
    """Account data structure"""

    total_collateral_base: Required[int | float]
    total_debt_base: Required[int | float]
    available_borrows_base: Required[int | float]
    current_liquidation_threshold: Required[int | float]
    ltv: Required[int | float]
    health_factor_wad: Required[int]
    health_factor: Required[float]


class BaseCurrencyInfo(TypedDict):
    """Base currency information structure"""

    marketReferenceCurrencyUnit: Required[int]
    marketReferenceCurrencyPriceInUsd: Required[int]
    networkBaseTokenPriceInUsd: Required[int]
    networkBaseTokenPriceDecimals: Required[int]


class HyperlendClient(WayfinderClient):
    """Client for Hyperlend-related operations"""

    def __init__(self):
        super().__init__()
        self.api_base_url = get_api_base_url()

    async def get_stable_markets(
        self,
        *,
        required_underlying_tokens: float | None = None,
        buffer_bps: int | None = None,
        min_buffer_tokens: float | None = None,
    ) -> StableMarketsHeadroomResponse:
        """
        Fetch stable markets headroom from Hyperlend.

        Args:
            required_underlying_tokens: Required underlying tokens amount
            buffer_bps: Buffer in basis points
            min_buffer_tokens: Minimum buffer in tokens

        Example:
            GET /api/v1/blockchain/hyperlend/stable_markets_headroom/?required_underlying_tokens=1000&buffer_bps=50&min_buffer_tokens=100

        Returns:
            Dictionary containing stable markets headroom data with markets and notes
        """
        url = f"{self.api_base_url}/v1/blockchain/hyperlend/stable_markets_headroom/"
        params: dict[str, Any] = {}
        if required_underlying_tokens is not None:
            params["required_underlying_tokens"] = required_underlying_tokens
        if buffer_bps is not None:
            params["buffer_bps"] = buffer_bps
        if min_buffer_tokens is not None:
            params["min_buffer_tokens"] = min_buffer_tokens

        response = await self._authed_request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)

    async def get_assets_view(
        self,
        *,
        user_address: str,
    ) -> AssetsView:
        """
        Fetch assets view for a user address from Hyperlend.

        Args:
            user_address: User wallet address to query assets for

        Example:
            GET /api/v1/blockchain/hyperlend/assets/?user_address=0x0c737cB5934afCb5B01965141F865F795B324080

        Returns:
            Dictionary containing assets view data with account information and base currency info
        """
        url = f"{self.api_base_url}/v1/blockchain/hyperlend/assets/"
        params: dict[str, Any] = {
            "user_address": user_address,
        }

        response = await self._authed_request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)

    async def get_market_entry(
        self,
        *,
        token: str,
    ) -> MarketEntry:
        """
        Fetch market entry from Hyperlend.

        Args:
            token: Token address to query market for

        Example:
            GET /api/v1/blockchain/hyperlend/market_entry/?token=0x5555555555555555555555555555555555555555

        Returns:
            Dictionary containing market entry data with symbol and reserve information
        """
        url = f"{self.api_base_url}/v1/blockchain/hyperlend/market_entry/"
        params: dict[str, Any] = {
            "token": token,
        }

        response = await self._authed_request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)

    async def get_lend_rate_history(
        self,
        *,
        token: str,
        lookback_hours: int,
        force_refresh: bool | None = None,
    ) -> LendRateHistory:
        """
        Fetch lend rate history from Hyperlend.

        Args:
            token: Token address to query rate history for
            lookback_hours: Number of hours to look back for rate history
            force_refresh: Whether to force refresh the data (optional)

        Example:
            GET /api/v1/blockchain/hyperlend/lend_rate_history/?token=0x5555555555555555555555555555555555555555&lookback_hours=24&force_refresh=false

        Returns:
            Dictionary containing lend rate history data with history array
        """
        url = f"{self.api_base_url}/v1/blockchain/hyperlend/lend_rate_history/"
        params: dict[str, Any] = {
            "token": token,
            "lookback_hours": lookback_hours,
        }
        if force_refresh is not None:
            params["force_refresh"] = "true" if force_refresh else "false"

        response = await self._authed_request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)
