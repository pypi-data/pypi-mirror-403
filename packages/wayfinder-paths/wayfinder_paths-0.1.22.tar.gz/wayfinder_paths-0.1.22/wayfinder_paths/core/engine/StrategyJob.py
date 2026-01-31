import asyncio
from typing import Any

from loguru import logger

from wayfinder_paths.core.clients.ClientManager import ClientManager
from wayfinder_paths.core.config import StrategyJobConfig
from wayfinder_paths.core.strategies.Strategy import Strategy


class StrategyJob:
    def __init__(
        self,
        strategy: Strategy,
        config: StrategyJobConfig,
        clients: dict[str, Any] | None = None,
        skip_auth: bool = False,
    ):
        self.strategy = strategy
        self.config = config

        self.job_id = strategy.name or "unknown"
        self.clients = ClientManager(clients=clients, skip_auth=skip_auth)

    def _setup_strategy(self):
        if not self.strategy:
            raise ValueError("No strategy provided to StrategyJob")

        self.strategy.log = self.log

    async def setup(self):
        self._setup_strategy()

        # Ensure API key is set for API calls
        # All clients inherit from WayfinderClient and have _ensure_api_key()
        if not self.clients._skip_auth:
            # Ensure API key on any client (they all share the same method)
            token_client = self.clients.token
            if token_client:
                token_client._ensure_api_key()

        existing_cfg = dict(getattr(self.strategy, "config", {}) or {})
        strategy_cfg = dict(self.config.strategy_config or {})
        merged_cfg = {**strategy_cfg, **existing_cfg}
        self.strategy.config = merged_cfg
        self.strategy.clients = self.clients
        await self.strategy.setup()

    async def execute_strategy(self, action: str, **kwargs) -> dict[str, Any]:
        try:
            if action == "deposit":
                result = await self.strategy.deposit(**kwargs)
            elif action == "withdraw":
                result = await self.strategy.withdraw(**kwargs)
            elif action == "update":
                result = await self.strategy.update()
            elif action == "status":
                result = await self.strategy.status()
            elif action == "exit":
                result = await self.strategy.exit(**kwargs)
            elif action == "partial_liquidate":
                usd_value = kwargs.get("usd_value")
                if usd_value is None:
                    result = (
                        False,
                        "usd_value parameter is required for partial_liquidate",
                    )
                else:
                    result = await self.strategy.partial_liquidate(usd_value)
            else:
                result = {"success": False, "message": f"Unknown action: {action}"}

            await self.log(f"Strategy action '{action}' completed: {result}")
            return result

        except Exception as e:
            error_msg = f"Strategy action '{action}' failed: {str(e)}"
            await self.log(error_msg)
            await self.handle_error({"error": str(e), "action": action})
            return {"success": False, "error": str(e)}

    async def run_continuous(self, interval_seconds: int | None = None):
        interval = interval_seconds or self.config.system.update_interval
        logger.info(
            f"Starting continuous execution for strategy: {self.strategy.name} with interval {interval}s"
        )

        while True:
            try:
                await self.execute_strategy("update")
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Continuous execution cancelled")
                break
            except Exception as e:
                logger.error(f"Error in continuous execution: {str(e)}")
                await asyncio.sleep(interval)

    async def log(self, msg: str):
        logger.info(f"Job {self.job_id}: {msg}")

    async def handle_error(self, error_data: dict[str, Any]) -> None:
        pass

    async def stop(self):
        if hasattr(self.strategy, "stop"):
            await self.strategy.stop()

        logger.info(f"Strategy job {self.job_id} stopped")
