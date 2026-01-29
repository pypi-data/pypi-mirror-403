from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List
import threading

@dataclass
class MessageSTM:
    _kv: Dict[str, Any] = field(default_factory=dict)
    _messages: List[Dict[str, str]] = field(default_factory=list)
    _lock: threading.RLock = field(default_factory=threading.RLock)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._kv[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._kv.get(key, default)

    def add(self, role: str, content: str) -> None:
        with self._lock:
            self._messages.append({"role": role, "content": content})

    def messages(self, limit: int = 50) -> List[Dict[str, str]]:
        with self._lock:
            return list(self._messages[-limit:])

    def to_openai_messages(self, limit: int = 50) -> List[Dict[str, str]]:
        return self.messages(limit=limit)
