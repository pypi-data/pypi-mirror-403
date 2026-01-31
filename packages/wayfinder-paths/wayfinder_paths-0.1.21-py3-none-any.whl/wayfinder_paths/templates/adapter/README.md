# Adapter Template

Adapters expose protocol-specific capabilities to strategies. They wrap one or more clients from `wayfinder_paths.core.clients`.

## Quick Start

1. Copy the template:
   ```bash
   cp -r wayfinder_paths/templates/adapter wayfinder_paths/adapters/my_adapter
   ```
2. Rename `MyAdapter` in `adapter.py` to match your adapter's purpose.
3. Set `adapter_type` to a unique identifier (e.g., `"MY_PROTOCOL"`).
4. Implement your public methods.
5. Add tests in `test_adapter.py`.

## Directory Structure

```
my_adapter/
├── adapter.py          # Adapter implementation
├── examples.json       # Example payloads (optional)
├── test_adapter.py     # Pytest tests
└── README.md           # Adapter documentation
```

## Adapter Structure

```python
from typing import Any

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter
from wayfinder_paths.core.clients.SomeClient import SomeClient


class MyAdapter(BaseAdapter):
    """Adapter for MyProtocol operations."""

    adapter_type = "MY_PROTOCOL"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__("my_adapter", config)
        self.client = SomeClient()

    async def connect(self) -> bool:
        """Optional: Establish connectivity."""
        return True

    async def do_something(self, param: str) -> tuple[bool, Any]:
        """
        Execute an operation.

        Args:
            param: Operation parameter

        Returns:
            Tuple of (success, data) where data is result or error message
        """
        try:
            result = await self.client.call(param)
            return (True, result)
        except Exception as e:
            self.logger.error(f"Operation failed: {e}")
            return (False, str(e))
```

## Key Conventions

1. **Return tuples**: All methods return `(success: bool, data: Any)`
2. **Adapter type**: Set `adapter_type` for registry lookups
3. **Config access**: Use `self.config` for configuration
4. **Logging**: Use `self.logger` for consistent logging
5. **Error handling**: Catch exceptions and return `(False, error_message)`

## BaseAdapter Interface

```python
class BaseAdapter(ABC):
    adapter_type: str | None = None

    def __init__(self, name: str, config: dict | None = None):
        self.name = name
        self.config = config or {}
        self.logger = logger.bind(adapter=self.__class__.__name__)

    async def connect(self) -> bool:
        """Establish connectivity (default: True)."""
        return True

    async def get_balance(self, asset: str) -> dict:
        """Get balance (raises NotImplementedError by default)."""
        raise NotImplementedError

    async def health_check(self) -> dict:
        """Check adapter health."""
        ...

    async def close(self) -> None:
        """Clean up resources."""
        pass
```

## Testing

Create `test_adapter.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from .adapter import MyAdapter


class TestMyAdapter:
    @pytest.fixture
    def adapter(self):
        return MyAdapter()

    @pytest.mark.asyncio
    async def test_do_something_success(self, adapter):
        with patch.object(adapter, "client") as mock_client:
            mock_client.call = AsyncMock(return_value={"result": "ok"})

            success, data = await adapter.do_something(param="test")

            assert success
            assert data["result"] == "ok"

    @pytest.mark.asyncio
    async def test_do_something_failure(self, adapter):
        with patch.object(adapter, "client") as mock_client:
            mock_client.call = AsyncMock(side_effect=Exception("API error"))

            success, data = await adapter.do_something(param="test")

            assert not success
            assert "error" in data.lower()
```

Run tests:

```bash
poetry run pytest wayfinder_paths/adapters/my_adapter/ -v
```

## Best Practices

- Keep adapters thin - business logic belongs in strategies
- Mock clients in tests, not adapters
- Document each public method with Args/Returns docstrings
- Use type hints for all parameters and return values
- Log errors with context for debugging
