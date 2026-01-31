ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

# Chain code to EVM chain id mapping
CHAIN_CODE_TO_ID = {
    "base": 8453,
    "arbitrum": 42161,
    "arbitrum-one": 42161,
    "ethereum": 1,
    "mainnet": 1,
    "hyperevm": 999,
}

# Gas/defaults
DEFAULT_NATIVE_GAS_UNITS = 21000
# Fallback gas limit used only when RPC gas estimation fails for non-revert reasons.
# Must be high enough for typical DeFi interactions (lending, swaps, etc.).
GAS_BUFFER_MULTIPLIER = 1.1
ONE_GWEI = 1_000_000_000
DEFAULT_SLIPPAGE = 0.005

# Timeout constants (seconds)
# Base L2 (and some RPC providers) can occasionally take >2 minutes to index/return receipts,
# even if the transaction is eventually mined. A longer timeout reduces false negatives that
# can lead to unsafe retry behavior (nonce gaps, duplicate swaps, etc.).
DEFAULT_HTTP_TIMEOUT = 30.0  # HTTP client timeout

# Adapter type identifiers
ADAPTER_BALANCE = "BALANCE"
ADAPTER_BRAP = "BRAP"
ADAPTER_MOONWELL = "MOONWELL"
ADAPTER_HYPERLIQUID = "HYPERLIQUID"
ADAPTER_POOL = "POOL"
ADAPTER_TOKEN = "TOKEN"
ADAPTER_LEDGER = "LEDGER"
ADAPTER_HYPERLEND = "HYPERLEND"

# Pagination defaults
DEFAULT_PAGINATION_LIMIT = 50
