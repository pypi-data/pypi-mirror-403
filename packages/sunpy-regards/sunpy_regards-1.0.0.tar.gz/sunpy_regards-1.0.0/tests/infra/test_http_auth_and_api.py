from __future__ import annotations

import pytest

from sunpy_regards.config import RegardsConfig
from sunpy_regards.domain.exceptions import RegardsApiError, RegardsAuthError
from sunpy_regards.infrastructure.http.auth import request_token
from sunpy_regards.infrastructure.http.regards_client import RegardsApi


class FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status
        self.content = b"BYTES"

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload

    def iter_content(self, chunk_size=1024):
        yield self.content


def test_request_token_success(monkeypatch):
    import requests

    def fake_post(url, data=None, headers=None, timeout=None):
        return FakeResp({"access_token": "TOK"}, status=200)

    monkeypatch.setattr(requests, "post", fake_post)

    cfg = RegardsConfig(
        base_url="https://regards.example", username="u", password="p", tenant="Solar"
    )
    tok = request_token(cfg)
    assert tok == "TOK"


def test_request_token_missing_credentials_raises():
    cfg = RegardsConfig(
        base_url="https://regards.example", username="", password="", tenant="Solar"
    )
    with pytest.raises(RegardsAuthError):
        request_token(cfg)


def test_regards_api_search_mocked(monkeypatch):
    import requests

    cfg = RegardsConfig(
        base_url="https://regards.example", username="u", password="p", tenant="Solar"
    )
    api = RegardsApi(cfg)
    api._token = "FAKE"  # évite auth

    payload = {
        "content": [
            {
                "urn": "URN:AIP:DATA:Solar:TEST-URN:V1",
                "content": {"feature": {"properties": {"observatory": "SDO", "instrument": "AIA"}}},
                "files": {"RAWDATA": [{"uri": "https://example/file", "filename": "x.fits"}]},
            }
        ]
    }

    def fake_get(url, headers=None, params=None, timeout=None, stream=False):
        return FakeResp(payload, status=200)

    monkeypatch.setattr(requests, "get", fake_get)

    out = api.search(q='properties.instrument:"AIA"', page=0, size=10)
    assert len(out) == 1
    assert out[0].instrument == "AIA"


def test_regards_api_download_bytes_mocked(monkeypatch):
    import requests

    cfg = RegardsConfig(
        base_url="https://regards.example", username="u", password="p", tenant="Solar"
    )
    api = RegardsApi(cfg)
    api._token = "FAKE"

    def fake_get(url, headers=None, timeout=None, stream=False):
        r = FakeResp({}, status=200)
        r.content = b"HELLO"
        return r

    monkeypatch.setattr(requests, "get", fake_get)

    data = api.download_bytes(url="https://regards.example/file")
    assert data == b"HELLO"


def test_regards_api_search_error(monkeypatch):
    import requests

    cfg = RegardsConfig(
        base_url="https://regards.example", username="u", password="p", tenant="Solar"
    )
    api = RegardsApi(cfg)
    api._token = "FAKE"

    def fake_get(url, headers=None, params=None, timeout=None, stream=False):
        return FakeResp({"x": "y"}, status=500)

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(RegardsApiError):
        api.search(q="x", page=0, size=10)
