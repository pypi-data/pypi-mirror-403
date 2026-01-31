"""
Moonwell ABI constants for smart contract interactions.

This module contains ABI definitions for Moonwell protocol contracts,
including mToken (ERC20 Delegator), Comptroller, and Reward Distributor contracts.
"""

# mToken (CErc20Delegator) ABI - for lending, borrowing, and position management
MTOKEN_ABI = [
    # Lend (supply) tokens by minting mTokens
    {
        "name": "mint",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "mintAmount", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Withdraw (redeem) underlying by burning mTokens
    {
        "name": "redeem",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "redeemTokens", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Withdraw exact underlying amount
    {
        "name": "redeemUnderlying",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "redeemAmount", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Borrow underlying tokens
    {
        "name": "borrow",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "borrowAmount", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Repay borrowed tokens
    {
        "name": "repayBorrow",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "repayAmount", "type": "uint256"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get mToken balance
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "owner", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get underlying balance (including accrued interest)
    {
        "name": "balanceOfUnderlying",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "owner", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get current borrow balance (including interest)
    {
        "name": "borrowBalanceCurrent",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get stored borrow balance (without accruing interest first)
    {
        "name": "borrowBalanceStored",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get exchange rate between mToken and underlying
    {
        "name": "exchangeRateCurrent",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get stored exchange rate
    {
        "name": "exchangeRateStored",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get underlying token address
    {
        "name": "underlying",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}],
    },
    # Get supply rate per timestamp
    {
        "name": "supplyRatePerTimestamp",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get borrow rate per timestamp
    {
        "name": "borrowRatePerTimestamp",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get total borrows
    {
        "name": "totalBorrows",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get total supply of mTokens
    {
        "name": "totalSupply",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get cash (available liquidity)
    {
        "name": "getCash",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Accrue interest
    {
        "name": "accrueInterest",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get decimals
    {
        "name": "decimals",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint8"}],
    },
]

# Comptroller ABI - for collateral management and account liquidity
COMPTROLLER_ABI = [
    # Enable a market as collateral
    {
        "name": "enterMarkets",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "mTokens", "type": "address[]"}],
        "outputs": [{"name": "", "type": "uint256[]"}],
    },
    # Disable a market as collateral
    {
        "name": "exitMarket",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "mTokenAddress", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get account liquidity (error, liquidity, shortfall)
    {
        "name": "getAccountLiquidity",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [
            {"name": "error", "type": "uint256"},
            {"name": "liquidity", "type": "uint256"},
            {"name": "shortfall", "type": "uint256"},
        ],
    },
    # Get market info (isListed, collateralFactorMantissa)
    {
        "name": "markets",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "mToken", "type": "address"}],
        "outputs": [
            {"name": "isListed", "type": "bool"},
            {"name": "collateralFactorMantissa", "type": "uint256"},
        ],
    },
    # Check if account has entered a market
    {
        "name": "checkMembership",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "account", "type": "address"},
            {"name": "mToken", "type": "address"},
        ],
        "outputs": [{"name": "", "type": "bool"}],
    },
    # Get all markets an account has entered
    {
        "name": "getAssetsIn",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "address[]"}],
    },
    # Get all listed markets
    {
        "name": "getAllMarkets",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address[]"}],
    },
    # Get hypothetical account liquidity
    {
        "name": "getHypotheticalAccountLiquidity",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "account", "type": "address"},
            {"name": "mTokenModify", "type": "address"},
            {"name": "redeemTokens", "type": "uint256"},
            {"name": "borrowAmount", "type": "uint256"},
        ],
        "outputs": [
            {"name": "error", "type": "uint256"},
            {"name": "liquidity", "type": "uint256"},
            {"name": "shortfall", "type": "uint256"},
        ],
    },
    # Get close factor
    {
        "name": "closeFactorMantissa",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get liquidation incentive
    {
        "name": "liquidationIncentiveMantissa",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Claim rewards for a user (called on comptroller in some versions)
    {
        "name": "claimReward",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "holder", "type": "address"}],
        "outputs": [],
    },
]

# Reward Distributor ABI - for claiming WELL rewards
REWARD_DISTRIBUTOR_ABI = [
    # Claim rewards for all markets
    {
        "name": "claimReward",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [],
        "outputs": [],
    },
    # Claim rewards for specific holder and markets
    {
        "name": "claimReward",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "holder", "type": "address"},
            {"name": "mTokens", "type": "address[]"},
        ],
        "outputs": [],
    },
    # Get reward token address
    {
        "name": "rewardToken",
        "type": "function",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "address"}],
    },
    # Get pending rewards (accrued but not yet claimed)
    {
        "name": "rewardAccrued",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "holder", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    # Get outstanding rewards for a user across all markets
    # Returns array of (mToken, [(rewardToken, totalReward, supplySide, borrowSide)])
    {
        "name": "getOutstandingRewardsForUser",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "user", "type": "address"}],
        "outputs": [
            {
                "name": "",
                "type": "tuple[]",
                "components": [
                    {"name": "mToken", "type": "address"},
                    {
                        "name": "rewards",
                        "type": "tuple[]",
                        "components": [
                            {"name": "rewardToken", "type": "address"},
                            {"name": "totalReward", "type": "uint256"},
                            {"name": "supplySide", "type": "uint256"},
                            {"name": "borrowSide", "type": "uint256"},
                        ],
                    },
                ],
            }
        ],
    },
    # Get outstanding rewards for a user for a specific mToken
    {
        "name": "getOutstandingRewardsForUser",
        "type": "function",
        "stateMutability": "view",
        "inputs": [
            {"name": "mToken", "type": "address"},
            {"name": "user", "type": "address"},
        ],
        "outputs": [
            {
                "name": "",
                "type": "tuple[]",
                "components": [
                    {"name": "rewardToken", "type": "address"},
                    {"name": "totalReward", "type": "uint256"},
                    {"name": "supplySide", "type": "uint256"},
                    {"name": "borrowSide", "type": "uint256"},
                ],
            }
        ],
    },
    # Get all market configurations for an mToken
    # Returns array of (mToken, rewardToken, supplyEmissionsPerSec, borrowEmissionsPerSec, ...)
    {
        "name": "getAllMarketConfigs",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "mToken", "type": "address"}],
        "outputs": [
            {
                "name": "",
                "type": "tuple[]",
                "components": [
                    {"name": "mToken", "type": "address"},
                    {"name": "rewardToken", "type": "address"},
                    {"name": "owner", "type": "address"},
                    {"name": "emissionCap", "type": "uint256"},
                    {"name": "supplyEmissionsPerSec", "type": "uint256"},
                    {"name": "borrowEmissionsPerSec", "type": "uint256"},
                    {"name": "supplyGlobalIndex", "type": "uint256"},
                    {"name": "borrowGlobalIndex", "type": "uint256"},
                    {"name": "endTime", "type": "uint256"},
                ],
            }
        ],
    },
]

# WETH ABI for wrapping/unwrapping ETH
WETH_ABI = [
    {
        "name": "deposit",
        "type": "function",
        "stateMutability": "payable",
        "inputs": [],
        "outputs": [],
    },
    {
        "name": "withdraw",
        "type": "function",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "wad", "type": "uint256"}],
        "outputs": [],
    },
    {
        "name": "balanceOf",
        "type": "function",
        "stateMutability": "view",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
]
