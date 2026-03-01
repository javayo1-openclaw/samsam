from __future__ import annotations


def choose_side_by_btc_trend(first_price: float, last_price: float) -> str:
    if last_price >= first_price:
        return "UP"
    return "DOWN"
