from __future__ import annotations

from typing import Protocol

from .dto import ProductDTO


class RegardsRepository(Protocol):
    def register_values(self) -> dict[str, list[tuple[str, str]]]:
        """
        Returns dynamic lists for (datasets, instruments, observatories).
        Each list is [(value, description), ...].
        """
        ...

    def search(self, *, q: str, page: int, size: int) -> list[ProductDTO]: ...

    def download_bytes(self, *, url: str) -> bytes: ...
