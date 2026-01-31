from wayfinder_paths.core.strategies.Strategy import StatusDict, StatusTuple, Strategy


class MyStrategy(Strategy):
    name = "My Strategy"
    description = "Short description of what the strategy does."
    summary = "One-line summary for discovery."

    def __init__(self):
        super().__init__()

    async def setup(self):
        return None

    async def deposit(
        self, main_token_amount: float, gas_token_amount: float
    ) -> StatusTuple:
        return (True, "Deposit successful")

    async def withdraw(self, amount: float | None = None) -> StatusTuple:
        return await super().withdraw(amount=amount)

    async def update(self) -> StatusTuple:
        return (True, "Update successful")

    async def _status(self) -> StatusDict:
        return {
            "portfolio_value": 0.0,
            "net_deposit": 0.0,
            "strategy_status": {},
        }

    @staticmethod
    def policies() -> list[str]:
        return []
