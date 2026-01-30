from __future__ import annotations

import pytest

from sunpy_regards.config import RegardsConfig


def test_config_from_env_raises_when_missing_credentials(monkeypatch):
    monkeypatch.delenv("REGARDS_USERNAME", raising=False)
    monkeypatch.delenv("REGARDS_PASSWORD", raising=False)

    with pytest.raises(RuntimeError):
        RegardsConfig.from_env()
