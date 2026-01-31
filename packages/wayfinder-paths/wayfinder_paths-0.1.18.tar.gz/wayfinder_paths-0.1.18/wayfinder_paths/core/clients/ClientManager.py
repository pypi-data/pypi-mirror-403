"""
Client Manager
Consolidated client management for all API interactions
"""

from typing import Any

from wayfinder_paths.core.clients.BRAPClient import BRAPClient
from wayfinder_paths.core.clients.HyperlendClient import HyperlendClient
from wayfinder_paths.core.clients.LedgerClient import LedgerClient
from wayfinder_paths.core.clients.PoolClient import PoolClient
from wayfinder_paths.core.clients.protocols import (
    BRAPClientProtocol,
    HyperlendClientProtocol,
    LedgerClientProtocol,
    PoolClientProtocol,
    TokenClientProtocol,
    WalletClientProtocol,
)
from wayfinder_paths.core.clients.TokenClient import TokenClient
from wayfinder_paths.core.clients.WalletClient import WalletClient


class ClientManager:
    """
    Manages all API client instances for a strategy job.

    Args:
        clients: Optional dict of pre-instantiated clients to inject directly.
            Keys: 'token', 'hyperlend', 'ledger', 'wallet', 'transaction', 'pool', 'brap'.
            If not provided, defaults to HTTP-based clients.
        skip_auth: If True, skips authentication (for SDK usage).
    """

    def __init__(
        self,
        clients: dict[str, Any] | None = None,
        skip_auth: bool = False,
    ):
        """
        Initialize ClientManager.

        Args:
            clients: Optional dict of pre-instantiated clients to inject directly.
            skip_auth: If True, skips authentication (for SDK usage).
        """
        self._injected_clients = clients or {}
        self._skip_auth = skip_auth

        self._token_client: TokenClientProtocol | None = None
        self._wallet_client: WalletClientProtocol | None = None
        self._ledger_client: LedgerClientProtocol | None = None
        self._pool_client: PoolClientProtocol | None = None
        self._hyperlend_client: HyperlendClientProtocol | None = None
        self._brap_client: BRAPClientProtocol | None = None

    def _get_or_create_client(
        self,
        client_attr: str,
        injected_key: str,
        client_class: type[Any],
    ) -> Any:
        """
        Helper method to get or create a client instance.

        Args:
            client_attr: Name of the private attribute storing the client (e.g., "_token_client").
            injected_key: Key to look up in _injected_clients dict.
            client_class: Client class to instantiate if not injected.

        Returns:
            Client instance.
        """
        client = getattr(self, client_attr)
        if not client:
            client = self._injected_clients.get(injected_key) or client_class()
            setattr(self, client_attr, client)
        return client

    @property
    def token(self) -> TokenClientProtocol:
        """Get or create token client"""
        return self._get_or_create_client("_token_client", "token", TokenClient)

    @property
    def ledger(self) -> LedgerClientProtocol:
        """Get or create ledger client"""
        return self._get_or_create_client("_ledger_client", "ledger", LedgerClient)

    @property
    def pool(self) -> PoolClientProtocol:
        """Get or create pool client"""
        return self._get_or_create_client("_pool_client", "pool", PoolClient)

    @property
    def hyperlend(self) -> HyperlendClientProtocol:
        """Get or create hyperlend client"""
        return self._get_or_create_client(
            "_hyperlend_client", "hyperlend", HyperlendClient
        )

    @property
    def wallet(self) -> WalletClientProtocol:
        """Get or create wallet client"""
        return self._get_or_create_client("_wallet_client", "wallet", WalletClient)

    @property
    def brap(self) -> BRAPClientProtocol:
        """Get or create BRAP client"""
        return self._get_or_create_client("_brap_client", "brap", BRAPClient)

    def get_all_clients(self) -> dict[str, Any]:
        """Get all initialized clients for direct access"""
        return {
            "token": self._token_client,
            "transaction": self._transaction_client,
            "ledger": self._ledger_client,
            "pool": self._pool_client,
            "wallet": self._wallet_client,
            "hyperlend": self._hyperlend_client,
            "brap": self._brap_client,
        }
