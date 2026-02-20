from __future__ import annotations

import argparse
import time
from dataclasses import asdict

from .config import load_settings
from .data_store import DataStore, TradeRecord
from .polymarket_client import PolymarketClient, Position
from .strategy import AdaptiveStrategy
from .telegram import TelegramGateway


class TradingEngine:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.store = DataStore(self.settings.db_path)
        self.strategy = AdaptiveStrategy()
        self.exchange = PolymarketClient(
            self.settings.polymarket_api_key,
            self.settings.polymarket_api_secret,
            self.settings.symbol,
        )
        self.tg = TelegramGateway(
            self.settings.telegram_bot_token,
            self.settings.telegram_chat_id,
        )
        self.position: Position | None = None
        self.last_status_ts = 0.0
        self.closed_count = 0

    def run(self) -> None:
        self.tg.send("🚀 live engine started")
        while True:
            self._handle_commands()
            self._tick()
            time.sleep(self.settings.poll_interval_sec)

    def _handle_commands(self) -> None:
        for cmd in self.tg.poll_commands():
            if cmd.command == "/status":
                self.tg.send(self._status_text())
            elif cmd.command == "/close":
                self._force_close("telegram")
            elif cmd.command == "/buyup":
                if not self.position:
                    self.position = self.exchange.open_position("UP", self.strategy.state.size_fraction)
                    self.tg.send("Manual UP position opened")
            elif cmd.command == "/buydown":
                if not self.position:
                    self.position = self.exchange.open_position("DOWN", self.strategy.state.size_fraction)
                    self.tg.send("Manual DOWN position opened")

    def _tick(self) -> None:
        now = time.time()
        feats = self.exchange.get_features()
        score = self.strategy.score(
            feats["momentum"], feats["order_imbalance"], feats["vol_spike"]
        )

        if self.position is None and self.strategy.should_enter(score):
            side = "UP" if score > 0 else "DOWN"
            self.position = self.exchange.open_position(side, self.strategy.state.size_fraction)
            self.tg.send(f"Opened {side} | score={score:.3f} size={self.strategy.state.size_fraction:.2f}")

        if self.position is not None:
            held = int(now - self.position.entry_ts)
            if held >= 8 * 60:
                self._force_close("time_exit", score=score, spread_bps=feats["spread_bps"], held=held)

        if now - self.last_status_ts >= self.settings.status_interval_sec:
            self.tg.send(self._status_text())
            self.last_status_ts = now

    def _force_close(self, reason: str, score: float = 0.0, spread_bps: float = 0.0, held: int = 0) -> None:
        if not self.position:
            return
        pnl, fees = self.exchange.close_position(self.position)
        outcome = 1 if pnl - fees > 0 else 0
        self.store.insert_trade(
            TradeRecord(
                ts=int(time.time()),
                symbol=self.settings.symbol,
                side=self.position.side,
                signal_score=score,
                spread_bps=spread_bps,
                hold_seconds=held,
                pnl=pnl,
                fees=fees,
                outcome=outcome,
            )
        )
        self.closed_count += 1
        self.tg.send(f"Closed {self.position.side} reason={reason} pnl={pnl - fees:.4f}")
        self.position = None

        if self.closed_count % self.settings.retrain_every_n_trades == 0:
            self.strategy.retrain(self.store.fetch_recent_trades())
            self.tg.send(f"Strategy auto-tuned: {asdict(self.strategy.state)}")

    def _status_text(self) -> str:
        stats = self.store.summary()
        position = self.position.side if self.position else "NONE"
        return (
            f"📊 Status\n"
            f"Position: {position}\n"
            f"Trades: {int(stats['n'])}\n"
            f"Win rate: {stats['win_rate'] * 100:.2f}%\n"
            f"Net PnL: {stats['net_pnl']:.4f}\n"
            f"Params: threshold={self.strategy.state.entry_threshold:.2f}, size={self.strategy.state.size_fraction:.2f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Polymarket 15m aggressive trading engine")
    parser.parse_args()
    TradingEngine().run()


if __name__ == "__main__":
    main()
