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
    def mock_web3_service(self):
        """Mock TokenClient for testing"""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def adapter(self, mock_wallet_client, mock_token_client, mock_web3_service):
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
            return BalanceAdapter(config={}, web3_service=mock_web3_service)

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
