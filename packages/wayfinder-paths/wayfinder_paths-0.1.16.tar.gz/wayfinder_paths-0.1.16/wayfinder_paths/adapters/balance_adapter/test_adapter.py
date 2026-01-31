from unittest.mock import AsyncMock, patch

import pytest

from wayfinder_paths.adapters.balance_adapter.adapter import BalanceAdapter


class TestBalanceAdapter:
    """Test cases for BalanceAdapter"""

    @pytest.fixture
    def mock_wallet_client(self):
        """Mock WalletClient for testing"""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def mock_token_client(self):
        """Mock TokenClient for testing"""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def adapter(self, mock_wallet_client, mock_token_client):
        """Create a BalanceAdapter instance with mocked clients for testing"""
        with (
            patch(
                "wayfinder_paths.adapters.balance_adapter.adapter.WalletClient",
                return_value=mock_wallet_client,
            ),
            patch(
                "wayfinder_paths.adapters.balance_adapter.adapter.TokenClient",
                return_value=mock_token_client,
            ),
        ):
            return BalanceAdapter(config={})

    @pytest.mark.asyncio
    async def test_health_check(self, adapter):
        """Test adapter health check"""
        health = await adapter.health_check()
        assert isinstance(health, dict)
        assert health.get("status") in {"healthy", "unhealthy", "error"}

    @pytest.mark.asyncio
    async def test_connect(self, adapter):
        """Test adapter connection"""
        ok = await adapter.connect()
        assert isinstance(ok, bool)

    def test_adapter_type(self, adapter):
        """Test adapter has adapter_type"""
        assert adapter.adapter_type == "BALANCE"

    @pytest.mark.asyncio
    async def test_get_balance_with_query_string(
        self, adapter, mock_token_client, mock_wallet_client
    ):
        """Test get_balance with query as string (auto-resolves chain_id)."""
        mock_token_client.get_token_details = AsyncMock(
            return_value={
                "token_id": "usd-coin-base",
                "address": "0x123",
                "chain": {"id": 8453, "code": "base"},
            }
        )
        mock_wallet_client.get_token_balance_for_address = AsyncMock(
            return_value={"balance": 1000000}
        )

        success, balance = await adapter.get_balance(
            query="usd-coin-base",
            wallet_address="0xWallet",
        )

        assert success
        assert balance == 1000000
        mock_token_client.get_token_details.assert_called_once_with("usd-coin-base")
        mock_wallet_client.get_token_balance_for_address.assert_called_once_with(
            wallet_address="0xWallet",
            query="usd-coin-base",
            chain_id=8453,
        )

    @pytest.mark.asyncio
    async def test_get_balance_with_query_dict(
        self, adapter, mock_token_client, mock_wallet_client
    ):
        """get_balance accepts query= as dict with token_id key."""
        mock_token_client.get_token_details = AsyncMock(
            return_value={
                "token_id": "wsteth-base",
                "address": "0x456",
                "chain": {"id": 8453, "code": "base"},
            }
        )
        mock_wallet_client.get_token_balance_for_address = AsyncMock(
            return_value={"balance": 3000000}
        )

        success, balance = await adapter.get_balance(
            query={"token_id": "wsteth-base"},
            wallet_address="0x123",
        )
        assert success
        assert balance == 3000000
        mock_token_client.get_token_details.assert_called_once_with("wsteth-base")
        mock_wallet_client.get_token_balance_for_address.assert_called_once_with(
            wallet_address="0x123",
            query="wsteth-base",
            chain_id=8453,
        )

    @pytest.mark.asyncio
    async def test_get_balance_missing_query(self, adapter):
        """get_balance returns error when query is empty or missing token_id."""
        success, result = await adapter.get_balance(query={}, wallet_address="0xabc")
        assert success is False
        assert "missing query" in str(result)

    @pytest.mark.asyncio
    async def test_get_balance_with_pool_address(
        self, adapter, mock_token_client, mock_wallet_client
    ):
        """Test get_balance with pool address (explicit chain_id)"""
        mock_wallet_client.get_token_balance_for_address = AsyncMock(
            return_value={"balance": 5000000}
        )
        mock_token_client.get_token_details = AsyncMock()

        success, balance = await adapter.get_balance(
            query="0xPoolAddress",
            wallet_address="0xWallet",
            chain_id=8453,
        )

        assert success
        assert balance == 5000000
        mock_wallet_client.get_token_balance_for_address.assert_called_once_with(
            wallet_address="0xWallet",
            query="0xPoolAddress",
            chain_id=8453,
        )
        mock_token_client.get_token_details.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_balance_token_not_found(self, adapter, mock_token_client):
        """Test get_balance when token is not found"""
        mock_token_client.get_token_details = AsyncMock(return_value=None)

        success, error = await adapter.get_balance(
            query="invalid-token",
            wallet_address="0xWallet",
        )

        assert success is False
        assert "Token not found" in str(error)

    @pytest.mark.asyncio
    async def test_get_balance_missing_chain_id(self, adapter, mock_token_client):
        """Test get_balance when chain_id cannot be resolved"""
        mock_token_client.get_token_details = AsyncMock(
            return_value={
                "token_id": "token-without-chain",
                "address": "0x123",
                "chain": {},
            }
        )

        success, error = await adapter.get_balance(
            query="token-without-chain",
            wallet_address="0xWallet",
        )

        assert success is False
        assert "missing a chain id" in str(error)
