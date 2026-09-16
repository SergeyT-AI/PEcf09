"""
Клиент OpenAI через ProxyAPI или напрямую.

Схема как в учебном telegram-bot:
USE_PROXYAPI, PROXYAPI_BASE_URL, OPENAI_DIRECT_BASE_URL.
"""

from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

_client: Optional[OpenAI] = None
_logged = False


def _env(key: str, default: str = "") -> str:
    return (os.getenv(key, default) or default).strip()


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("true", "1", "yes", "on")


def use_proxyapi() -> bool:
    return _env_bool("USE_PROXYAPI", True)


def openai_base_url() -> str:
    proxy_url = _env("PROXYAPI_BASE_URL", "https://api.proxyapi.ru/openai/v1")
    direct_url = _env("OPENAI_DIRECT_BASE_URL", "https://api.openai.com/v1")
    return proxy_url if use_proxyapi() else direct_url


def make_openai_client(api_key: Optional[str] = None) -> OpenAI:
    global _client, _logged
    key = (api_key or _env("OPENAI_API_KEY")).strip()
    base_url = openai_base_url()
    if _client is None:
        _client = OpenAI(api_key=key, base_url=base_url)
        if not _logged:
            if use_proxyapi():
                print(f"OpenAI-клиент инициализирован через ProxyAPI: {base_url}")
            else:
                print("OpenAI-клиент инициализирован напрямую")
            _logged = True
    return _client
