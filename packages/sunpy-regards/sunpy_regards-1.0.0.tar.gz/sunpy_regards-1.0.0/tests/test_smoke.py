from __future__ import annotations

import sunpy.net.attrs as a

from sunpy_regards.adapters.sunpy._attrs import Dataset, Observatory, walker
from sunpy_regards.adapters.sunpy.client import REGARDSClient


def test_imports_and_entrypoints():
    # Basic import + class exists
    assert REGARDSClient is not None
    assert REGARDSClient.__name__ == "REGARDSClient"


def test_attrs_module_location():
    provider, module = REGARDSClient._attrs_module()
    assert provider == "regards"
    assert module == "sunpy_regards.adapters.sunpy.attrs"


def test_attrwalker_builds_regards_query():
    q = walker.create(
        a.Time("2020-01-01", "2020-01-02")
        & a.Instrument("AIA")
        & Dataset("GAIA-DEM data")
        & Observatory("SDO")
        & a.Provider("REGARDS")
    )

    # walker.create returns a list of branches, each branch is list[str]
    assert isinstance(q, list)
    assert len(q) >= 1
    assert isinstance(q[0], list)
    assert any("properties.date_obs:[" in s for s in q[0])
    assert any('properties.instrument:"AIA"' in s for s in q[0])
    assert any('properties.dataset_name:"GAIA-DEM data"' in s for s in q[0])
    assert any('properties.observatory:"SDO"' in s for s in q[0])
