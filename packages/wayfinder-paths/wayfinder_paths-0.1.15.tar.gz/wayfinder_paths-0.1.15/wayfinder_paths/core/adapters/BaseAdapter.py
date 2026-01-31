from __future__ import annotations

from abc import ABC
from typing import Any

from loguru import logger


class BaseAdapter(ABC):
    """Base adapter class for exchange/protocol integrations"""

    adapter_type: str | None = None

    def __init__(self, name: str, config: dict[str, Any] | None = None):
        self.name = name
        self.config = config or {}
        self.logger = logger.bind(adapter=self.__class__.__name__)

    async def connect(self) -> bool:
        """Optional: establish connectivity. Defaults to True."""
        return True

    async def get_balance(self, asset: str) -> dict[str, Any]:
        """
        Get balance for an asset.
        Optional method that can be overridden by subclasses.

        Args:
            asset: Asset identifier (token address, token ID, etc.).

        Returns:
            Dictionary containing balance information.

        Raises:
            ValueError: If asset is empty or invalid.
            NotImplementedError: If this adapter does not support balance queries.
        """
        if not asset or not isinstance(asset, str) or not asset.strip():
            raise ValueError("asset must be a non-empty string")
        raise NotImplementedError(
            f"get_balance not supported by {self.__class__.__name__}"
        )

    async def health_check(self) -> dict[str, Any]:
        """
        Check adapter health and connectivity
        Returns: Health status dictionary
        """
        try:
            connected = await self.connect()
            return {
                "status": "healthy" if connected else "unhealthy",
                "connected": connected,
                "adapter": self.adapter_type or self.__class__.__name__,
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "adapter": self.adapter_type or self.__class__.__name__,
            }

    async def close(self) -> None:
        """Clean up resources"""
        pass
