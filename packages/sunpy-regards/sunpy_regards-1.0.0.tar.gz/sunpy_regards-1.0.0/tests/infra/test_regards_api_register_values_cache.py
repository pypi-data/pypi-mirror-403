from __future__ import annotations

from sunpy_regards.config import RegardsConfig
from sunpy_regards.infrastructure.http.regards_client import RegardsApi


class FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


def test_register_values_cached(monkeypatch):
    import requests

    cfg = RegardsConfig(
        base_url="https://regards.example", username="u", password="p", tenant="Solar"
    )
    api = RegardsApi(cfg)
    api._token = "FAKE"  # avoid auth

    payload = {
        "content": [
            {
                "content": {
                    "feature": {
                        "label": "GAIA-DEM",
                        "properties": {
                            "dataset_name": "GAIA-DEM data",
                            "instrument": "AIA",
                            "observatory": "SDO",
                        },
                    }
                }
            }
        ]
    }

    calls = {"n": 0}

    def fake_get(url, headers=None, params=None, timeout=None, stream=False):
        calls["n"] += 1
        return FakeResp(payload, status=200)

    monkeypatch.setattr(requests, "get", fake_get)

    out1 = api.register_values()
    out2 = api.register_values()  # should use cache

    assert calls["n"] == 1  # called once only
    assert out1["datasets"][0][0] == "GAIA-DEM data"
    assert out2 == out1
