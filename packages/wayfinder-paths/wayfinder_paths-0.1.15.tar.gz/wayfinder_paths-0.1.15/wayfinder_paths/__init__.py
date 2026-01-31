"""Wayfinder Path - Trading strategies and adapters for automated strategy management"""

__version__ = "0.1.0"

# Re-export commonly used items for convenience
from wayfinder_paths.core import (
    BaseAdapter,
    LiquidationResult,
    StatusDict,
    StatusTuple,
    Strategy,
    StrategyJob,
)

__all__ = [
    "__version__",
    "BaseAdapter",
    "Strategy",
    "StatusDict",
    "StatusTuple",
    "StrategyJob",
]
