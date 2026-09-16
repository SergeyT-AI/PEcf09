"""Telegram-бот RAG-ассистента из урока PEcf09.

Ассистент отвечает только здесь, не на сайте. Пайплайн: кеш → RAG → logs.db.
"""

import os
import time

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from cache import ResponseCache
from db_logger import DatabaseLogger
from runtime import answer_question


class TelegramRAGBot:
    def __init__(self, token: str, rag_assistant, cache: ResponseCache, logger: DatabaseLogger):
        self.rag_assistant = rag_assistant
        self.cache = cache
        self.logger = logger
        self.application = Application.builder().token(token).build()
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        self.application.add_handler(CommandHandler("logs", self.logs_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_message = """
Добро пожаловать.

Я отвечаю на вопросы про Python и RAG. Спрашивайте, что такое Python, как хранятся эмбеддинги и как ассистент находит фрагменты в документах.

Команды:
/help — справка
/stats — метрики из логов
/logs — выгрузка ваших логов в CSV

Напишите вопрос обычным сообщением.
        """
        await update.message.reply_text(welcome_message.strip())

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
Как я работаю:

• Вопрос идёт в базу знаний (Python, векторные базы, RAG)
• Повтор берётся из кеша
• Каждый диалог пишется в SQLite: без ФИО и телефонов, только идентификатор, текст и время

Команды:
/start — начать
/help — эта справка
/stats — документы, кеш, среднее время
/logs — CSV ваших обращений

Примеры:
• Что такое Python?
• Как работает RAG?
• Зачем нужны векторные базы данных?
        """
        await update.message.reply_text(help_text.strip())

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            doc_count = self.rag_assistant.embedding_store.collection.count()
            cache_size = self.cache.size()
            model = self.rag_assistant.model
            log_stats = self.logger.get_stats()
            stats_message = f"""
Статистика системы:

База знаний:
  • документов: {doc_count}
  • модель: {model}

Кеш:
  • записей: {cache_size}

Логи:
  • всего запросов: {log_stats['total_requests']}
  • из кеша: {log_stats['cached_requests']}
  • уникальных пользователей: {log_stats['unique_users']}
  • среднее время ответа: {log_stats['avg_response_time_ms']:.0f} мс
            """
            await update.message.reply_text(stats_message.strip())
        except Exception as e:
            await update.message.reply_text(f"Ошибка при получении статистики: {e}")

    async def logs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            user_id = str(update.effective_user.id)
            csv_content = self.logger.export_to_csv(user_id=user_id)
            if not csv_content:
                await update.message.reply_text("Логов для вашего пользователя не найдено.")
                return
            filename = f"logs_{user_id}_{int(time.time())}.csv"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(csv_content)
            with open(filename, "rb") as f:
                await update.message.reply_document(
                    document=f,
                    filename=filename,
                    caption="Ваши логи взаимодействий с ботом",
                )
            os.remove(filename)
        except Exception as e:
            await update.message.reply_text(f"Ошибка при экспорте логов: {e}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        user = update.effective_user
        user_id = str(user.id)
        username = user.username or user.first_name or "Unknown"
        await update.message.chat.send_action(action="typing")
        try:
            answer, from_cache, _elapsed = answer_question(
                query=user_message,
                rag_assistant=self.rag_assistant,
                cache=self.cache,
                logger=self.logger,
                source="telegram",
                user_id=user_id,
                username=username,
                verbose=False,
            )
            max_length = 4000
            if len(answer) <= max_length:
                await update.message.reply_text(answer)
            else:
                parts = [answer[i : i + max_length] for i in range(0, len(answer), max_length)]
                for i, part in enumerate(parts):
                    await update.message.reply_text(part)
            if from_cache:
                await update.message.reply_text("(ответ из кеша)")
        except Exception as e:
            error_message = f"Произошла ошибка при обработке запроса: {e}"
            await update.message.reply_text(error_message)
            self.logger.log_interaction(
                query=user_message,
                response=error_message,
                source="telegram",
                user_id=user_id,
                username=username,
                from_cache=False,
                response_time_ms=0,
            )

    def run(self):
        print("Запуск Telegram бота...")
        print("Бот готов к работе. Нажмите Ctrl+C для остановки.")
        self.application.run_polling()
