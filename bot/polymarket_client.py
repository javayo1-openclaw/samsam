from __future__ import annotations

import time
from dataclasses import dataclass

import requests


@dataclass(slots=True)
class Position:
    side: str
    token_id: str
    entry_ts: int
    entry_price: float
    size: float


class PolymarketClient:
    """Polymarket client for BTC 15m YES/NO tokens.

    Requires token ids for the specific BTC 15m market outcome tokens.
    """

    def __init__(
        self,
        host: str,
        chain_id: int,
        private_key: str,
        api_key: str,
        api_secret: str,
        api_passphrase: str,
        yes_token_id: str,
        no_token_id: str,
    ) -> None:
        self.host = host.rstrip("/")
        self.chain_id = chain_id
        self.private_key = private_key
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.yes_token_id = yes_token_id
        self.no_token_id = no_token_id

        self._clob_client = None
        self._init_clob_client()

    def _init_clob_client(self) -> None:
        try:
            from py_clob_client.client import ClobClient
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("py-clob-client 미설치: pip install py-clob-client") from exc

        client = ClobClient(self.host, key=self.private_key, chain_id=self.chain_id)

        if self.api_key and self.api_secret and self.api_passphrase:
            client.set_api_creds(
                {
                    "key": self.api_key,
                    "secret": self.api_secret,
                    "passphrase": self.api_passphrase,
                }
            )
        else:
            client.set_api_creds(client.create_or_derive_api_creds())

        self._clob_client = client

    def _best_bid_ask(self, token_id: str) -> tuple[float, float]:
        resp = requests.get(
            f"{self.host}/book",
            params={"token_id": token_id},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        best_bid = float(bids[0]["price"]) if bids else 0.0
        best_ask = float(asks[0]["price"]) if asks else 1.0
        return best_bid, best_ask

    def get_features(self) -> dict[str, float]:
        yes_bid, yes_ask = self._best_bid_ask(self.yes_token_id)
        yes_mid = (yes_bid + yes_ask) / 2
        spread_bps = ((yes_ask - yes_bid) / max(yes_mid, 1e-6)) * 10_000
        return {
            "yes_mid_price": yes_mid,
            "spread_bps": spread_bps,
        }

    def mark_price(self, token_id: str) -> float:
        bid, ask = self._best_bid_ask(token_id)
        return (bid + ask) / 2

    def open_position(self, side: str, size: float) -> Position:
        token_id = self.yes_token_id if side == "UP" else self.no_token_id
        entry_price = self.mark_price(token_id)
        self._place_buy(token_id, size)
        return Position(side=side, token_id=token_id, entry_ts=int(time.time()), entry_price=entry_price, size=size)

    def close_position(self, pos: Position) -> tuple[float, float, float]:
        exit_price = self.mark_price(pos.token_id)
        self._place_sell(pos.token_id, pos.size)
        pnl = (exit_price - pos.entry_price) * pos.size
        fees = abs(pos.size) * 0.002
        return pnl, fees, exit_price

    def _place_buy(self, token_id: str, size: float) -> None:
        from py_clob_client.clob_types import OrderArgs, OrderType
        from py_clob_client.order_builder.constants import BUY

        order = self._clob_client.create_order(
            OrderArgs(token_id=token_id, price=0.99, size=size, side=BUY)
        )
        self._clob_client.post_order(order, OrderType.FOK)

    def _place_sell(self, token_id: str, size: float) -> None:
        from py_clob_client.clob_types import OrderArgs, OrderType
        from py_clob_client.order_builder.constants import SELL

        order = self._clob_client.create_order(
            OrderArgs(token_id=token_id, price=0.01, size=size, side=SELL)
        )
        self._clob_client.post_order(order, OrderType.FOK)
