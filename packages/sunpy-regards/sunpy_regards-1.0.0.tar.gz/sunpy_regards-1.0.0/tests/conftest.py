from __future__ import annotations

import importlib.util

import pytest


def _has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "requires_sunpy: tests that require sunpy installed")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if _has("sunpy"):
        return

    skip = pytest.mark.skip(reason="sunpy not installed")
    for item in items:
        if "requires_sunpy" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Bloque toute tentative de réseau (requests) pendant les tests unitaires.
    """
    import requests

    def _blocked(*args, **kwargs):
        raise RuntimeError("Network is blocked in unit tests. Use integration tests for HTTP.")

    monkeypatch.setattr(requests, "get", _blocked)
    monkeypatch.setattr(requests, "post", _blocked)
    # Plus robuste: bloque aussi les appels génériques (requests.request, Session.request)
    monkeypatch.setattr(requests, "request", _blocked)
    monkeypatch.setattr(requests.sessions.Session, "request", _blocked)
