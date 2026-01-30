from __future__ import annotations

from datetime import datetime, timezone

from sunpy_regards.domain.entities import Product
from sunpy_regards.domain.value_objects import TimeRange


def test_time_range_basic():
    tr = TimeRange(
        start=datetime(2020, 1, 1, tzinfo=timezone.utc),
        end=datetime(2020, 1, 2, tzinfo=timezone.utc),
    )
    assert tr.start < tr.end


def test_product_dataclass():
    p = Product(
        urn="URN:TEST",
        observatory="SDO",
        instrument="AIA",
        dataset="GAIA-DEM data",
        start_time="2020-01-01T00:00:00",
        end_time="2020-01-01T00:10:00",
        download_url="https://example/file",
        filename="file.fits",
    )
    assert p.instrument == "AIA"
    assert p.filename.endswith(".fits")
