# Лендинг PEcf08 + Telegram-ассистент PEcf09

Сайт из домашнего задания **PEcf08** (Flask, форма, админка) остаётся витриной. Ассистент из урока **PEcf09** отвечает только в Telegram: кеш, RAG, `logs.db`, команды `/stats` и `/logs`.

Первый кейс на лендинге описывает эту схему и ведёт на бота.

Живой стенд:

- сайт: http://91.132.196.180/
- бот: https://t.me/example_bases_bot
- код: https://github.com/SergeyT-AI/PEcf09

Файл `.env` в репозиторий не входит. Скопируйте `.env.example` и подставьте свои ключи.

## Сайт

```
cd homework/site
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Сайт: http://127.0.0.1:5050/

Админка: http://127.0.0.1:5050/admin/login — `admin` / `admin123`

Юзернейм бота на лендинге берётся из `TELEGRAM_BOT_USERNAME` в `.env`. Ссылка: `https://t.me/<username>`.

## Telegram-бот

В `.env` нужны `TELEGRAM_BOT_TOKEN` (от @BotFather) и `TELEGRAM_BOT_USERNAME`.

```
cd homework/site/assistant
python run_telegram.py
```

Без `OPENAI_API_KEY` поиск идёт по файлам урока в `assistant/docs/` (Python, векторные базы, RAG), логирование то же. С ключом эмбеддинги и ответы идут через ProxyAPI (`https://api.proxyapi.ru/openai/v1`), как в учебном telegram-bot. Переключение: `USE_PROXYAPI=true|false`.

## Что внутри

| Путь | Откуда |
|---|---|
| `templates/`, `static/`, форма, админка | сайт PEcf08 |
| `assistant/db_logger.py`, `cache.py`, `embeddings.py`, `rag.py`, `telegram_bot.py`, `main.py` | код урока PEcf09 |
| `assistant/run_telegram.py`, `runtime.py` | запуск бота с тем же пайплайном логов |
| `assistant/docs/` | база знаний бота: Python, векторные базы, RAG и логи урока |
