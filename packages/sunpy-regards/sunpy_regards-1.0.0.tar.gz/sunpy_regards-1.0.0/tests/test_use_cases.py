from __future__ import annotations

from sunpy_regards.application.dto import ProductDTO
from sunpy_regards.application.use_cases import FetchProducts, RegisterValues, SearchProducts


class FakeRepo:
    def __init__(self):
        self.calls = []

    def register_values(self):
        self.calls.append(("register_values",))
        return {"datasets": [("D", "desc")], "instruments": [], "observatories": []}

    def search(self, *, q: str, page: int, size: int):
        self.calls.append(("search", q, page, size))
        return [
            ProductDTO(
                observatory="SDO",
                instrument="AIA",
                dataset="GAIA-DEM data",
                start_time="2020-01-01T00:00:00",
                end_time="2020-01-01T00:10:00",
                urn="URN:TEST",
                download_url="https://example/file",
                filename="x.fits",
                extra={},
            )
        ]

    def download_bytes(self, *, url: str) -> bytes:
        self.calls.append(("download_bytes", url))
        return b"OK"


def test_search_products_calls_repo():
    repo = FakeRepo()
    uc = SearchProducts(repo)
    out = uc.execute(q="x", page=2, size=10)
    assert len(out) == 1
    assert repo.calls[0] == ("search", "x", 2, 10)


def test_register_values_calls_repo():
    repo = FakeRepo()
    uc = RegisterValues(repo)
    out = uc.execute()
    assert out["datasets"][0][0] == "D"
    assert repo.calls[0] == ("register_values",)


def test_fetch_products_calls_repo():
    repo = FakeRepo()
    uc = FetchProducts(repo)
    data = uc.download(url="https://x")
    assert data == b"OK"
    assert repo.calls[0] == ("download_bytes", "https://x")
