from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass(slots=True)
class TelegramCommand:
    raw: str
    command: str
    args: list[str]


class TelegramGateway:
    def __init__(self, token: str, chat_id: str) -> None:
        self._token = token
        self._chat_id = str(chat_id)
        self._offset = 0

    @property
    def enabled(self) -> bool:
        return bool(self._token and self._chat_id)

    def send(self, text: str) -> None:
        if not self.enabled:
            return
        requests.post(
            f"https://api.telegram.org/bot{self._token}/sendMessage",
            json={"chat_id": self._chat_id, "text": text},
            timeout=10,
        )

    def poll_commands(self) -> list[TelegramCommand]:
        if not self.enabled:
            return []
        resp = requests.get(
            f"https://api.telegram.org/bot{self._token}/getUpdates",
            params={"timeout": 0, "offset": self._offset},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        commands: list[TelegramCommand] = []
        for item in data.get("result", []):
            self._offset = max(self._offset, item["update_id"] + 1)
            message = item.get("message", {})
            if str(message.get("chat", {}).get("id", "")) != self._chat_id:
                continue
            text = message.get("text", "").strip()
            if not text.startswith("/"):
                continue
            parts = text.split()
            cmd = parts[0].lower()
            commands.append(TelegramCommand(raw=text, command=cmd, args=parts[1:]))
        return commands
