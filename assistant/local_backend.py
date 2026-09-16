"""Локальный поиск и ответ, если нет OPENAI_API_KEY. Интерфейс как у кода урока."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Tuple

from embeddings import get_sample_documents, load_documents_from_folder


class _Count:
    def __init__(self, store: "EmbeddingStore"):
        self._store = store

    def count(self) -> int:
        return self._store.count()


class EmbeddingStore:
    def __init__(
        self,
        collection_name: str = "rag_documents",
        persist_directory: str = "./chroma_db",
        embedding_model: str = "local",
        api_key: Optional[str] = None,
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self._chunks: List[Tuple[str, str]] = []
        self.collection = _Count(self)
        print("Хранилище: локальный поиск по docs/")

    def count(self) -> int:
        return len(self._chunks)

    def _create_chunks(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = max(end - overlap, start + 1)
        return chunks

    def add_documents(self, documents: List[Tuple[str, str]]) -> None:
        print(f"\nДобавление {len(documents)} документов...")
        for doc_name, doc_text in documents:
            chunks = self._create_chunks(doc_text)
            print(f"  • {doc_name}: {len(chunks)} чанков")
            for chunk in chunks:
                self._chunks.append((chunk, doc_name))

    def _tokenize(self, text: str) -> set:
        return set(re.findall(r"[а-яёa-z0-9]+", text.lower()))

    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, str, float]]:
        q_tokens = self._tokenize(query)
        scored: List[Tuple[str, str, float]] = []
        for chunk, source in self._chunks:
            tokens = self._tokenize(chunk)
            if not tokens:
                continue
            overlap = len(q_tokens & tokens)
            distance = 1.0 - (overlap / max(len(q_tokens), 1))
            scored.append((chunk, source, distance))
        scored.sort(key=lambda item: item[2])
        return scored[:top_k]


class RAGAssistant:
    def __init__(self, embedding_store, api_key=None, model="local", temperature=0.7):
        self.embedding_store = embedding_store
        self.model = model
        self.temperature = temperature
        print("RAG-ассистент: ответ по найденному контексту, без облака")

    def generate_response(self, query: str, top_k: int = 3, verbose: bool = True):
        if verbose:
            print(f"\nПоиск релевантных документов (top_k={top_k})...")
        search_results = self.embedding_store.search(query, top_k=top_k)
        if verbose and search_results:
            print(f"Найдено {len(search_results)} фрагментов:")
            for i, (chunk, source, distance) in enumerate(search_results, 1):
                print(f"  {i}. [{source}] (similarity: {1 - distance:.3f})")
                print(f"     {chunk[:100]}...")
        if not search_results or search_results[0][2] > 0.85:
            answer = (
                "В базе нет надёжного ответа. Передайте вопрос человеку — "
                "сложные случаи ассистент не закрывает."
            )
            return answer, search_results
        top = [item for item in search_results if item[2] <= 0.85][:2]
        text = " ".join(top[0][0].split())
        sources = ", ".join(sorted({item[1] for item in top}))
        answer = (
            f"{text}\n\nИсточник в базе: {sources}. "
            "Если случай сложный — напишите в форму на сайте."
        )
        return answer, search_results
