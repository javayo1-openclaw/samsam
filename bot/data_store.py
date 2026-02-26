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
                outcome INTEGER NOT NULL
            )
            """
        )
        self.conn.commit()

    def insert_trade(self, trade: TradeRecord) -> None:
        self.conn.execute(
            """
            INSERT INTO trades
            (ts, side, token_id, signal_score, spread_bps, hold_seconds, entry_price, exit_price, size, pnl, fees, outcome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            ),
        )
        self.conn.commit()

    def fetch_recent_trades(self, limit: int = 500) -> Iterable[tuple]:
        cursor = self.conn.execute(
            """
            SELECT ts, side, token_id, signal_score, spread_bps, hold_seconds,
                   entry_price, exit_price, size, pnl, fees, outcome
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
