"""
Live API tests for HyperliquidAdapter.

These tests hit the real Hyperliquid API to verify:
- Spot asset ID resolution (PURR, ETH, BTC, HYPE)
- Perp asset ID resolution
- API connectivity

Run with: pytest wayfinder_paths/adapters/hyperliquid_adapter/test_adapter_live.py -v
"""

import pytest

from wayfinder_paths.adapters.hyperliquid_adapter.adapter import HyperliquidAdapter


@pytest.fixture
def live_adapter():
    """Create adapter connected to real Hyperliquid API."""
    return HyperliquidAdapter(config={})


class TestSpotAssetIDs:
    """Test spot asset ID resolution against live API."""

    @pytest.mark.asyncio
    async def test_get_spot_assets_returns_dict(self, live_adapter):
        """Verify get_spot_assets returns a populated dict."""
        success, spot_assets = await live_adapter.get_spot_assets()

        assert success
        assert isinstance(spot_assets, dict)
        assert len(spot_assets) > 0

    @pytest.mark.asyncio
    async def test_purr_spot_asset_id(self, live_adapter):
        """PURR/USDC should be the first spot pair (index 0 + 10000 = 10000)."""
        success, spot_assets = await live_adapter.get_spot_assets()

        assert success
        assert "PURR/USDC" in spot_assets
        assert spot_assets["PURR/USDC"] == 10000

    @pytest.mark.asyncio
    async def test_hype_spot_asset_id(self, live_adapter):
        """HYPE/USDC should have asset ID 10107."""
        success, spot_assets = await live_adapter.get_spot_assets()

        assert success
        assert "HYPE/USDC" in spot_assets
        # HYPE is index 107, so asset_id = 10107
        assert spot_assets["HYPE/USDC"] == 10107

    @pytest.mark.asyncio
    async def test_eth_spot_exists(self, live_adapter):
        """ETH/USDC spot pair should exist."""
        success, spot_assets = await live_adapter.get_spot_assets()

        assert success
        # ETH spot may have different naming, check common variants
        eth_pairs = [k for k in spot_assets if "ETH" in k and "USDC" in k]
        assert len(eth_pairs) > 0, (
            f"No ETH/USDC spot found. Available: {list(spot_assets.keys())[:20]}"
        )

    @pytest.mark.asyncio
    async def test_btc_spot_exists(self, live_adapter):
        """BTC/USDC spot pair should exist."""
        success, spot_assets = await live_adapter.get_spot_assets()

        assert success
        # BTC spot may have different naming
        btc_pairs = [k for k in spot_assets if "BTC" in k and "USDC" in k]
        assert len(btc_pairs) > 0, (
            f"No BTC/USDC spot found. Available: {list(spot_assets.keys())[:20]}"
        )

    @pytest.mark.asyncio
    async def test_spot_asset_ids_are_valid(self, live_adapter):
        """All spot asset IDs should be >= 10000."""
        success, spot_assets = await live_adapter.get_spot_assets()

        assert success
        for name, asset_id in spot_assets.items():
            assert asset_id >= 10000, f"{name} has invalid asset_id {asset_id}"

    @pytest.mark.asyncio
    async def test_get_spot_asset_id_helper(self, live_adapter):
        """Test synchronous helper after cache is populated."""
        # First populate cache
        success, _ = await live_adapter.get_spot_assets()
        assert success

        # Now use sync helper
        purr_id = live_adapter.get_spot_asset_id("PURR", "USDC")
        assert purr_id == 10000

        hype_id = live_adapter.get_spot_asset_id("HYPE", "USDC")
        assert hype_id == 10107

        # Non-existent should return None
        fake_id = live_adapter.get_spot_asset_id("FAKECOIN", "USDC")
        assert fake_id is None


