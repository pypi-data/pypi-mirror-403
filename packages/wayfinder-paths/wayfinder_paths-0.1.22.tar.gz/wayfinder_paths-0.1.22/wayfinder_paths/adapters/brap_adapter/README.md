# BRAP Adapter

Adapter for cross-chain swaps and bridges via the BRAP (Bridge/Router/Adapter Protocol).

- **Type**: `BRAP`
- **Module**: `wayfinder_paths.adapters.brap_adapter.adapter.BRAPAdapter`

## Overview

The BRAPAdapter provides:
- Cross-chain swap quotes
- Bridge operation quotes
- Route comparison and optimization
- Fee calculations
- Swap execution

## Usage

```python
from wayfinder_paths.adapters.brap_adapter.adapter import BRAPAdapter

adapter = BRAPAdapter()
```

## Methods

### get_swap_quote

Get quotes for a cross-chain swap.

```python
success, data = await adapter.get_swap_quote(
    from_token_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    to_token_address="0x...",
    from_chain_id=8453,
    to_chain_id=1,
    from_address="0x...",
    to_address="0x...",
    amount="1000000000",  # Raw amount
    slippage=0.01,        # 1%
)
if success:
    best_quote = data.get("quotes", {}).get("best_quote", {})
    print(f"Output: {best_quote.get('output_amount')}")
```

### get_best_quote

Get the best quote for a swap.

```python
success, data = await adapter.get_best_quote(
    from_token_address="0x...",
    to_token_address="0x...",
    from_chain_id=8453,
    to_chain_id=1,
    from_address="0x...",
    to_address="0x...",
    amount="1000000000",
)
```

### compare_routes

Compare available routes for a swap.

```python
success, data = await adapter.compare_routes(
    from_token_address="0x...",
    to_token_address="0x...",
    from_chain_id=8453,
    to_chain_id=1,
    amount="1000000000",
)
if success:
    print(f"Total routes: {data.get('total_routes')}")
    for route in data.get("all_routes", []):
        print(f"Output: {route.get('output_amount')}, Fee: {route.get('total_fee')}")
```

### calculate_swap_fees

Calculate fees for a swap operation.

```python
success, data = await adapter.calculate_swap_fees(
    from_token_address="0x...",
    to_token_address="0x...",
    from_chain_id=8453,
    to_chain_id=1,
    amount="1000000000",
    slippage=0.01,
)
if success:
    print(f"Gas fee: {data.get('gas_fee')}")
    print(f"Bridge fee: {data.get('bridge_fee')}")
    print(f"Total fee: {data.get('total_fee')}")
```

### validate_swap_parameters

Validate swap parameters before execution.

```python
success, data = await adapter.validate_swap_parameters(
    from_token_address="0x...",
    to_token_address="0x...",
    from_chain_id=8453,
    to_chain_id=1,
    amount="1000000000",
)
if success and data.get("valid"):
    print("Parameters are valid")
```

## Dependencies

- `BRAPClient` - Low-level API client

## Testing

```bash
poetry run pytest wayfinder_paths/adapters/brap_adapter/ -v
```
