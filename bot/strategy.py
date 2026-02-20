from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(slots=True)
class StrategyState:
    entry_threshold: float = 0.62
    min_confidence: float = 0.55
    size_fraction: float = 0.2


class AdaptiveStrategy:
    """Simple online strategy tuner using recent trade outcomes.

    This is intentionally conservative in parameter updates to avoid unstable behavior.
    """

    def __init__(self) -> None:
        self.state = StrategyState()

    def score(self, momentum: float, order_imbalance: float, vol_spike: float) -> float:
        raw = 0.5 * momentum + 0.3 * order_imbalance + 0.2 * vol_spike
        return float(np.clip(raw, -1.0, 1.0))

    def should_enter(self, score: float) -> bool:
        confidence = (score + 1) / 2
        return confidence >= self.state.entry_threshold and confidence >= self.state.min_confidence

    def retrain(self, recent_rows: Iterable[tuple]) -> None:
        rows = list(recent_rows)
        if len(rows) < 30:
            return

        outcomes = np.array([r[8] for r in rows], dtype=np.float64)
        signals = np.array([r[3] for r in rows], dtype=np.float64)
        spread = np.array([r[4] for r in rows], dtype=np.float64)

        weighted_edge = np.mean(outcomes * np.sign(signals) - 0.01 * spread)
        if weighted_edge > 0.03:
            self.state.entry_threshold = max(0.52, self.state.entry_threshold - 0.01)
            self.state.size_fraction = min(0.35, self.state.size_fraction + 0.01)
        elif weighted_edge < -0.02:
            self.state.entry_threshold = min(0.8, self.state.entry_threshold + 0.02)
            self.state.size_fraction = max(0.08, self.state.size_fraction - 0.02)
