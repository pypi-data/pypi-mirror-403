from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any


def _load_wallets(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a list in {path}")
    return [w for w in data if isinstance(w, dict)]


def _load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a dict in {path}")
    return data


def _find_wallet(wallets: list[dict[str, Any]], label: str) -> dict[str, Any]:
    for w in wallets:
        if w.get("label") == label:
            return w
    raise ValueError(f"Wallet label not found in config.json: {label}")


def _get_strategy_class(strategy: str):
    if strategy == "basis_trading_strategy":
        from wayfinder_paths.strategies.basis_trading_strategy.strategy import (
            BasisTradingStrategy,
        )

        return BasisTradingStrategy

    if strategy == "hyperlend_stable_yield_strategy":
        from wayfinder_paths.strategies.hyperlend_stable_yield_strategy.strategy import (
            HyperlendStableYieldStrategy,
        )

        return HyperlendStableYieldStrategy

    if strategy == "moonwell_wsteth_loop_strategy":
        from wayfinder_paths.strategies.moonwell_wsteth_loop_strategy.strategy import (
            MoonwellWstethLoopStrategy,
        )

        return MoonwellWstethLoopStrategy

    raise ValueError(f"Unknown strategy: {strategy}")


async def _run(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    wallets_path = (
        Path(args.wallets).resolve() if args.wallets else repo_root / "config.json"
    )
    config_path = (
        Path(args.config).resolve() if args.config else repo_root / "config.json"
    )

    wallets = _load_wallets(wallets_path)
    config = _load_config(config_path)

    main_wallet = _find_wallet(wallets, args.main_wallet_label)
    strategy_wallet = _find_wallet(wallets, args.strategy_wallet_label)

    # Merge config with wallet info
    strategy_config = {
        "main_wallet": main_wallet,
        "strategy_wallet": strategy_wallet,
        **config.get("strategy", {}),
    }

    strategy_class = _get_strategy_class(args.strategy)
    s = strategy_class(strategy_config)

    await s.setup()

    if args.command == "deposit":
        ok, msg = await s.deposit(
            main_token_amount=float(args.usdc), gas_token_amount=float(args.eth)
        )
        print(msg)
        return 0 if ok else 1

    if args.command == "update":
        ok, msg = await s.update()
        print(msg)
        return 0 if ok else 1

    if args.command == "withdraw":
        ok, msg = await s.withdraw(
            amount=float(args.amount) if args.amount is not None else None
        )
        print(msg)
        return 0 if ok else 1

    if args.command == "status":
        st = await s.status()
        print(json.dumps(st, indent=2, sort_keys=True))
        return 0

    raise ValueError(f"Unknown command: {args.command}")


def main() -> int:
    p = argparse.ArgumentParser(
        description="Run a strategy locally (deposit/update/withdraw/status)."
    )
    p.add_argument(
        "--strategy",
        default="basis_trading_strategy",
        choices=[
            "basis_trading_strategy",
            "hyperlend_stable_yield_strategy",
            "moonwell_wsteth_loop_strategy",
        ],
    )
    p.add_argument(
        "--wallets", default=None, help="Path to config.json (default: repo root)"
    )
    p.add_argument(
        "--config", default=None, help="Path to config.json (default: repo root)"
    )
    p.add_argument("--main-wallet-label", default="main")
    p.add_argument("--strategy-wallet-label", default="basis_trading_strategy")

    sub = p.add_subparsers(dest="command", required=True)

    dep = sub.add_parser("deposit")
    dep.add_argument("--usdc", required=True, type=float)
    dep.add_argument("--eth", default=0.0, type=float)

    sub.add_parser("update")

    wd = sub.add_parser("withdraw")
    wd.add_argument("--amount", default=None, type=float)

    sub.add_parser("status")

    args = p.parse_args()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
