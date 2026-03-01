from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    polymarket_host: str
    polymarket_chain_id: int
    polymarket_private_key: str
    polymarket_api_key: str
    polymarket_api_secret: str
    polymarket_api_passphrase: str
    yes_token_id: str
    no_token_id: str
    telegram_bot_token: str
    telegram_chat_id: str
    poll_interval_sec: float = 1.0
    status_interval_sec: float = 30.0
    db_path: str = "trade_data.sqlite3"
    order_size: float = 10.0
    entry_price_cap: float = 0.30
    take_profit_pct_primary: float = 1.5
    take_profit_pct_fallback: float = 1.0
    round_seconds: int = 15 * 60
    trend_window_seconds: int = 5
    entry_check_second: int = 10 * 60
    force_exit_before_expiry_sec: int = 3 * 60


def load_settings() -> Settings:
    return Settings(
        polymarket_host=os.getenv("POLYMARKET_HOST", "https://clob.polymarket.com"),
        polymarket_chain_id=int(os.getenv("POLYMARKET_CHAIN_ID", "137")),
        polymarket_private_key=os.getenv("POLYMARKET_PRIVATE_KEY", ""),
        polymarket_api_key=os.getenv("POLYMARKET_API_KEY", ""),
        polymarket_api_secret=os.getenv("POLYMARKET_API_SECRET", ""),
        polymarket_api_passphrase=os.getenv("POLYMARKET_API_PASSPHRASE", ""),
        yes_token_id=os.getenv("BTC15M_YES_TOKEN_ID", ""),
        no_token_id=os.getenv("BTC15M_NO_TOKEN_ID", ""),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        poll_interval_sec=float(os.getenv("POLL_INTERVAL_SEC", "1")),
        status_interval_sec=float(os.getenv("STATUS_INTERVAL_SEC", "30")),
        db_path=os.getenv("DB_PATH", "trade_data.sqlite3"),
        order_size=float(os.getenv("ORDER_SIZE", "10")),
        entry_price_cap=float(os.getenv("ENTRY_PRICE_CAP", "0.30")),
        take_profit_pct_primary=float(os.getenv("TAKE_PROFIT_PCT_PRIMARY", "1.5")),
        take_profit_pct_fallback=float(os.getenv("TAKE_PROFIT_PCT_FALLBACK", "1.0")),
        round_seconds=int(os.getenv("ROUND_SECONDS", "900")),
        trend_window_seconds=int(os.getenv("TREND_WINDOW_SECONDS", "5")),
        entry_check_second=int(os.getenv("ENTRY_CHECK_SECOND", "600")),
        force_exit_before_expiry_sec=int(os.getenv("FORCE_EXIT_BEFORE_EXPIRY_SEC", "180")),
    )
