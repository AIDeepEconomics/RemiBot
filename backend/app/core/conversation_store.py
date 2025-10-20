from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, Iterable, List


@dataclass(frozen=True)
class ConversationTurn:
    role: str
    message: str


class ConversationStore:
    """Almacena en memoria las últimas interacciones por contacto."""

    def __init__(self, max_turns: int = 10) -> None:
        self.max_turns = max_turns
        self._store: Dict[str, Deque[ConversationTurn]] = {}

    def append(self, contact: str, role: str, message: str) -> None:
        history = self._store.setdefault(contact, deque(maxlen=self.max_turns))
        history.append(ConversationTurn(role=role, message=message))

    def history(self, contact: str) -> List[ConversationTurn]:
        return list(self._store.get(contact, []))

    def get_recent(self, contact: str, limit: int = 10) -> List[Dict[str, str]]:
        """Retorna historial en formato compatible con LLM APIs."""
        turns = self._store.get(contact, [])
        recent = list(turns)[-limit:] if len(turns) > limit else list(turns)
        return [{"role": turn.role, "content": turn.message} for turn in recent]

    def clear(self, contact: str) -> None:
        self._store.pop(contact, None)

    def items(self) -> Iterable[tuple[str, List[ConversationTurn]]]:
        for contact, turns in self._store.items():
            yield contact, list(turns)
