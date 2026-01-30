from __future__ import annotations

from dataclasses import dataclass

import pytest
import sunpy.net.attrs as a
from sunpy.net.base_client import QueryResponseTable

from sunpy_regards.adapters.sunpy._attrs import Dataset, Observatory
from sunpy_regards.adapters.sunpy.client import DISPLAY_COLUMNS, REGARDSClient

pytestmark = pytest.mark.requires_sunpy


@dataclass(frozen=True)
class FakeProduct:
    observatory: str | None = "SDO"
    instrument: str | None = "AIA"
    dataset: str | None = "GAIA-DEM data"
    start_time: str | None = "2020-01-01T00:00:00"
    end_time: str | None = "2020-01-01T00:10:00"
    urn: str | None = "URN:TEST:1"
    download_url: str | None = "https://example.org/file.fits"
    filename: str | None = "file.fits"
    extra: dict | None = None


class FakeSearchUC:
    def execute(self, *, q: str, page: int = 0, size: int = 500):
        return [FakeProduct(extra={"wavemin": 171.0, "xcen": 0.0, "ycen": 0.0})]


def test_search_returns_view_table_and_keeps_full_table(monkeypatch):
    client = REGARDSClient.__new__(REGARDSClient)  # bypass __init__
    client.config = type("C", (), {"base_url": "https://regards.invalid"})()
    client._uc_search = FakeSearchUC()

    res = REGARDSClient.search(
        client,
        a.Time("2020-01-01", "2020-01-02"),
        a.Instrument("AIA"),
        Dataset("GAIA-DEM data"),
        Observatory("SDO"),
        a.Provider("REGARDS"),
        page=0,
        size=10,
    )

    assert isinstance(res, QueryResponseTable)
    assert len(res) == 1

    # ✅ 1) La "vue" ne doit contenir que les colonnes affichées
    assert list(res.colnames) == [c for c in DISPLAY_COLUMNS if c in res.colnames]
    assert "Download URL" not in res.colnames
    assert "Product URN" not in res.colnames
    assert "Filename" not in res.colnames

    # ✅ 2) La table complète doit exister et contenir les colonnes cachées
    assert hasattr(res, "_regards_full_table")
    full = res._regards_full_table  # type: ignore[attr-defined]

    assert "Download URL" in full.colnames
    assert "Product URN" in full.colnames
    assert "Filename" in full.colnames

    assert full["Download URL"][0] == "https://example.org/file.fits"
    assert full["Product URN"][0] == "URN:TEST:1"
    assert full["Instrument"][0] == "AIA"
