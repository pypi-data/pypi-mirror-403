import pytest

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.strategies.Strategy import StatusDict, StatusTuple, Strategy


class FakeAdapter(BaseAdapter):
    adapter_type = "FAKE"

    async def connect(self) -> bool:
        return True

    async def get_balance(self, asset: str):
        return {"asset": asset, "amount": 100}


class FakeLedgerAdapter(BaseAdapter):
    adapter_type = "LEDGER"

    async def connect(self) -> bool:
        return True

    async def record_strategy_snapshot(self, **kwargs):
        pass


class FakeStrategy(Strategy):
    name = "Fake Strategy"

    async def deposit(self, amount: float = 0) -> StatusTuple:
        return (True, "deposited")

    async def update(self) -> StatusTuple:
        return (True, "updated")

    async def withdraw(self, amount: float = 0) -> StatusTuple:
        return (True, "withdrew")

    async def _status(self) -> StatusDict:
        return {"total_earned": 0.0, "strategy_status": {"ok": True}}

    @staticmethod
    def policy() -> str:
        return "wallet.id == 'TEST'"


@pytest.mark.asyncio
async def test_smoke_deposit_update_withdraw_status():
    s = FakeStrategy(
        config={
            "strategy_wallet": {"address": "0x1234567890123456789012345678901234567890"}
        }
    )
    s.register_adapters([FakeAdapter("fake")])
    s.ledger_adapter = FakeLedgerAdapter("ledger")
    ok, msg = await s.deposit(amount=1)
    assert ok
    ok, msg = await s.update()
    assert ok
    ok, msg = await s.withdraw(amount=1)
    assert ok
    st = await s.status()
    assert "total_earned" in st
