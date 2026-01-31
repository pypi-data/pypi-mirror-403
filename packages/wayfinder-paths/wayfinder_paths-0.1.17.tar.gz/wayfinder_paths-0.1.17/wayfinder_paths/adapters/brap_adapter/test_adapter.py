from unittest.mock import AsyncMock

import pytest

from wayfinder_paths.adapters.brap_adapter.adapter import BRAPAdapter


class TestBRAPAdapter:
    """Test cases for BRAPAdapter"""

    @pytest.fixture
    def mock_brap_client(self):
        """Mock BRAPClient for testing"""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def adapter(self, mock_brap_client):
        """Create a BRAPAdapter instance with mocked client for testing"""
        adapter = BRAPAdapter()
        adapter.brap_client = mock_brap_client
        return adapter

    @pytest.mark.asyncio
    async def test_get_swap_quote_success(self, adapter, mock_brap_client):
        """Test successful swap quote retrieval"""
        mock_response = {
            "quotes": [
                {
                    "provider": "enso",
                    "input_amount": 1000000000000000000,
                    "output_amount": 995000000000000000,
                    "calldata": {
                        "data": "0x",
                        "to": "0x",
                        "from_address": "0x",
                        "value": "0",
                        "chainId": 8453,
                    },
                    "fee_estimate": {"fee_total_usd": 0.008, "fee_breakdown": []},
                }
            ],
            "best_quote": {
                "provider": "enso",
                "input_amount": 1000000000000000000,
                "output_amount": 995000000000000000,
                "calldata": {
                    "data": "0x",
                    "to": "0x",
                    "from_address": "0x",
                    "value": "0",
                    "chainId": 8453,
                },
                "fee_estimate": {"fee_total_usd": 0.008, "fee_breakdown": []},
            },
        }
        mock_brap_client.get_quote = AsyncMock(return_value=mock_response)

        success, data = await adapter.get_swap_quote(
            from_token_address="0x" + "a" * 40,
            to_token_address="0x" + "b" * 40,
            from_chain_id=8453,
            to_chain_id=1,
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0x1234567890123456789012345678901234567890",
            amount="1000000000000000000",
            slippage=0.01,
        )

        assert success
        assert data == mock_response
        mock_brap_client.get_quote.assert_called_once_with(
            from_token="0x" + "a" * 40,
            to_token="0x" + "b" * 40,
            from_chain=8453,
            to_chain=1,
            from_wallet="0x1234567890123456789012345678901234567890",
            from_amount="1000000000000000000",
        )

    @pytest.mark.asyncio
    async def test_get_best_quote_success(self, adapter, mock_brap_client):
        """Test successful best quote retrieval"""
        mock_response = {
            "quotes": [],
            "best_quote": {
                "provider": "enso",
                "input_amount": 1000000000000000000,
                "output_amount": 995000000000000000,
                "calldata": {
                    "data": "0x",
                    "to": "0x",
                    "from_address": "0x",
                    "value": "0",
                    "chainId": 8453,
                },
                "fee_estimate": {"fee_total_usd": 0.008, "fee_breakdown": []},
            },
        }
        mock_brap_client.get_quote = AsyncMock(return_value=mock_response)

        success, data = await adapter.get_best_quote(
            from_token_address="0x" + "a" * 40,
            to_token_address="0x" + "b" * 40,
            from_chain_id=8453,
            to_chain_id=1,
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0x1234567890123456789012345678901234567890",
            amount="1000000000000000000",
        )

        assert success
        assert data["input_amount"] == 1000000000000000000
        assert data["output_amount"] == 995000000000000000

    @pytest.mark.asyncio
    async def test_get_best_quote_no_quotes(self, adapter, mock_brap_client):
        """Test best quote retrieval when no quotes available"""
        mock_response = {"quotes": [], "best_quote": None}
        mock_brap_client.get_quote = AsyncMock(return_value=mock_response)

        success, data = await adapter.get_best_quote(
            from_token_address="0x" + "a" * 40,
            to_token_address="0x" + "b" * 40,
            from_chain_id=8453,
            to_chain_id=1,
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0x1234567890123456789012345678901234567890",
            amount="1000000000000000000",
        )

        assert success is False
        assert "No quotes available" in data

    @pytest.mark.asyncio
    async def test_calculate_swap_fees_success(self, adapter, mock_brap_client):
        """Test successful swap fee calculation"""
        mock_quote_response = {
            "quotes": [],
            "best_quote": {
                "provider": "enso",
                "input_amount": 1000000000000000000,
                "output_amount": 995000000000000000,
                "gas_estimate": 5000000000000000,
                "quote": {"priceImpact": 5},
                "fee_estimate": {
                    "fee_total_usd": 0.008,
                    "fee_breakdown": [],
                },
                "calldata": {
                    "data": "0x",
                    "to": "0x",
                    "from_address": "0x",
                    "value": "0",
                    "chainId": 8453,
                },
            },
        }
        mock_brap_client.get_quote = AsyncMock(return_value=mock_quote_response)

        success, data = await adapter.calculate_swap_fees(
            from_token_address="0x" + "a" * 40,
            to_token_address="0x" + "b" * 40,
            from_chain_id=8453,
            to_chain_id=1,
            amount="1000000000000000000",
            slippage=0.01,
        )

        assert success
        assert data["input_amount"] == 1000000000000000000
        assert data["output_amount"] == 995000000000000000
        assert data["gas_fee"] == 5000000000000000
        assert data["total_fee"] == 0.008

    @pytest.mark.asyncio
    async def test_compare_routes_success(self, adapter, mock_brap_client):
        """Test successful route comparison"""
        mock_response = {
            "quotes": [
                {
                    "provider": "enso",
                    "output_amount": 995000000000000000,
                    "fee_estimate": {"fee_total_usd": 0.008, "fee_breakdown": []},
                    "calldata": {
                        "data": "0x",
                        "to": "0x",
                        "from_address": "0x",
                        "value": "0",
                        "chainId": 8453,
                    },
                },
                {
                    "provider": "enso",
                    "output_amount": 992000000000000000,
                    "fee_estimate": {"fee_total_usd": 0.012, "fee_breakdown": []},
                    "calldata": {
                        "data": "0x",
                        "to": "0x",
                        "from_address": "0x",
                        "value": "0",
                        "chainId": 8453,
                    },
                },
            ],
            "best_quote": {
                "provider": "enso",
                "output_amount": 995000000000000000,
                "fee_estimate": {"fee_total_usd": 0.008, "fee_breakdown": []},
                "calldata": {
                    "data": "0x",
                    "to": "0x",
                    "from_address": "0x",
                    "value": "0",
                    "chainId": 8453,
                },
            },
        }
        mock_brap_client.get_quote = AsyncMock(return_value=mock_response)

        success, data = await adapter.compare_routes(
            from_token_address="0x" + "a" * 40,
            to_token_address="0x" + "b" * 40,
            from_chain_id=8453,
            to_chain_id=1,
            amount="1000000000000000000",
        )

        assert success
        assert data["total_routes"] == 2
        assert len(data["all_routes"]) == 2
        assert data["best_route"]["output_amount"] == 995000000000000000

    @pytest.mark.asyncio
    async def test_estimate_gas_cost_success(self, adapter):
        """Test successful gas cost estimation"""
        success, data = await adapter.estimate_gas_cost(
            from_chain_id=8453, to_chain_id=1, operation_type="swap"
        )

        assert success
        assert data["from_chain"] == "base"
        assert data["to_chain"] == "ethereum"
        assert data["from_gas_estimate"] == 100000
        assert data["to_gas_estimate"] == 150000
        assert data["total_operations"] == 2

    @pytest.mark.asyncio
    async def test_validate_swap_parameters_success(self, adapter, mock_brap_client):
        """Test successful swap parameter validation"""
        mock_quote_response = {
            "quotes": [],
            "best_quote": {
                "output_amount": 995000000000000000,
                "calldata": {
                    "data": "0x",
                    "to": "0x",
                    "from_address": "0x",
                    "value": "0",
                    "chainId": 8453,
                },
                "fee_estimate": {"fee_total_usd": 0.008, "fee_breakdown": []},
            },
        }
        mock_brap_client.get_quote = AsyncMock(return_value=mock_quote_response)

        success, data = await adapter.validate_swap_parameters(
            from_token_address="0x" + "a" * 40,
            to_token_address="0x" + "b" * 40,
            from_chain_id=8453,
            to_chain_id=1,
            amount="1000000000000000000",
        )

        assert success
        assert data["valid"] is True
        assert data["quote_available"] is True
        assert data["estimated_output"] == "995000000000000000"

    @pytest.mark.asyncio
    async def test_validate_swap_parameters_invalid_address(self, adapter):
        """Test swap parameter validation with invalid address"""
        success, data = await adapter.validate_swap_parameters(
            from_token_address="invalid_address",
            to_token_address="0xB1c97a44F7552d9Dd5e5e5e5e5e5e5e5e5e5e5e5e5e",
            from_chain_id=8453,
            to_chain_id=1,
            amount="1000000000000000000",
        )

        assert success is False
        assert data["valid"] is False
        assert "Invalid from_token_address" in data["errors"]

    @pytest.mark.asyncio
    async def test_validate_swap_parameters_invalid_amount(self, adapter):
        """Test swap parameter validation with invalid amount"""
        success, data = await adapter.validate_swap_parameters(
            from_token_address="0x" + "a" * 40,
            to_token_address="0x" + "b" * 40,
            from_chain_id=8453,
            to_chain_id=1,
            amount="invalid_amount",
        )

        assert success is False
        assert data["valid"] is False
        assert "Invalid amount format" in data["errors"]

    @pytest.mark.asyncio
    async def test_get_swap_quote_failure(self, adapter, mock_brap_client):
        """Test swap quote retrieval failure"""
        mock_brap_client.get_quote = AsyncMock(side_effect=Exception("API Error"))

        success, data = await adapter.get_swap_quote(
            from_token_address="0x" + "a" * 40,
            to_token_address="0x" + "b" * 40,
            from_chain_id=8453,
            to_chain_id=1,
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0x1234567890123456789012345678901234567890",
            amount="1000000000000000000",
        )

        assert success is False
        assert "API Error" in data

    def test_adapter_type(self, adapter):
        """Test adapter has adapter_type"""
        assert adapter.adapter_type == "BRAP"
