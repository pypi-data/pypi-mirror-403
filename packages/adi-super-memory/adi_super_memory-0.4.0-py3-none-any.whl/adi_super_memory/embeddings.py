from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
import hashlib, math

class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dim(self) -> int: ...
    @abstractmethod
    def embed(self, texts: List[str]) -> List[List[float]]: ...

class HashEmbeddingProvider(EmbeddingProvider):
    def __init__(self, dim: int = 256):
        self._dim = dim
    @property
    def dim(self) -> int:
        return self._dim
    def _one(self, text: str) -> List[float]:
        b = text.encode("utf-8", errors="ignore")
        seed = hashlib.sha256(b).digest()
        out = b""
        cur = seed
        while len(out) < self._dim:
            cur = hashlib.sha256(cur + seed).digest()
            out += cur
        v = [((out[i] - 128) / 128.0) for i in range(self._dim)]
        n = math.sqrt(sum(x*x for x in v)) or 1.0
        return [x / n for x in v]
    def embed(self, texts: List[str]) -> List[List[float]]:
        return [self._one(t) for t in texts]
