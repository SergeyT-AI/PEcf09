"""Запуск RAG-ассистента в Telegram. На сайт он не встраивается."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from runtime import initialize_system
from telegram_bot import TelegramRAGBot

ROOT = Path(__file__).resolve().parent


def main() -> None:
    load_dotenv(ROOT.parent / ".env")
    load_dotenv(ROOT / ".env")
    token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        print("Нет TELEGRAM_BOT_TOKEN в .env")
        print("Создайте бота у @BotFather и впишите токен.")
        return
    _store, rag_assistant, cache, logger = initialize_system()
    TelegramRAGBot(token, rag_assistant, cache, logger).run()


if __name__ == "__main__":
    main()
