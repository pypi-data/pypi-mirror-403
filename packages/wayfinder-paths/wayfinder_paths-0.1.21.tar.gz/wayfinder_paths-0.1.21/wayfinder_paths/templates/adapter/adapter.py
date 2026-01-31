from typing import Any

from wayfinder_paths.core.adapters.BaseAdapter import BaseAdapter


class MyAdapter(BaseAdapter):
    adapter_type: str = "MY_ADAPTER"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__("my_adapter", config)

    async def connect(self) -> bool:
        return True

    async def example_operation(self, **kwargs) -> tuple[bool, str]:
        return (True, "example.op executed")
