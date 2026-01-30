from __future__ import annotations

from .dto import ProductDTO
from .ports import RegardsRepository


class SearchProducts:
    def __init__(self, repo: RegardsRepository) -> None:
        self._repo = repo

    def execute(self, *, q: str, page: int = 0, size: int = 500) -> list[ProductDTO]:
        return self._repo.search(q=q, page=page, size=size)


class RegisterValues:
    def __init__(self, repo: RegardsRepository) -> None:
        self._repo = repo

    def execute(self) -> dict[str, list[tuple[str, str]]]:
        return self._repo.register_values()


class FetchProducts:
    def __init__(self, repo: RegardsRepository) -> None:
        self._repo = repo

    def download(self, *, url: str) -> bytes:
        return self._repo.download_bytes(url=url)
