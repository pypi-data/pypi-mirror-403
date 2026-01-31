"""
Wallet Client
Fetches wallet-related data such as aggregated balances for the authenticated user.
"""

from __future__ import annotations

from typing import NotRequired, Required, TypedDict

from wayfinder_paths.core.clients.AuthClient import AuthClient
from wayfinder_paths.core.clients.WayfinderClient import WayfinderClient
from wayfinder_paths.core.config import get_api_base_url


class TokenBalance(TypedDict):
    """Token balance response structure"""

    token_id: Required[str]
    wallet_address: Required[str]
    balance: Required[str]
    balance_human: NotRequired[float | None]
    usd_value: NotRequired[float | None]


class PoolBalance(TypedDict):
    """Pool balance response structure"""

    pool_address: Required[str]
    chain_id: Required[int]
    user_address: Required[str]
    balance: Required[str]
    balance_human: NotRequired[float | None]
    usd_value: NotRequired[float | None]


class WalletClient(WayfinderClient):
    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=api_key)
        self.api_base_url = get_api_base_url()
        self._auth_client = AuthClient(api_key=api_key)

    async def get_token_balance_for_wallet(
        self,
        *,
        token_id: str,
        wallet_address: str,
        human_readable: bool = True,
    ) -> TokenBalance:
        """
        Fetch a single token balance for an explicit wallet address.

        Mirrors POST /api/v1/public/balances/token/
        """
        url = f"{self.api_base_url}/public/balances/token/"
        payload = {
            "token_id": token_id,
            "wallet_address": wallet_address,
            "human_readable": human_readable,
        }
        response = await self._authed_request("POST", url, json=payload)
        data = response.json()
        return data.get("data", data)

    async def get_pool_balance_for_wallet(
        self,
        *,
        pool_address: str,
        chain_id: int,
        user_address: str,
        human_readable: bool = True,
    ) -> PoolBalance:
        """
        Fetch a wallet's LP/share balance for a given pool address and chain.

        Mirrors POST /api/v1/public/balances/pool/
        """
        url = f"{self.api_base_url}/public/balances/pool/"
        payload = {
            "pool_address": pool_address,
            "chain_id": chain_id,
            "user_address": user_address,
            "human_readable": human_readable,
        }
        response = await self._authed_request("POST", url, json=payload)
        data = response.json()
        return data.get("data", data)
