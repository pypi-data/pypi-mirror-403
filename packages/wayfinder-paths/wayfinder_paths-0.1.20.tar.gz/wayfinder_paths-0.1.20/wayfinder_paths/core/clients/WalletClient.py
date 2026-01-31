from __future__ import annotations

from typing import NotRequired, Required, TypedDict

from wayfinder_paths.core.clients.WayfinderClient import WayfinderClient
from wayfinder_paths.core.config import get_api_base_url


class AddressBalance(TypedDict):
    balance: Required[int]
    balance_human: NotRequired[float | None]
    usd_value: NotRequired[float | None]
    address: NotRequired[str]
    token_id: NotRequired[str | None]
    wallet_address: NotRequired[str]
    chain_id: NotRequired[int]


class WalletClient(WayfinderClient):
    def __init__(self):
        super().__init__()
        self.api_base_url = get_api_base_url()

    async def get_token_balance_for_address(
        self,
        *,
        wallet_address: str,
        query: str,
        chain_id: int | None = None,
    ) -> AddressBalance:
        if chain_id is None:
            raise ValueError("chain_id is required")

        url = f"{self.api_base_url}/v1/blockchain/balances/address/"
        params = {
            "wallet_address": wallet_address,
            "chain_id": chain_id,
            "query": query,
        }
        response = await self._authed_request("GET", url, params=params)
        return response.json()
