from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(slots=True)
class StrategyState:
    entry_threshold: float = 0.62
    min_confidence: float = 0.55


class AdaptiveStrategy:
    def __init__(self) -> None:
        self.state = StrategyState()
        self._price_window: deque[float] = deque(maxlen=20)

    def score(self, yes_mid_price: float, spread_bps: float) -> float:
        self._price_window.append(yes_mid_price)
        if len(self._price_window) < 4:
            return 0.0
        momentum = self._price_window[-1] - self._price_window[0]
        spread_penalty = min(spread_bps / 100, 0.2)
        raw = 4.0 * momentum - spread_penalty
        return float(np.clip(raw, -1.0, 1.0))

    def should_enter(self, score: float) -> bool:
        confidence = (abs(score) + 1) / 2
        return confidence >= self.state.entry_threshold and confidence >= self.state.min_confidence

    def retrain(self, recent_rows: Iterable[tuple]) -> None:
        rows = list(recent_rows)
        if len(rows) < 30:
            return
        outcomes = np.array([r[11] for r in rows], dtype=np.float64)
        signals = np.array([r[3] for r in rows], dtype=np.float64)
        edge = np.mean(outcomes * np.sign(signals))
        if edge > 0.05:
            self.state.entry_threshold = max(0.52, self.state.entry_threshold - 0.01)
        elif edge < -0.02:
            self.state.entry_threshold = min(0.8, self.state.entry_threshold + 0.02)
