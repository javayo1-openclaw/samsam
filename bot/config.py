from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    polymarket_api_key: str
    polymarket_api_secret: str
    telegram_bot_token: str
    telegram_chat_id: str
    symbol: str = "BTC"
    poll_interval_sec: float = 5.0
    status_interval_sec: float = 60.0
    retrain_every_n_trades: int = 30
    db_path: str = "trade_data.sqlite3"


def load_settings() -> Settings:
    return Settings(
        polymarket_api_key=os.getenv("POLYMARKET_API_KEY", ""),
        polymarket_api_secret=os.getenv("POLYMARKET_API_SECRET", ""),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        symbol=os.getenv("SYMBOL", "BTC"),
        poll_interval_sec=float(os.getenv("POLL_INTERVAL_SEC", "5")),
        status_interval_sec=float(os.getenv("STATUS_INTERVAL_SEC", "60")),
        retrain_every_n_trades=int(os.getenv("RETRAIN_EVERY_N_TRADES", "30")),
        db_path=os.getenv("DB_PATH", "trade_data.sqlite3"),
    )
