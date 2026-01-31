# Adapter Template

Adapters expose protocol-specific capabilities to strategies. They should be thin, async wrappers around one or more clients from `wayfinder_paths.core.clients`.

## Quick start

1. Copy the template:
   ```
   cp -r wayfinder_paths/templates/adapter wayfinder_paths/adapters/my_adapter
   ```
2. Rename `MyAdapter` in `adapter.py` to match your adapter's purpose.
3. Implement the public methods that provide your adapter's capabilities.
4. Add tests in `test_adapter.py`.

## Layout

```
my_adapter/
├── adapter.py          # Adapter implementation
├── examples.json       # Example payloads (optional but encouraged)
├── test_adapter.py     # Pytest smoke tests
└── README.md           # Adapter-specific notes
```

## Skeleton adapter

```python
from typing import Any

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.clients.PoolClient import PoolClient


class MyAdapter(BaseAdapter):
    adapter_type = "MY_ADAPTER"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__("my_adapter", config)
        self.pool_client = PoolClient()

    async def connect(self) -> bool:
        """Optional: prime caches / test connectivity."""
        return True

    async def get_pools(self, pool_ids: list[str]) -> tuple[bool, Any]:
        """Example capability that proxies PoolClient."""
        try:
            data = await self.pool_client.get_pools_by_ids(
                pool_ids=pool_ids
            )
            return (True, data)
        except Exception as exc:  # noqa: BLE001
            self.logger.error(f"Failed to fetch pools: {exc}")
            return (False, str(exc))
```

Your adapter should return `(success, payload)` tuples for every operation, just like the built-in adapters do.

## Testing

`test_adapter.py` should cover the public methods you expose. Patch out remote clients with `unittest.mock.AsyncMock` so tests run offline.

```python
import pytest
from unittest.mock import AsyncMock, patch

from wayfinder_paths.adapters.my_adapter.adapter import MyAdapter


@pytest.mark.asyncio
async def test_get_pools():
    with patch(
        "wayfinder_paths.adapters.my_adapter.adapter.PoolClient",
        return_value=AsyncMock(
            get_pools_by_ids=AsyncMock(return_value={"pools": []})
        ),
    ):
        adapter = MyAdapter(config={})
        success, data = await adapter.get_pools(["pool-1"])
        assert success
        assert "pools" in data
```

## Best practices

- Keep adapters stateless and idempotent—strategies may reuse instances across operations.
- Use `self.logger` for contextual logging (BaseAdapter has already bound the adapter name).
- Return `(success, payload)` tuples consistently for all operations.
- Raise `NotImplementedError` for capabilities you intentionally do not support yet.
