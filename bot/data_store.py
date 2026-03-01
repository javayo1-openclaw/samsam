from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class TradeRecord:
    ts: int
    side: str
    token_id: str
    signal_score: float
    spread_bps: float
    hold_seconds: int
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    fees: float
    outcome: int
    entry_reason_ko: str
    exit_reason_ko: str
    is_fallback_entry: int


class DataStore:
    def __init__(self, db_path: str) -> None:
        self.path = Path(db_path)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                side TEXT NOT NULL,
                token_id TEXT NOT NULL,
                signal_score REAL NOT NULL,
                spread_bps REAL NOT NULL,
                hold_seconds INTEGER NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                size REAL NOT NULL,
                pnl REAL NOT NULL,
                fees REAL NOT NULL,
                outcome INTEGER NOT NULL,
                entry_reason_ko TEXT NOT NULL DEFAULT '',
                exit_reason_ko TEXT NOT NULL DEFAULT '',
                is_fallback_entry INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._ensure_columns()
        self.conn.commit()

    def _ensure_columns(self) -> None:
        cols = {row[1] for row in self.conn.execute("PRAGMA table_info(trades)").fetchall()}
        if "entry_reason_ko" not in cols:
            self.conn.execute("ALTER TABLE trades ADD COLUMN entry_reason_ko TEXT NOT NULL DEFAULT ''")
        if "exit_reason_ko" not in cols:
            self.conn.execute("ALTER TABLE trades ADD COLUMN exit_reason_ko TEXT NOT NULL DEFAULT ''")
        if "is_fallback_entry" not in cols:
            self.conn.execute("ALTER TABLE trades ADD COLUMN is_fallback_entry INTEGER NOT NULL DEFAULT 0")

    def insert_trade(self, trade: TradeRecord) -> None:
        self.conn.execute(
            """
            INSERT INTO trades
            (ts, side, token_id, signal_score, spread_bps, hold_seconds, entry_price, exit_price, size, pnl, fees, outcome,
             entry_reason_ko, exit_reason_ko, is_fallback_entry)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade.ts,
                trade.side,
                trade.token_id,
                trade.signal_score,
                trade.spread_bps,
                trade.hold_seconds,
                trade.entry_price,
                trade.exit_price,
                trade.size,
                trade.pnl,
                trade.fees,
                trade.outcome,
                trade.entry_reason_ko,
                trade.exit_reason_ko,
                trade.is_fallback_entry,
            ),
        )
        self.conn.commit()

    def fetch_recent_trades(self, limit: int = 50) -> Iterable[tuple]:
        cursor = self.conn.execute(
            """
            SELECT ts, side, token_id, entry_price, exit_price, size, pnl, fees, outcome,
                   entry_reason_ko, exit_reason_ko, is_fallback_entry
            FROM trades
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()

    def summary(self) -> dict[str, float]:
        cursor = self.conn.execute(
            """
            SELECT
              COUNT(*) AS n,
              COALESCE(AVG(outcome), 0),
              COALESCE(SUM(pnl - fees), 0)
            FROM trades
            """
        )
        n, win_rate, net_pnl = cursor.fetchone()
        return {"n": float(n), "win_rate": float(win_rate), "net_pnl": float(net_pnl)}
