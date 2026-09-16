"""
Сборка ассистента из урока: db_logger, cache, RAG, log_interaction.

Если есть OPENAI_API_KEY — эмбеддинги и ответы через ProxyAPI (OpenAI-совместимый API).
Без ключа — тот же пайплайн логирования, локальный поиск по docs/.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cache import ResponseCache
from db_logger import DatabaseLogger
from embeddings import get_sample_documents

ASSISTANT_DIR = ROOT
CACHE_FILE = ASSISTANT_DIR / "cache.json"
LOGS_DB = ASSISTANT_DIR / "logs.db"
CHROMA_DIR = ASSISTANT_DIR / "chroma_db"


def initialize_system():
    print("=" * 70)
    print("ИНИЦИАЛИЗАЦИЯ RAG-АССИСТЕНТА")
    print("=" * 70)

    load_dotenv(ROOT.parent / ".env")
    load_dotenv(ROOT / ".env")
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if api_key in {"your_openai_api_key_here", ""}:
        api_key = ""

    print("\n[1/4] Инициализация кеша...")
    cache = ResponseCache(cache_file=str(CACHE_FILE))

    print("\n[2/4] Инициализация векторного хранилища...")
    if api_key:
        from embeddings import EmbeddingStore
        from rag import RAGAssistant

        embedding_store = EmbeddingStore(
            collection_name="rag_documents",
            persist_directory=str(CHROMA_DIR),
            embedding_model="text-embedding-3-small",
            api_key=api_key,
        )
        rag_assistant = None
        model_name = os.getenv("MODEL_NAME", "gpt-4o")
        from openai_client import openai_base_url, use_proxyapi

        backend = "ProxyAPI" if use_proxyapi() else "OpenAI напрямую"
        print(f"LLM: {model_name} через {backend} ({openai_base_url()})")
    else:
        print("OPENAI_API_KEY нет — локальный поиск по docs/, логи те же.")
        from local_backend import EmbeddingStore, RAGAssistant as LocalRAG

        embedding_store = EmbeddingStore()
        rag_assistant = LocalRAG(embedding_store)
        model_name = "local"

    if embedding_store.collection.count() == 0:
        print("\nБаза пуста. Добавляем документы из docs/...")
        embedding_store.add_documents(get_sample_documents())
    else:
        print(f"В базе уже есть {embedding_store.collection.count()} документов")

    print("\n[3/4] Инициализация RAG-ассистента...")
    if api_key:
        from rag import RAGAssistant

        rag_assistant = RAGAssistant(
            embedding_store=embedding_store,
            api_key=api_key,
            model=model_name,
            temperature=0.7,
        )

    print("\n[4/4] Инициализация логгера базы данных...")
    logger = DatabaseLogger(db_path=str(LOGS_DB))
    print("Логгер инициализирован")

    print("\n" + "=" * 70)
    print("СИСТЕМА ГОТОВА К РАБОТЕ")
    print("=" * 70)
    return embedding_store, rag_assistant, cache, logger


def answer_question(
    query: str,
    rag_assistant,
    cache: ResponseCache,
    logger: DatabaseLogger,
    source: str = "console",
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    verbose: bool = True,
) -> str:
    """Пайплайн из main.py урока: кеш → RAG → log_interaction."""
    if verbose:
        print("\n" + "=" * 70)
        print(f"ВОПРОС: {query}")
        print("=" * 70)

    start_time = time.time()

    if verbose:
        print("\n[Шаг 1] Проверка кеша...")
    cached_answer = cache.get(query)
    from_cache = cached_answer is not None

    if cached_answer:
        if verbose:
            print("\nОтвет из кеша:")
            print("-" * 70)
            print(cached_answer)
            print("-" * 70)
        answer = cached_answer
    else:
        if verbose:
            print("\n[Шаг 2] Выполнение RAG (поиск + генерация)...")
        try:
            answer, _search_results = rag_assistant.generate_response(
                query=query,
                top_k=3,
                verbose=verbose,
            )
            if verbose:
                print("\n[Шаг 3] Сохранение ответа в кеш...")
            cache.set(query, answer)
            if verbose:
                print("\nОТВЕТ:")
                print("-" * 70)
                print(answer)
                print("-" * 70)
        except Exception as e:
            answer = f"Ошибка при обработке запроса: {e}"
            if verbose:
                print(f"\n{answer}")

    response_time_ms = int((time.time() - start_time) * 1000)
    logger.log_interaction(
        query=query,
        response=answer,
        source=source,
        user_id=user_id,
        username=username,
        from_cache=from_cache,
        response_time_ms=response_time_ms,
    )
    return answer, from_cache, response_time_ms
