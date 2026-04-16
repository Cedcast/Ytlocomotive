"""
distributors/telegram_bot.py
Distributes content to Telegram via the Bot API using direct HTTP requests.
"""
import requests

import config
from utils.logger import get_logger

logger = get_logger(__name__)

def send_message(text: str) -> bool:
    """Sends a Markdown text message to the configured Telegram chat."""
    try:
        resp = requests.post(
            f"{config.TELEGRAM_API_BASE}/sendMessage",
            json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"},
            timeout=30,
        )
        resp.raise_for_status()
        logger.info("Telegram message sent.")
        return True
    except Exception as exc:
        logger.error(f"Telegram sendMessage failed: {exc}")
        return False

def send_video(video_path: str, caption: str) -> bool:
    """Sends a video file with caption to the configured Telegram chat."""
    try:
        with open(video_path, "rb") as vf:
            resp = requests.post(
                f"{config.TELEGRAM_API_BASE}/sendVideo",
                data={
                    "chat_id": config.TELEGRAM_CHAT_ID,
                    "caption": caption[:1024],
                    "parse_mode": "Markdown",
                    "supports_streaming": "true",
                },
                files={"video": vf},
                timeout=120,
            )
        resp.raise_for_status()
        logger.info(f"Telegram video sent: {video_path}")
        return True
    except Exception as exc:
        logger.error(f"Telegram sendVideo failed: {exc}")
        return False
