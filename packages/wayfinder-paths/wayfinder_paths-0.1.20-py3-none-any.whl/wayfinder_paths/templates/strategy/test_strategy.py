import sys
from pathlib import Path

# TODO: Replace MyStrategy with your actual strategy class name
from wayfinder_paths.strategies.your_strategy.strategy import (
    MyStrategy,  # noqa: E402
)

# Ensure wayfinder-paths is on path for tests.test_utils import
# This is a workaround until conftest loading order is resolved
_wayfinder_path_dir = Path(__file__).parent.parent.parent.parent.resolve()
_wayfinder_path_str = str(_wayfinder_path_dir)
if _wayfinder_path_str not in sys.path:
    sys.path.insert(0, _wayfinder_path_str)
elif sys.path.index(_wayfinder_path_str) > 0:
    # Move to front to take precedence
    sys.path.remove(_wayfinder_path_str)
    sys.path.insert(0, _wayfinder_path_str)

import pytest  # noqa: E402

try:
    from tests.test_utils import get_canonical_examples, load_strategy_examples
except ImportError:
    # Fallback if path setup didn't work
    import importlib.util

    test_utils_path = Path(_wayfinder_path_dir) / "tests" / "test_utils.py"
    spec = importlib.util.spec_from_file_location("tests.test_utils", test_utils_path)
    test_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_utils)
    get_canonical_examples = test_utils.get_canonical_examples
    load_strategy_examples = test_utils.load_strategy_examples


@pytest.fixture
def strategy():
    mock_config = {
        "main_wallet": {"address": "0x1234567890123456789012345678901234567890"},
        "strategy_wallet": {"address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"},
    }

    s = MyStrategy(
        config=mock_config,
        main_wallet=mock_config["main_wallet"],
        strategy_wallet=mock_config["strategy_wallet"],
    )

    # TODO: Add mocking for your adapters here if needed
    # Example for balance_adapter:
    # if hasattr(s, "balance_adapter") and s.balance_adapter:
    #     usdc_balance_mock = AsyncMock(return_value=(True, 60000000))
    #     gas_balance_mock = AsyncMock(return_value=(True, 2000000000000000))
    #
    #     def get_balance_side_effect(query, wallet_address, **kwargs):
    #         token_id = query if isinstance(query, str) else (query or {}).get("token_id")
    #         if token_id == "usd-coin-base" or token_id == "usd-coin":
    #         elif token_id == "ethereum-base" or token_id == "ethereum":
    #
    #     s.balance_adapter.get_balance = AsyncMock(
    #         side_effect=get_balance_side_effect
    #     )

    # Example for token_adapter:
    # if hasattr(s, "token_adapter") and s.token_adapter:
    #     default_token = {
    #         "id": "usd-coin-base",
    #         "symbol": "USDC",
    #         "name": "USD Coin",
    #         "decimals": 6,
    #         "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    #         "chain": {"code": "base", "id": 8453, "name": "Base"},
    #     }
    #     s.token_adapter.get_token = AsyncMock(return_value=(True, default_token))
    #     s.token_adapter.get_gas_token = AsyncMock(return_value=(True, default_token))

    # Example for transaction adapters:
    # if hasattr(s, "tx_adapter") and s.tx_adapter:
    #     s.tx_adapter.move_from_main_wallet_to_strategy_wallet = AsyncMock(
    #     )
    #     s.tx_adapter.move_from_strategy_wallet_to_main_wallet = AsyncMock(
    #     )

    # Example for ledger_adapter:
    # if hasattr(s, "ledger_adapter") and s.ledger_adapter:
    #     s.ledger_adapter.get_strategy_net_deposit = AsyncMock(
    #     )
    #     s.ledger_adapter.get_strategy_transactions = AsyncMock(
    #     )

    return s


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_smoke(strategy):
    examples = load_strategy_examples(Path(__file__))
    smoke_data = examples["smoke"]

    st = await strategy.status()
    assert isinstance(st, dict)
    assert "portfolio_value" in st or "net_deposit" in st or "strategy_status" in st

    deposit_params = smoke_data.get("deposit", {})
    ok, msg = await strategy.deposit(**deposit_params)
    assert isinstance(ok, bool)
    assert isinstance(msg, str)

    ok, msg = await strategy.update(**smoke_data.get("update", {}))
    assert isinstance(ok, bool)

    ok, msg = await strategy.withdraw(**smoke_data.get("withdraw", {}))
    assert isinstance(ok, bool)


@pytest.mark.asyncio
async def test_canonical_usage(strategy):
    examples = load_strategy_examples(Path(__file__))
    canonical = get_canonical_examples(examples)

    for example_name, example_data in canonical.items():
        if "deposit" in example_data:
            deposit_params = example_data.get("deposit", {})
            ok, _ = await strategy.deposit(**deposit_params)
            assert ok, f"Canonical example '{example_name}' deposit failed"

        if "update" in example_data:
            ok, msg = await strategy.update()
            assert ok, f"Canonical example '{example_name}' update failed: {msg}"

        if "status" in example_data:
            st = await strategy.status()
            assert isinstance(st, dict), (
                f"Canonical example '{example_name}' status failed"
            )


@pytest.mark.asyncio
async def test_error_cases(strategy):
    examples = load_strategy_examples(Path(__file__))

    for example_name, example_data in examples.items():
        if isinstance(example_data, dict) and "expect" in example_data:
            expect = example_data.get("expect", {})

            if "deposit" in example_data:
                deposit_params = example_data.get("deposit", {})
                ok, _ = await strategy.deposit(**deposit_params)

                if expect.get("success") is False:
                    assert ok is False, (
                        f"Expected {example_name} deposit to fail but it succeeded"
                    )
                elif expect.get("success") is True:
                    assert ok is True, (
                        f"Expected {example_name} deposit to succeed but it failed"
                    )

            if "update" in example_data:
                ok, _ = await strategy.update()
                if "success" in expect:
                    expected_success = expect.get("success")
                    assert ok == expected_success, (
                        f"Expected {example_name} update to "
                        f"{'succeed' if expected_success else 'fail'} but got opposite"
                    )
