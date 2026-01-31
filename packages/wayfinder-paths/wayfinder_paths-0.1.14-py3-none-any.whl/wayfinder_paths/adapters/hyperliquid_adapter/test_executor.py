"""Tests for LocalHyperliquidExecutor."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


class TestLocalHyperliquidExecutor:
    """Tests for LocalHyperliquidExecutor."""

    @pytest.fixture
    def mock_info_without_asset_to_coin(self):
        """Mock Info that only exposes coin_to_asset (no asset_to_coin)."""
        return SimpleNamespace(coin_to_asset={"HYPE": 7})

    @pytest.fixture
    def mock_exchange(self):
        """Mock Exchange client."""
        mock = MagicMock()
        mock.update_leverage.return_value = {"status": "ok"}
        mock.market_open.return_value = {"status": "ok"}
        return mock

    @pytest.mark.asyncio
    async def test_update_leverage_works_without_asset_to_coin(
        self, mock_info_without_asset_to_coin, mock_exchange
    ):
        """update_leverage should map asset_id->coin via coin_to_asset inversion."""
        dummy_wallet = SimpleNamespace(address="0xabc")

        with patch(
            "wayfinder_paths.adapters.hyperliquid_adapter.executor.Account"
        ) as mock_account:
            mock_account.from_key.return_value = dummy_wallet
            with patch(
                "wayfinder_paths.adapters.hyperliquid_adapter.executor.Info",
                return_value=mock_info_without_asset_to_coin,
            ):
                with patch(
                    "wayfinder_paths.adapters.hyperliquid_adapter.executor.Exchange",
                    return_value=mock_exchange,
                ):
                    from wayfinder_paths.adapters.hyperliquid_adapter.executor import (
                        LocalHyperliquidExecutor,
                    )

                    executor = LocalHyperliquidExecutor(
                        config={"strategy_wallet": {"private_key": "0x" + "11" * 32}}
                    )
                    resp = await executor.update_leverage(
                        asset_id=7,
                        leverage=1,
                        is_cross=True,
                        address="0xabc",
                    )

                    assert resp.get("status") == "ok"
                    mock_exchange.update_leverage.assert_called_once_with(
                        leverage=1,
                        name="HYPE",
                        is_cross=True,
                    )

    @pytest.mark.asyncio
    async def test_place_market_order_perp_works_without_asset_to_coin(
        self, mock_info_without_asset_to_coin, mock_exchange
    ):
        """place_market_order should map asset_id->coin via coin_to_asset inversion."""
        dummy_wallet = SimpleNamespace(address="0xabc")

        with patch(
            "wayfinder_paths.adapters.hyperliquid_adapter.executor.Account"
        ) as mock_account:
            mock_account.from_key.return_value = dummy_wallet
            with patch(
                "wayfinder_paths.adapters.hyperliquid_adapter.executor.Info",
                return_value=mock_info_without_asset_to_coin,
            ):
                with patch(
                    "wayfinder_paths.adapters.hyperliquid_adapter.executor.Exchange",
                    return_value=mock_exchange,
                ):
                    from wayfinder_paths.adapters.hyperliquid_adapter.executor import (
                        LocalHyperliquidExecutor,
                    )

                    executor = LocalHyperliquidExecutor(
                        config={"strategy_wallet": {"private_key": "0x" + "11" * 32}}
                    )
                    resp = await executor.place_market_order(
                        asset_id=7,
                        is_buy=True,
                        slippage=0.01,
                        size=1.0,
                        address="0xabc",
                        reduce_only=False,
                        cloid=MagicMock(),  # Avoid Cloid conversion
                    )

                    assert resp.get("status") == "ok"
                    mock_exchange.market_open.assert_called_once()
                    _, kwargs = mock_exchange.market_open.call_args
                    assert kwargs["name"] == "HYPE"
