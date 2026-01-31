# Pool Adapter

A Wayfinder adapter that provides high-level operations for DeFi pool data and analytics. This adapter wraps the `PoolClient` to offer strategy-friendly methods for discovering, analyzing, and filtering yield opportunities.

## Capabilities

- `pool.read`: Read pool information and metadata
- `pool.analytics`: Get comprehensive pool analytics
- `pool.discovery`: Find and search pools
- `llama.data`: Access Llama protocol data
- `pool.reports`: Get pool reports and analytics

## Configuration

The adapter uses the PoolClient which automatically handles authentication and API configuration through the Wayfinder settings. No additional configuration is required.

The PoolClient will automatically:

- Use the WAYFINDER_API_URL from settings
- Handle authentication via config.json
- Manage token refresh and retry logic

## Usage

### Initialize the Adapter

```python
from wayfinder_paths.adapters.pool_adapter.adapter import PoolAdapter

# No configuration needed - uses PoolClient with automatic settings
adapter = PoolAdapter()
```

### Get Pools by IDs

```python
success, data = await adapter.get_pools_by_ids(
    pool_ids=["pool-123", "pool-456"]
)
if success:
    pools = data.get("pools", [])
    print(f"Found {len(pools)} pools")
else:
    print(f"Error: {data}")
```

### Get Llama Matches

```python
success, data = await adapter.get_pools()
if success:
    matches = data.get("matches", [])
    print(f"Found {len(matches)} Llama matches")
    for match in matches:
        if match.get("stablecoin"):
            print(f"Stablecoin pool: {match.get('id')} - APY: {match.get('apy')}%")
else:
    print(f"Error: {data}")
```

## Advanced Usage

## API Endpoints

The adapter uses the following Wayfinder API endpoints:

- `GET /api/v1/public/pools/?pool_ids=X` - Get pools by IDs
- `GET /api/v1/public/pools/` - Get all pools
- `GET /api/v1/public/pools/llama/matches/` - Get Llama matches
- `GET /api/v1/public/pools/llama/reports/` - Get Llama reports

## Error Handling

All methods return a tuple of `(success: bool, data: Any)` where:

- `success` is `True` if the operation succeeded
- `data` contains the response data on success or error message on failure

## Testing

Run the adapter tests:

```bash
pytest wayfinder_paths/adapters/pool_adapter/test_adapter.py -v
```

## Dependencies

- `PoolClient` - Low-level API client for pool operations
- `BaseAdapter` - Base adapter class with common functionality
