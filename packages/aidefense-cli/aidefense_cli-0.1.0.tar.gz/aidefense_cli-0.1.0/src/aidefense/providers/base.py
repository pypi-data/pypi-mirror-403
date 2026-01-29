from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from typing import Any


class BaseProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[dict[str, Any]], *, stream: bool) -> str | Iterable[str]:
        raise NotImplementedError

    def stream(self, messages: list[dict[str, Any]]) -> Iterator[str]:
        chunks = self.complete(messages, stream=True)
        if isinstance(chunks, str):
            yield chunks
            return
        yield from chunks

    def complete_text(self, messages: list[dict[str, Any]]) -> str:
        result = self.complete(messages, stream=False)
        if isinstance(result, str):
            return result
        return "".join(result)
