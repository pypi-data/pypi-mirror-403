#!/usr/bin/env python3
"""
Strategy Runner
Main entry point for running strategies locally
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from loguru import logger

from wayfinder_paths.core.config import StrategyJobConfig
from wayfinder_paths.core.engine.StrategyJob import StrategyJob
from wayfinder_paths.core.utils.evm_helpers import resolve_private_key_for_from_address
from wayfinder_paths.core.utils.web3 import get_transaction_chain_id, web3_from_chain_id


def load_strategy(
    strategy_name: str,
    *,
    config: StrategyJobConfig,
):
    """
    Dynamically load a strategy by name

    Args:
        strategy_name: Name of the strategy to load (directory name in strategies/)
        config: StrategyJobConfig instance containing user and strategy configuration

    Returns:
        Strategy instance
    """
    # Build the expected module path from strategy name
    strategies_dir = Path(__file__).parent / "strategies"
    strategy_dir = strategies_dir / strategy_name

    if not strategy_dir.exists():
        # List available strategies for better error message
        available = []
        if strategies_dir.exists():
            for path in strategies_dir.iterdir():
                if path.is_dir() and (path / "strategy.py").exists():
                    available.append(path.name)
        available_str = ", ".join(available) if available else "none"
        raise ValueError(
            f"Unknown strategy: {strategy_name}. Available strategies: {available_str}"
        )

    # Import strategy module and find Strategy class
    module_path = f"strategies.{strategy_name}.strategy"
    module = __import__(module_path, fromlist=[""])

    # Find the Strategy subclass in the module
    from wayfinder_paths.core.strategies.Strategy import Strategy

    strategy_class = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, Strategy)
            and attr is not Strategy
        ):
            strategy_class = attr
            break

    if strategy_class is None:
        raise ValueError(f"No Strategy class found in {module_path}")

    # Get wallet addresses from strategy_config (enriched from wallets array in config.json)
    main_wallet = config.strategy_config.get("main_wallet") or {}
    strategy_wallet = config.strategy_config.get("strategy_wallet") or {}
    main_wallet_address = main_wallet.get("address")
    strategy_wallet_address = strategy_wallet.get("address")

    async def main_wallet_signing_callback(transaction):
        private_key = resolve_private_key_for_from_address(
            main_wallet_address, config.strategy_config
        )
        async with web3_from_chain_id(get_transaction_chain_id(transaction)) as web3:
            signed = web3.eth.account.sign_transaction(transaction, private_key)
            return signed.raw_transaction.hex()

    async def strategy_wallet_signing_callback(transaction):
        private_key = resolve_private_key_for_from_address(
            strategy_wallet_address,
            config.strategy_config,
        )
        async with web3_from_chain_id(get_transaction_chain_id(transaction)) as web3:
            signed = web3.eth.account.sign_transaction(transaction, private_key)
            return signed.raw_transaction.hex()

    return strategy_class(
        config=config.strategy_config,
        main_wallet_signing_callback=main_wallet_signing_callback,
        strategy_wallet_signing_callback=strategy_wallet_signing_callback,
    )


def load_config(
    config_path: str | None = None, strategy_name: str | None = None
) -> StrategyJobConfig:
    """
    Load configuration from config.json file

    Args:
        config_path: Path to config file (defaults to "config.json")
        strategy_name: Optional strategy name for per-strategy wallet lookup

    Returns:
        StrategyJobConfig instance

    Raises:
        FileNotFoundError: If config file does not exist
    """
    # Default to config.json if not provided
    if not config_path:
        config_path = "config.json"

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(
            f"Config file not found: {config_path}. "
            "Please create config.json (see wayfinder_paths/config.example.json for template)"
        )

    logger.info(f"Loading config from {config_path}")
    with open(config_file) as f:
        config_data = json.load(f)

    config = StrategyJobConfig.from_dict(config_data, strategy_name=strategy_name)
    if strategy_name:
        config.strategy_config["_strategy_name"] = strategy_name
        config.__post_init__()
    return config


async def run_strategy(
    strategy_name: str | None = None,
    config_path: str | None = None,
    action: str = "run",
    **kwargs,
):
    """
    Run a strategy

    Args:
        strategy_name: Name of the strategy to run
        config_path: Optional path to config file
        action: Action to perform (run, deposit, withdraw, status)
        **kwargs: Additional arguments for the action
    """
    try:
        if not strategy_name:
            raise ValueError("strategy_name is required")

        logger.debug(f"Loading strategy by name: {strategy_name}")

        # Load configuration with strategy name for wallet lookup
        logger.debug(f"Config path provided: {config_path}")
        config = load_config(config_path, strategy_name=strategy_name)
        main_wallet_cfg = config.strategy_config.get("main_wallet") or {}
        strategy_wallet_cfg = config.strategy_config.get("strategy_wallet") or {}
        logger.debug(
            "Loaded config: wallets(main={} strategy={})",
            main_wallet_cfg.get("address") or "none",
            strategy_wallet_cfg.get("address") or "none",
        )

        # Validate required configuration
        # Authentication is via system.api_key in config.json

        # Load strategy with the enriched config
        strategy = load_strategy(
            strategy_name,
            config=config,
        )
        logger.info(f"Loaded strategy: {strategy.name}")

        # Create strategy job
        strategy_job = StrategyJob(strategy, config)

        # Setup strategy job
        logger.info("Setting up strategy job...")
        logger.debug("Auth mode: API key (from system.api_key)")
        await strategy_job.setup()

        # Execute action
        if action == "run":
            logger.info("Starting continuous execution...")
            await strategy_job.run_continuous(interval_seconds=kwargs.get("interval"))

        elif action == "deposit":
            main_token_amount = kwargs.get("main_token_amount")
            gas_token_amount = kwargs.get("gas_token_amount")

            if main_token_amount is None and gas_token_amount is None:
                raise ValueError(
                    "Either main token amount or gas token amount required for deposit (use --main-token-amount and/or --gas-token-amount)"
                )

            # Default to 0.0 if not provided
            if main_token_amount is None:
                main_token_amount = 0.0
            if gas_token_amount is None:
                gas_token_amount = 0.0

            result = await strategy_job.execute_strategy(
                "deposit",
                main_token_amount=main_token_amount,
                gas_token_amount=gas_token_amount,
            )
            logger.info(f"Deposit result: {result}")

        elif action == "withdraw":
            amount = kwargs.get("amount")
            result = await strategy_job.execute_strategy("withdraw", amount=amount)
            logger.info(f"Withdraw result: {result}")

        elif action == "status":
            result = await strategy_job.execute_strategy("status")
            logger.info(f"Status: {json.dumps(result, indent=2)}")

        elif action == "update":
            result = await strategy_job.execute_strategy("update")
            logger.info(f"Update result: {result}")

        elif action == "exit":
            result = await strategy_job.execute_strategy("exit")
            logger.info(f"Exit result: {result}")

        elif action == "partial-liquidate":
            usd_value = kwargs.get("amount")
            if not usd_value:
                raise ValueError("Amount (USD value) required for partial-liquidate")
            result = await strategy_job.execute_strategy(
                "partial_liquidate", usd_value=usd_value
            )
            logger.info(f"Partial liquidation result: {result}")

        elif action == "policy":
            policies: list[str] = []

            try:
                spols = getattr(strategy, "policies", None)
                if callable(spols):
                    result = spols()  # type: ignore[misc]
                    if isinstance(result, list) and result:
                        policies = [p for p in result if isinstance(p, str)]
            except Exception:
                pass

            seen = set()
            deduped: list[str] = []
            for p in policies:
                if p not in seen:
                    seen.add(p)
                    deduped.append(p)

            # Get wallet_id from CLI arg, config, or leave as None
            wallet_id = kwargs.get("wallet_id")
            if not wallet_id:
                wallet_id = config.strategy_config.get("wallet_id")
            if not wallet_id:
                wallet_id = config.system.wallet_id

            # Render policies with wallet_id if available
            if wallet_id:
                rendered = [
                    p.replace("FORMAT_WALLET_ID", str(wallet_id)) for p in deduped
                ]
            else:
                rendered = deduped
                logger.info(
                    "Policy rendering without wallet_id - policies contain FORMAT_WALLET_ID placeholder"
                )

            logger.info(json.dumps({"policies": rendered}, indent=2))

        elif action == "script":
            duration = kwargs.get("duration") or 300
            logger.info(f"Running script mode for {duration}s...")
            task = asyncio.create_task(
                strategy_job.run_continuous(
                    interval_seconds=kwargs.get("interval") or 60
                )
            )
            await asyncio.sleep(duration)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info("Script mode execution completed")

        else:
            raise ValueError(f"Unknown action: {action}")

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        if "strategy_job" in locals():
            await strategy_job.stop()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run strategy strategies")
    parser.add_argument(
        "strategy",
        help="Strategy to run (stablecoin_yield_strategy)",
    )
    parser.add_argument(
        "--config", help="Path to config file (defaults to config.json)"
    )
    parser.add_argument(
        "--action",
        default="run",
        choices=[
            "run",
            "deposit",
            "withdraw",
            "status",
            "update",
            "exit",
            "policy",
            "script",
            "partial-liquidate",
        ],
        help="Action to perform (default: run)",
    )
    parser.add_argument(
        "--amount",
        type=float,
        help="Amount for withdraw/partial-liquidate actions",
    )
    parser.add_argument(
        "--main-token-amount",
        "--main_token_amount",
        type=float,
        dest="main_token_amount",
        help="Main token amount for deposit action",
    )
    parser.add_argument(
        "--gas-token-amount",
        "--gas_token_amount",
        type=float,
        dest="gas_token_amount",
        default=0.0,
        help="Gas token amount for deposit action (default: 0.0)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Update interval in seconds for continuous/script modes",
    )
    parser.add_argument(
        "--duration", type=int, help="Duration in seconds for script action"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--wallet-id",
        help="Wallet ID for policy rendering (replaces FORMAT_WALLET_ID in policies)",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = "DEBUG" if args.debug else "INFO"
    logger.remove()
    logger.add(sys.stderr, level=log_level)

    # Run strategy
    asyncio.run(
        run_strategy(
            strategy_name=args.strategy,
            config_path=args.config,
            action=args.action,
            amount=args.amount,
            main_token_amount=args.main_token_amount,
            gas_token_amount=args.gas_token_amount,
            interval=args.interval,
            duration=args.duration,
            wallet_id=getattr(args, "wallet_id", None),
        )
    )


if __name__ == "__main__":
    main()
