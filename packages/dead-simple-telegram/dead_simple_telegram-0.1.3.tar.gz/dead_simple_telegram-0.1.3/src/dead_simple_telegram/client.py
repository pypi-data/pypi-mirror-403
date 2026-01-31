from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping

import requests


@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    chat_id: str
    timeout: int = 10

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        return cls(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            timeout=int(os.getenv("TELEGRAM_TIMEOUT", 10)),
        )

    @classmethod
    def from_dict(cls, config_dict: Mapping[str, Any]) -> "TelegramConfig":
        return cls(
            bot_token=str(config_dict.get("bot_token", "")),
            chat_id=str(config_dict.get("chat_id", "")),
            timeout=int(config_dict.get("timeout", 10)),
        )


def send_message(config: TelegramConfig, text: str) -> dict:
    """
    send message to telegram chat... dead simple...

    :param config: Telegram configuration object
    :type config: TelegramConfig
    :param text: Message text to send, markdown for formatting if desired
    :type text: str
    :return: Response from Telegram API
    :rtype: dict[Any, Any]
    """
    url = f"https://api.telegram.org/bot{config.bot_token}/sendMessage"
    payload = {
        "chat_id": config.chat_id,
        "text": text,
        "parse_mode": "HTML",  # or HTML
    }
    r = requests.post(
        url,
        json=payload,
        timeout=config.timeout,
    )
    if not r.ok:
        # IMPORTANT: don't log the URL (it contains the token)
        raise RuntimeError(f"Telegram send failed: {r.status_code} {r.text}")
    
    r.raise_for_status()
    return r.json()
