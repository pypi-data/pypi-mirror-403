from typing import Any

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.clients.PoolClient import (
    LlamaMatch,
    PoolClient,
    PoolList,
)


class PoolAdapter(BaseAdapter):
    """
    Pool adapter for DeFi pool data and analytics operations.

    Provides high-level operations for:
    - Fetching pool information and metadata
    - Getting pool analytics and reports
    - Accessing Llama protocol data
    - Pool discovery and filtering
    """

    adapter_type: str = "POOL"

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        pool_client: PoolClient | None = None,
    ):
        super().__init__("pool_adapter", config)
        self.pool_client = pool_client or PoolClient()

    async def get_pools_by_ids(
        self, pool_ids: list[str]
    ) -> tuple[bool, PoolList | str]:
        """
        Get pool information by pool IDs.

        Args:
            pool_ids: List of pool identifiers

        Returns:
            Tuple of (success, data) where data is pool information or error message
        """
        try:
            data = await self.pool_client.get_pools_by_ids(pool_ids=pool_ids)
            return (True, data)
        except Exception as e:
            self.logger.error(f"Error fetching pools by IDs: {e}")
            return (False, str(e))

    async def get_pools(self) -> tuple[bool, dict[str, LlamaMatch] | str]:
        """
        Get Llama protocol matches for pools.

        Returns:
            Tuple of (success, data) where data is Llama matches or error message
        """
        try:
            data = await self.pool_client.get_pools()
            return (True, data)
        except Exception as e:
            self.logger.error(f"Error fetching Llama matches: {e}")
            return (False, str(e))
