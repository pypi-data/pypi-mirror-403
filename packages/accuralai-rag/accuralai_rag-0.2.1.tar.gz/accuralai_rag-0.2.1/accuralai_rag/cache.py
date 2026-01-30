"""RAG-specific caching utilities (in-memory + Redis)."""

from __future__ import annotations

import os
import pickle
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:  # Optional dependency
    import redis
except Exception:  # pragma: no cover - redis optional
    redis = None  # type: ignore[assignment]

from .utils import stable_hash


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class RAGCache:
    def __init__(self, namespace: str = "rag", default_ttl: int = 3600, redis_client: Optional[Any] = None) -> None:
        self.namespace = namespace
        self.default_ttl = default_ttl
        self._redis = redis_client or self._connect_redis()
        self._local: Dict[str, CacheEntry] = {}

    def _connect_redis(self):
        if redis is None:
            return None
        url = os.getenv("REDIS_URL")
        if not url:
            return None
        try:
            return redis.from_url(url)
        except Exception:  # pragma: no cover - optional connection failure
            return None

    # ------------------------------------------------------------------
    def make_key(self, key: str) -> str:
        return f"{self.namespace}:{stable_hash(key)}"

    def get(self, key: str) -> Any:
        namespaced = self.make_key(key)
        entry = self._local.get(namespaced)
        now = time.time()
        if entry and entry.expires_at > now:
            return entry.value
        self._local.pop(namespaced, None)
        if self._redis is None:
            return None
        raw = self._redis.get(namespaced)
        if not raw:
            return None
        try:
            return pickle.loads(raw)
        except Exception:  # pragma: no cover - invalid payload
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        expires_in = ttl or self.default_ttl
        namespaced = self.make_key(key)
        self._local[namespaced] = CacheEntry(value=value, expires_at=time.time() + expires_in)
        if self._redis is not None:
            payload = pickle.dumps(value)
            self._redis.setex(namespaced, expires_in, payload)


__all__ = ["RAGCache"]
