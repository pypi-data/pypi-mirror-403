"""
Token Adapter
Handles token information, prices, and parsing
"""

from __future__ import annotations

from typing import NotRequired, Required, TypedDict

from wayfinder_paths.core.clients.WayfinderClient import WayfinderClient
from wayfinder_paths.core.config import get_api_base_url


class TokenLinks(TypedDict):
    """Token links structure"""

    github: NotRequired[list[str]]
    reddit: NotRequired[str]
    discord: NotRequired[str]
    twitter: NotRequired[str]
    homepage: NotRequired[list[str]]
    telegram: NotRequired[str]


class ChainAddress(TypedDict):
    """Chain address structure"""

    address: Required[str]
    token_id: Required[str]
    is_contract: NotRequired[bool]
    chain_id: NotRequired[int]


class ChainInfo(TypedDict):
    """Chain information structure"""

    id: Required[int]
    name: Required[str]
    code: Required[str]


class TokenMetadata(TypedDict):
    """Token metadata structure"""

    query_processed: NotRequired[str]
    query_type: NotRequired[str]
    has_addresses: NotRequired[bool]
    address_count: NotRequired[int]
    has_price_data: NotRequired[bool]


class TokenDetails(TypedDict):
    """Token details response structure"""

    asset_id: NotRequired[str]
    token_ids: NotRequired[list[str]]
    name: Required[str]
    symbol: Required[str]
    decimals: Required[int]
    description: NotRequired[str]
    links: NotRequired[TokenLinks]
    categories: NotRequired[list[str]]
    current_price: NotRequired[float]
    market_cap: NotRequired[float]
    total_volume_usd_24h: NotRequired[float]
    price_change_24h: NotRequired[float]
    price_change_7d: NotRequired[float]
    price_change_30d: NotRequired[float]
    price_change_1y: NotRequired[float]
    addresses: NotRequired[dict[str, str]]
    chain_addresses: NotRequired[dict[str, ChainAddress]]
    chain_ids: NotRequired[dict[str, int]]
    id: NotRequired[int]
    token_id: Required[str]
    address: Required[str]
    chain: NotRequired[ChainInfo]
    query: NotRequired[str]
    query_type: NotRequired[str]
    metadata: NotRequired[TokenMetadata]
    image_url: NotRequired[str | None]


class GasToken(TypedDict):
    """Gas token response structure"""

    id: Required[str]
    coingecko_id: NotRequired[str]
    token_id: Required[str]
    name: Required[str]
    symbol: Required[str]
    address: Required[str]
    decimals: Required[int]
    chain: NotRequired[ChainInfo]


class TokenClient(WayfinderClient):
    """Adapter for token-related operations"""

    def __init__(self):
        super().__init__()
        self.api_base_url = f"{get_api_base_url()}/v1/blockchain/tokens"

    async def get_token_details(
        self, query: str, market_data: bool = False, chain_id: int | None = None
    ) -> TokenDetails:
        """
        Get token data including price from the token-details endpoint.

        Args:
            query: Token identifier, address, or symbol to query
            market_data: Whether to include market data (default: True)
            chain_id: Optional chain ID

        Returns:
            Full token data including price information
        """
        url = f"{self.api_base_url}/detail/"
        params = {
            "query": query,
            "market_data": market_data,
        }
        if chain_id is not None:
            params["chain_id"] = chain_id
        response = await self._authed_request("GET", url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)

    async def get_gas_token(self, query: str) -> GasToken:
        """
        Fetch the native gas token for a given chain code or query.

        Args:
            query: Chain code or query string

        Returns:
            Gas token information including chain details
        """
        url = f"{self.api_base_url}/gas/"
        params = {"query": query}
        response = await self._authed_request("GET", url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)
