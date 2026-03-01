from __future__ import annotations

import argparse
import time

from .config import load_settings
from .data_store import DataStore, TradeRecord
from .polymarket_client import PolymarketClient, Position
from .strategy import choose_side_by_btc_trend
from .telegram import TelegramGateway


class TradingEngine:
    def __init__(self) -> None:
        self.settings = load_settings()
        self.store = DataStore(self.settings.db_path)
        self.exchange = PolymarketClient(
            self.settings.polymarket_host,
            self.settings.polymarket_chain_id,
            self.settings.polymarket_private_key,
            self.settings.polymarket_api_key,
            self.settings.polymarket_api_secret,
            self.settings.polymarket_api_passphrase,
            self.settings.yes_token_id,
            self.settings.no_token_id,
        )
        self.tg = TelegramGateway(
            self.settings.telegram_bot_token,
            self.settings.telegram_chat_id,
        )

        self.position: Position | None = None
        self.last_status_ts = 0.0

        self.round_start_ts = 0
        self.round_side: str | None = None
        self.round_first_btc: float | None = None
        self.round_last_btc: float | None = None
        self.round_has_trade = False
        self.round_signal_locked = False

        self.current_entry_reason_ko = ""
        self.current_is_fallback_entry = 0

    def run(self) -> None:
        self.tg.send("🚀 BTC 15m rule-engine started")
        while True:
            self._handle_commands()
            self._tick()
            time.sleep(self.settings.poll_interval_sec)

    def _current_round_start(self, now_ts: int) -> int:
        return now_ts - (now_ts % self.settings.round_seconds)

    def _reset_round(self, start_ts: int) -> None:
        self.round_start_ts = start_ts
        self.round_side = None
        self.round_first_btc = None
        self.round_last_btc = None
        self.round_has_trade = False
        self.round_signal_locked = False

    def _handle_commands(self) -> None:
        for cmd in self.tg.poll_commands():
            if cmd.command == "/status":
                self.tg.send(self._status_text())
            elif cmd.command == "/close":
                self._force_close("telegram_manual")
            elif cmd.command == "/history":
                self.tg.send(self._history_text())

    def _tick(self) -> None:
        now = int(time.time())
        start = self._current_round_start(now)
        if self.round_start_ts != start:
            self._reset_round(start)

        elapsed = now - self.round_start_ts

        self._update_trend_signal(elapsed)
        self._attempt_entry(elapsed)
        self._manage_open_position(elapsed)

        if now - self.last_status_ts >= self.settings.status_interval_sec:
            self.tg.send(self._status_text())
            self.last_status_ts = float(now)

    def _update_trend_signal(self, elapsed: int) -> None:
        if self.round_signal_locked:
            return
        if elapsed > self.settings.trend_window_seconds:
            if self.round_first_btc is not None and self.round_last_btc is not None:
                self.round_side = choose_side_by_btc_trend(self.round_first_btc, self.round_last_btc)
                self.round_signal_locked = True
                self.tg.send(
                    f"[진입근거] 초반 5초 BTC 추세로 방향 확정: {self.round_side} | "
                    f"{self.round_first_btc:.2f} -> {self.round_last_btc:.2f}"
                )
            return

        px = self.exchange.get_btc_price()
        if self.round_first_btc is None:
            self.round_first_btc = px
        self.round_last_btc = px

    def _attempt_entry(self, elapsed: int) -> None:
        if self.position is not None or self.round_has_trade:
            return
        if self.round_side is None:
            return
        if elapsed < self.settings.entry_check_second:
            return

        side_price = self.exchange.side_mark_price(self.round_side)
        if side_price > self.settings.entry_price_cap:
            self.round_has_trade = True
            self.tg.send(
                f"[진입스킵] 10분 시점 가격 {side_price:.3f}가 상한 {self.settings.entry_price_cap:.3f} 초과"
            )
            return

        self.current_entry_reason_ko = (
            f"초반 5초 BTC 추세가 {self.round_side}이고, 10분 시점 해당 토큰가격 {side_price:.3f} <= "
            f"진입상한 {self.settings.entry_price_cap:.3f}"
        )
        self.current_is_fallback_entry = 0

        try:
            self.position = self.exchange.open_position(self.round_side, self.settings.order_size)
            self.round_has_trade = True
            self.tg.send(
                f"[진입성공] {self.round_side} 진입 | 근거: {self.current_entry_reason_ko}"
            )
        except Exception as primary_exc:
            opposite = "DOWN" if self.round_side == "UP" else "UP"
            side_price_opposite = self.exchange.side_mark_price(opposite)
            self.current_entry_reason_ko = (
                f"주전략 {self.round_side} FOK 미체결로 반대매매 {opposite} 실행. "
                f"반대측 10분 시점 가격={side_price_opposite:.3f}"
            )
            self.current_is_fallback_entry = 1
            try:
                self.position = self.exchange.open_position(opposite, self.settings.order_size)
                self.round_has_trade = True
                self.tg.send(
                    f"[반대진입성공] 1차 FOK 실패({primary_exc}) 후 {opposite} 진입 | 근거: {self.current_entry_reason_ko}"
                )
            except Exception as fallback_exc:
                self.round_has_trade = True
                self.tg.send(
                    f"[진입실패] 주전략/반대전략 모두 실패 | primary={primary_exc} | fallback={fallback_exc}"
                )

    def _manage_open_position(self, elapsed: int) -> None:
        if self.position is None:
            return

        mark = self.exchange.mark_price(self.position.token_id)
        pnl_pct = (mark - self.position.entry_price) / max(self.position.entry_price, 1e-9)
        tp_target = (
            self.settings.take_profit_pct_fallback
            if self.current_is_fallback_entry == 1
            else self.settings.take_profit_pct_primary
        )

        if pnl_pct >= tp_target:
            reason = (
                f"익절청산: {'반대진입' if self.current_is_fallback_entry else '정상진입'} "
                f"목표수익률 {tp_target * 100:.0f}% 달성"
            )
            self._force_close(reason, mark_price=mark)
            return

        cutoff = self.settings.round_seconds - self.settings.force_exit_before_expiry_sec
        if elapsed >= cutoff:
            self._force_close("만기 3분 전 강제청산", mark_price=mark)

    def _force_close(self, reason: str, mark_price: float = 0.0) -> None:
        if not self.position:
            return
        now = int(time.time())
        held = now - self.position.entry_ts
        pnl, fees, exit_price = self.exchange.close_position(self.position)
        outcome = 1 if pnl - fees > 0 else 0

        self.store.insert_trade(
            TradeRecord(
                ts=now,
                side=self.position.side,
                token_id=self.position.token_id,
                signal_score=1.0 if self.position.side == "UP" else -1.0,
                spread_bps=0.0,
                hold_seconds=held,
                entry_price=self.position.entry_price,
                exit_price=exit_price if exit_price > 0 else mark_price,
                size=self.position.size,
                pnl=pnl,
                fees=fees,
                outcome=outcome,
                entry_reason_ko=self.current_entry_reason_ko,
                exit_reason_ko=reason,
                is_fallback_entry=self.current_is_fallback_entry,
            )
        )
        self.tg.send(f"[청산] {self.position.side} | 사유: {reason} | 손익={pnl - fees:.4f}")
        self.position = None
        self.current_entry_reason_ko = ""
        self.current_is_fallback_entry = 0

    def _history_text(self) -> str:
        rows = list(self.store.fetch_recent_trades(5))
        if not rows:
            return "최근 매매 이력이 없습니다."

        lines = ["🧾 최근 5건 전적"]
        for row in rows:
            ts, side, _, entry_price, exit_price, size, pnl, fees, outcome, entry_reason, exit_reason, is_fallback = row
            lines.append(
                f"- [{ts}] {side} {'(반대진입)' if is_fallback else '(정상진입)'} "
                f"진입:{entry_price:.3f} 청산:{exit_price:.3f} 수량:{size} "
                f"손익:{(pnl - fees):.4f} {'승' if outcome == 1 else '패'}"
            )
            lines.append(f"  · 진입근거: {entry_reason}")
            lines.append(f"  · 청산사유: {exit_reason}")
        return "\n".join(lines)

    def _status_text(self) -> str:
        stats = self.store.summary()
        now = int(time.time())
        elapsed = now - self._current_round_start(now)
        position = self.position.side if self.position else "NONE"
        return (
            f"📊 Status\n"
            f"Round elapsed: {elapsed}s\n"
            f"Signal side: {self.round_side or 'NONE'}\n"
            f"Position: {position}\n"
            f"Trades: {int(stats['n'])}\n"
            f"Win rate: {stats['win_rate'] * 100:.2f}%\n"
            f"Net PnL: {stats['net_pnl']:.4f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Polymarket BTC15m Up/Down auto trader")
    parser.parse_args()
    TradingEngine().run()


if __name__ == "__main__":
    main()