class TestPerpAssetIDs:
    """Test perp asset ID resolution against live API."""

    @pytest.mark.asyncio
    async def test_coin_to_asset_mapping(self, live_adapter):
        """Verify perp coin to asset mapping is populated."""
        coin_to_asset = live_adapter.coin_to_asset

        assert isinstance(coin_to_asset, dict)
        assert len(coin_to_asset) > 0

    @pytest.mark.asyncio
    async def test_btc_perp_asset_id(self, live_adapter):
        """BTC perp should be asset_id 0."""
        coin_to_asset = live_adapter.coin_to_asset

        assert "BTC" in coin_to_asset
        assert coin_to_asset["BTC"] == 0

    @pytest.mark.asyncio
    async def test_eth_perp_asset_id(self, live_adapter):
        """ETH perp should be asset_id 1."""
        coin_to_asset = live_adapter.coin_to_asset

        assert "ETH" in coin_to_asset
        assert coin_to_asset["ETH"] == 1

    @pytest.mark.asyncio
    async def test_hype_perp_exists(self, live_adapter):
        """HYPE perp should exist with valid asset_id."""
        coin_to_asset = live_adapter.coin_to_asset

        assert "HYPE" in coin_to_asset
        assert coin_to_asset["HYPE"] < 10000  # Perp IDs are < 10000


class TestSpotMetaStructure:
    """Test spot_meta API response structure."""

    @pytest.mark.asyncio
    async def test_spot_meta_has_tokens(self, live_adapter):
        """Spot meta should have tokens array."""
        success, spot_meta = await live_adapter.get_spot_meta()

        assert success
        assert "tokens" in spot_meta
        assert isinstance(spot_meta["tokens"], list)
        assert len(spot_meta["tokens"]) > 0

    @pytest.mark.asyncio
    async def test_spot_meta_has_universe(self, live_adapter):
        """Spot meta should have universe array with pairs."""
        success, spot_meta = await live_adapter.get_spot_meta()

        assert success
        assert "universe" in spot_meta
        assert isinstance(spot_meta["universe"], list)
        assert len(spot_meta["universe"]) > 0

    @pytest.mark.asyncio
    async def test_spot_universe_pair_structure(self, live_adapter):
        """Each spot universe entry should have tokens and index."""
        success, spot_meta = await live_adapter.get_spot_meta()

        assert success
        for pair in spot_meta["universe"][:5]:  # Check first 5
            assert "tokens" in pair, f"Missing tokens in {pair}"
            assert "index" in pair, f"Missing index in {pair}"
            assert len(pair["tokens"]) >= 2, f"Invalid tokens in {pair}"


class TestL2BookResolution:
    """Test that spot asset IDs work with L2 book API."""

    @pytest.mark.asyncio
    async def test_purr_spot_l2_book(self, live_adapter):
        """PURR/USDC (10000) should return valid L2 book."""
        success, book = await live_adapter.get_spot_l2_book(10000)

        assert success
        assert "levels" in book

    @pytest.mark.asyncio
    async def test_hype_spot_l2_book(self, live_adapter):
        """HYPE/USDC (10107) should return valid L2 book."""
        success, book = await live_adapter.get_spot_l2_book(10107)

        assert success
        assert "levels" in book


class TestSzDecimals:
    """Test size decimals resolution for spot assets."""

    @pytest.mark.asyncio
    async def test_spot_sz_decimals(self, live_adapter):
        """Spot assets should have valid sz_decimals."""
        # HYPE spot = 10107
        decimals = live_adapter.get_sz_decimals(10107)
        assert isinstance(decimals, int)
        assert decimals >= 0

    @pytest.mark.asyncio
    async def test_perp_sz_decimals(self, live_adapter):
        """Perp assets should have valid sz_decimals."""
        # BTC perp = 0
        decimals = live_adapter.get_sz_decimals(0)
        assert isinstance(decimals, int)
        assert decimals >= 0

        # ETH perp = 1
        decimals = live_adapter.get_sz_decimals(1)
        assert isinstance(decimals, int)
        assert decimals >= 0
