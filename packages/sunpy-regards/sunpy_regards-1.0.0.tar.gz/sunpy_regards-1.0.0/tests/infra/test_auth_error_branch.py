from __future__ import annotations

import pytest

from sunpy_regards.config import RegardsConfig
from sunpy_regards.domain.exceptions import RegardsAuthError
from sunpy_regards.infrastructure.http.auth import request_token


def test_request_token_wraps_exception(monkeypatch):
    import requests

    def boom(*args, **kwargs):
        raise requests.RequestException("BOOM")

    monkeypatch.setattr(requests, "post", boom)

    cfg = RegardsConfig(
        base_url="https://regards.example", username="u", password="p", tenant="Solar"
    )

    with pytest.raises(RegardsAuthError):
        request_token(cfg)
