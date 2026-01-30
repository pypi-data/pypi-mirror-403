from __future__ import annotations

import sunpy.net.attrs as a

from sunpy_regards.adapters.sunpy._attrs import Dataset, Observatory
from sunpy_regards.adapters.sunpy.client import REGARDSClient


def test_register_values_fallback_when_no_env(monkeypatch):
    # Ensure env vars are not set so RegardsConfig.from_env() fails
    monkeypatch.delenv("REGARDS_USERNAME", raising=False)
    monkeypatch.delenv("REGARDS_PASSWORD", raising=False)
    monkeypatch.delenv("REGARDS_BASE_URL", raising=False)
    monkeypatch.delenv("REGARDS_TENANT", raising=False)

    values = REGARDSClient.register_values()

    assert Dataset in values
    assert a.Instrument in values
    assert Observatory in values
    assert a.Provider in values

    # Fallback must contain at least one element
    assert len(values[Dataset]) >= 1
    assert len(values[a.Instrument]) >= 1
    assert len(values[Observatory]) >= 1

    # Provider should include REGARDS
    providers = [v for (v, _desc) in values[a.Provider]]
    assert any(str(p).lower() == "regards" for p in providers)
