"""
Token Adapter
Handles token information, prices, and parsing
"""

from __future__ import annotations

from typing import NotRequired, Required, TypedDict

from wayfinder_paths.core.clients.AuthClient import AuthClient
from wayfinder_paths.core.clients.WayfinderClient import WayfinderClient
from wayfinder_paths.core.config import get_api_base_url


class TokenDetails(TypedDict):
    """Token details response structure"""

    id: Required[str]
    address: Required[str]
    symbol: Required[str]
    name: Required[str]
    decimals: Required[int]
    chain_id: Required[int]
    chain_code: Required[str]
    price_usd: NotRequired[float]
    price: NotRequired[float]
    image_url: NotRequired[str | None]
    coingecko_id: NotRequired[str | None]


class GasToken(TypedDict):
    """Gas token response structure"""

    id: Required[str]
    address: Required[str]
    symbol: Required[str]
    name: Required[str]
    decimals: Required[int]
    chain_id: Required[int]
    chain_code: Required[str]
    price_usd: NotRequired[float]


class TokenClient(WayfinderClient):
    """Adapter for token-related operations"""

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=api_key)
        self.api_base_url = f"{self.api_base_url}/tokens"
        self._auth_client: AuthClient | None = AuthClient(api_key=api_key)

    # ============== Public (No-Auth) Endpoints ==============

    async def get_token_details(
        self, token_id: str, force_refresh: bool = False
    ) -> TokenDetails:
        """
        Get token data including price from the token-details endpoint

        Args:
            token_id: Token identifier or address

        Returns:
            Full token data including price information
        """
        url = f"{get_api_base_url()}/public/tokens/detail/"
        params = {
            "query": token_id,
            "get_chart": "false",
            "force_refresh": str(force_refresh),
        }
        # Public endpoint: do not pass auth headers
        response = await self._request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)

    async def get_gas_token(self, chain_code: str) -> GasToken:
        """
        Fetch the native gas token for a given chain code via public endpoint.
        Example: GET /api/v1/public/tokens/gas/?chain_code=base
        """
        url = f"{get_api_base_url()}/public/tokens/gas/"
        params = {"chain_code": chain_code}
        # Public endpoint: do not pass auth headers
        response = await self._request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)
