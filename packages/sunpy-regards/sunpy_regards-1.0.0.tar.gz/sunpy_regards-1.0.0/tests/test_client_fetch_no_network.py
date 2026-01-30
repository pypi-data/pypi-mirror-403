from __future__ import annotations

from sunpy_regards.adapters.sunpy.client import REGARDSClient


class FakeFetchUC:
    def download(self, *, url: str) -> bytes:
        return b"DATA"


class FakeDownloader:
    def __init__(self):
        self.enqueued = []

    def enqueue_file(self, url, filename=None):
        self.enqueued.append((url, filename))


class View(list):
    """Objet itérable + attribut _regards_full_table."""


def test_fetch_uses_full_table_when_present(tmp_path):
    client = REGARDSClient.__new__(REGARDSClient)  # bypass __init__
    client.config = type("C", (), {"base_url": "https://regards.example"})()
    client._uc_fetch = FakeFetchUC()

    # vue (colonnes affichées) : volontairement sans Download URL
    view = View([{"Observatory": "SDO"}])

    # table complète attachée (celle que fetch doit utiliser)
    full = [
        {
            "Download URL": "https://regards.example/api/v1/x",
            "Filename": "x.fits",
            "Product URN": "URN:TEST",
        }
    ]
    view._regards_full_table = full  # type: ignore[attr-defined]

    dl = FakeDownloader()
    client.fetch(view, path=str(tmp_path / "{file}"), downloader=dl)

    p = tmp_path / "x.fits"
    assert p.exists()
    assert p.read_bytes() == b"DATA"
    assert dl.enqueued == []
