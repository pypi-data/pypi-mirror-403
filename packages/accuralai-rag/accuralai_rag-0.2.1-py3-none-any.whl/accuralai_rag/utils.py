"""Utility helpers shared across the accuralai-rag modules."""

from __future__ import annotations

import hashlib
import math
from typing import Iterable, Optional, Sequence

try:  # Optional dependency used only when available
    import numpy as np
except Exception:  # pragma: no cover - numpy missing in minimal envs
    np = None  # type: ignore[assignment]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity that falls back to pure Python if numpy is absent."""

    if np is not None:
        a_arr = np.asarray(a, dtype="float32")
        b_arr = np.asarray(b, dtype="float32")
        denom = float(np.linalg.norm(a_arr) * np.linalg.norm(b_arr))
        if denom == 0:
            return 0.0
        return float(np.dot(a_arr, b_arr) / denom)

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def normalize_vector(vec: Sequence[float]) -> Sequence[float]:
    if np is not None:
        arr = np.asarray(vec, dtype="float32")
        norm = np.linalg.norm(arr)
        return arr if norm == 0 else arr / norm
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def stable_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def maybe_to_numpy(batch: Sequence[Sequence[float]]):
    if np is None:
        return batch
    return np.asarray(batch, dtype="float32")


__all__ = [
    "cosine_similarity",
    "normalize_vector",
    "stable_hash",
    "maybe_to_numpy",
]
