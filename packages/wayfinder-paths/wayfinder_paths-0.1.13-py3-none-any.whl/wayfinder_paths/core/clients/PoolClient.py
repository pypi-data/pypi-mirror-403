"""
Pool Client
Provides read-only access to pool metadata and analytics via public endpoints.
"""

from __future__ import annotations

from typing import Any, NotRequired, Required, TypedDict

from wayfinder_paths.core.clients.AuthClient import AuthClient
from wayfinder_paths.core.clients.WayfinderClient import WayfinderClient
from wayfinder_paths.core.config import get_api_base_url


class PoolData(TypedDict):
    """Individual pool data structure"""

    id: Required[str]
    name: Required[str]
    symbol: Required[str]
    address: Required[str]
    chain_id: Required[int]
    chain_code: Required[str]
    apy: NotRequired[float]
    tvl: NotRequired[float]
    apy: NotRequired[float | None]
    tvlUsd: NotRequired[float | None]
    stablecoin: NotRequired[bool | None]
    ilRisk: NotRequired[str | None]
    network: NotRequired[str | None]


class PoolList(TypedDict):
    """Pool list response structure"""

    pools: Required[list[PoolData]]
    total: NotRequired[int | None]


class LlamaMatch(TypedDict):
    """Llama match data structure"""

    id: Required[str]
    apy: Required[float]
    tvlUsd: Required[float]
    stablecoin: Required[bool]
    ilRisk: Required[str]
    network: Required[str]


class PoolClient(WayfinderClient):
    """Client for pool-related read operations"""

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=api_key)
        self.api_base_url = f"{get_api_base_url()}"
        self._auth_client: AuthClient | None = AuthClient(api_key=api_key)

    async def get_pools(self) -> dict[str, LlamaMatch]:
        url = f"{self.api_base_url}/pools/"
        response = await self._request("GET", url, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)

    async def get_pools_by_ids(
        self,
        *,
        pool_ids: str,
    ) -> PoolList:
        url = f"{self.api_base_url}/pools/"
        params: dict[str, Any] = {"pool_ids": pool_ids}
        response = await self._request("GET", url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        return data.get("data", data)
