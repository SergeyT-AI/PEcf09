import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

SECRET_KEY = "pecf08-homework-secret"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
DATABASE = "contacts.db"

TELEGRAM_BOT_USERNAME = (os.getenv("TELEGRAM_BOT_USERNAME") or "example_bases_bot").strip().lstrip("@")
TELEGRAM_BOT_URL = (os.getenv("TELEGRAM_BOT_URL") or f"https://t.me/{TELEGRAM_BOT_USERNAME}").rstrip("/")
TELEGRAM_BOT_HANDLE = f"@{TELEGRAM_BOT_USERNAME}"


def _env(key: str, default: str = "") -> str:
    return (os.getenv(key, default) or default).strip()


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return str(raw).strip().lower() in ("true", "1", "yes", "on")


# --- OpenAI / ProxyAPI (ассистент в Telegram) ---
OPENAI_API_KEY = _env("OPENAI_API_KEY")
USE_PROXYAPI = _env_bool("USE_PROXYAPI", True)
PROXYAPI_BASE_URL = _env("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
OPENAI_DIRECT_BASE_URL = _env("OPENAI_DIRECT_BASE_URL", "https://api.openai.com/v1")
OPENAI_BASE_URL = PROXYAPI_BASE_URL if USE_PROXYAPI else OPENAI_DIRECT_BASE_URL
MODEL_NAME = _env("MODEL_NAME", "gpt-4o")
