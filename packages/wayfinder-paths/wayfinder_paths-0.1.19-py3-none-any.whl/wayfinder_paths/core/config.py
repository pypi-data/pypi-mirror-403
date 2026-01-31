import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from loguru import logger


def _load_config_file() -> dict[str, Any]:
    path = Path("config.json")
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.warning(f"Failed to read config file at config.json: {e}")
        return {}


CONFIG = _load_config_file()
SUPPORTED_CHAINS = [
    1,
    8453,
    56,
    42161,
    137,
    999,
]


@dataclass
class UserConfig:
    username: str | None = None
    password: str | None = None
    refresh_token: str | None = None
    main_wallet_address: str | None = None
    strategy_wallet_address: str | None = None
    default_slippage: float = 0.005
    gas_multiplier: float = 1.2


@dataclass
class SystemConfig:
    api_base_url: str = field(default="https://api.wayfinder.ai")
    job_id: str | None = None
    job_type: str = "strategy"
    update_interval: int = 60
    max_retries: int = 3
    retry_delay: int = 5
    log_path: str | None = None
    data_path: str | None = None
    wallet_id: str | None = None


@dataclass
class StrategyJobConfig:
    user: UserConfig
    system: SystemConfig
    strategy_config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        try:
            if not isinstance(self.strategy_config, dict):
                self.strategy_config = {}

            wallet_type = self._get_wallet_type()
            if wallet_type and wallet_type != "local":
                return

            by_label, by_addr = self._load_wallets_from_file()

            self._enrich_wallet_addresses(by_label)
            if wallet_type in (None, "local"):
                self._enrich_wallet_private_keys(by_addr)
        except Exception as e:
            logger.warning(
                f"Failed to enrich strategy config with wallet information: {e}"
            )

    def _get_wallet_type(self) -> str | None:
        wallet_type = self.strategy_config.get("wallet_type")
        if wallet_type:
            return wallet_type

        main_wallet = self.strategy_config.get("main_wallet")
        if isinstance(main_wallet, dict):
            wallet_type = main_wallet.get("wallet_type")
            if wallet_type:
                return wallet_type

        strategy_wallet = self.strategy_config.get("strategy_wallet")
        if isinstance(strategy_wallet, dict):
            wallet_type = strategy_wallet.get("wallet_type")
            if wallet_type:
                return wallet_type

        return None

    def _load_wallets_from_file(
        self,
    ) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
        entries = _read_wallets_from_config()
        by_label: dict[str, dict[str, Any]] = {}
        by_addr: dict[str, dict[str, Any]] = {}

        if entries and isinstance(entries, list):
            for e in entries:
                if isinstance(e, dict):
                    label = e.get("label")
                    if isinstance(label, str):
                        by_label[label] = e
                    addr = e.get("address")
                    if isinstance(addr, str):
                        by_addr[addr.lower()] = e

        return by_label, by_addr

    def _enrich_wallet_addresses(self, by_label: dict[str, dict[str, Any]]) -> None:
        if "main_wallet" not in self.strategy_config:
            main_wallet = by_label.get("main")
            if main_wallet:
                self.strategy_config["main_wallet"] = {
                    "address": main_wallet["address"]
                }

        strategy_name = self.strategy_config.get("_strategy_name")
        if strategy_name and isinstance(strategy_name, str):
            strategy_wallet = by_label.get(strategy_name)
            if strategy_wallet:
                if "strategy_wallet" not in self.strategy_config:
                    self.strategy_config["strategy_wallet"] = {
                        "address": strategy_wallet["address"]
                    }
                elif isinstance(self.strategy_config.get("strategy_wallet"), dict):
                    if not self.strategy_config["strategy_wallet"].get("address"):
                        self.strategy_config["strategy_wallet"]["address"] = (
                            strategy_wallet["address"]
                        )

    def _enrich_wallet_private_keys(self, by_addr: dict[str, dict[str, Any]]) -> None:
        try:
            for key in ("main_wallet", "strategy_wallet"):
                wallet_obj = self.strategy_config.get(key)
                if isinstance(wallet_obj, dict):
                    addr = (wallet_obj.get("address") or "").lower()
                    entry = by_addr.get(addr)
                    if entry:
                        pk = entry.get("private_key") or entry.get("private_key_hex")
                        if (
                            pk
                            and not wallet_obj.get("private_key")
                            and not wallet_obj.get("private_key_hex")
                        ):
                            wallet_obj["private_key_hex"] = pk
        except Exception as e:
            logger.warning(
                f"Failed to enrich wallet private keys from config.json: {e}"
            )

    @classmethod
    def from_dict(
        cls, data: dict[str, Any], strategy_name: str | None = None
    ) -> "StrategyJobConfig":
        user_data = data.get("user", {})
        user_cfg = UserConfig(
            username=user_data.get("username"),
            password=user_data.get("password"),
            refresh_token=user_data.get("refresh_token"),
            main_wallet_address=user_data.get("main_wallet_address"),
            strategy_wallet_address=user_data.get("strategy_wallet_address"),
            default_slippage=user_data.get("default_slippage", 0.005),
            gas_multiplier=user_data.get("gas_multiplier", 1.2),
        )

        system_data = data.get("system", {})
        sys_cfg = SystemConfig(
            api_base_url=system_data.get("api_base_url", "https://api.wayfinder.ai"),
            job_id=system_data.get("job_id"),
            job_type=system_data.get("job_type", "strategy"),
            update_interval=system_data.get("update_interval", 60),
            max_retries=system_data.get("max_retries", 3),
            retry_delay=system_data.get("retry_delay", 5),
            log_path=system_data.get("log_path"),
            data_path=system_data.get("data_path"),
            wallet_id=system_data.get("wallet_id"),
        )

        strategy_config = data.get("strategy", {})
        if strategy_name:
            strategy_config["_strategy_name"] = strategy_name
        return cls(
            user=user_cfg,
            system=sys_cfg,
            strategy_config=strategy_config,
        )


def set_rpc_urls(rpc_urls):
    if "strategy" not in CONFIG:
        CONFIG["strategy"] = {}
    if "rpc_urls" not in CONFIG["strategy"]:
        CONFIG["strategy"]["rpc_urls"] = {}
    CONFIG["strategy"]["rpc_urls"] = rpc_urls


def get_rpc_urls() -> dict[str, Any]:
    return CONFIG.get("strategy", {}).get("rpc_urls", {})


def get_api_base_url() -> str:
    system = CONFIG.get("system", {}) if isinstance(CONFIG, dict) else {}
    api_url = system.get("api_base_url")
    if api_url and isinstance(api_url, str):
        return api_url.strip()
    return "https://wayfinder.ai/api/v1"


def _read_wallets_from_config() -> list[dict[str, Any]]:
    try:
        wallets = CONFIG.get("wallets", [])
        if isinstance(wallets, list):
            return wallets
        logger.warning("Wallets section in config.json is not a list")
        return []
    except Exception as e:
        logger.warning(f"Failed to read wallets from config.json: {e}")
        return []
