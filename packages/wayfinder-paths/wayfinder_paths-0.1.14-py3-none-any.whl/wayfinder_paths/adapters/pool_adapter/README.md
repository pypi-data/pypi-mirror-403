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

### Get pools (all or filtered)

Pass at least `chain_id` when fetching all pools (e.g. `chain_id=8453` for Base):

```python
success, data = await adapter.get_pools(chain_id=8453)
if success:
    matches = data.get("matches", [])
    for match in matches:
        if match.get("stablecoin"):
            print(f"Pool {match.get('id')} - APY: {match.get('apy')}%")
else:
    print(f"Error: {data}")
```

Optional: `project="lido"` to filter by project.

## API Endpoints

The adapter uses the Wayfinder API:

- `GET /v1/blockchain/pools/?chain_id=1&project=lido` - List pools (filter by chain_id, optional project)
- `POST /v1/blockchain/pools/` - Get pools by IDs (body: `{"pool_ids": ["id1", "id2"]}`)

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
