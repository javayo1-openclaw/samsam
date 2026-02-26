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
    poll_interval_sec: float = 5.0
    status_interval_sec: float = 60.0
    retrain_every_n_trades: int = 30
    db_path: str = "trade_data.sqlite3"
    take_profit_pct: float = 0.02
    max_hold_seconds: int = 12 * 60
    order_size: float = 10.0


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
        poll_interval_sec=float(os.getenv("POLL_INTERVAL_SEC", "5")),
        status_interval_sec=float(os.getenv("STATUS_INTERVAL_SEC", "60")),
        retrain_every_n_trades=int(os.getenv("RETRAIN_EVERY_N_TRADES", "30")),
        db_path=os.getenv("DB_PATH", "trade_data.sqlite3"),
        take_profit_pct=float(os.getenv("TAKE_PROFIT_PCT", "0.02")),
        max_hold_seconds=int(os.getenv("MAX_HOLD_SECONDS", "720")),
        order_size=float(os.getenv("ORDER_SIZE", "10")),
    )
