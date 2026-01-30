from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from requests import Response

from ...application.dto import ProductDTO
from ...application.ports import RegardsRepository
from ...config import RegardsConfig
from ...domain.exceptions import RegardsApiError
from ..mappers.regards_mapper import extract_register_values, json_to_products
from .auth import request_token


@dataclass
class RegardsApi(RegardsRepository):
    """
    Concrete REGARDS repository (HTTP).

    Implements:
      - register_values() via /api/v1/rs-dam/datasets
      - search() via /api/v1/rs-access-project/dataobjects/search
      - download_bytes() via GET download URL
    """

    config: RegardsConfig
    _token: Optional[str] = None
    _register_cache: Optional[dict[str, list[tuple[str, str]]]] = None

    def _get_token(self) -> str:
        if self._token is None:
            self._token = request_token(self.config)
        return self._token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._get_token()}"}

    def register_values(self) -> dict[str, list[tuple[str, str]]]:
        if self._register_cache is not None:
            return self._register_cache

        url = f"{self.config.base_url}/api/v1/rs-dam/datasets"
        params: Dict[str, Any] = {"page": 0, "size": 100}

        try:
            response: Response = requests.get(
                url, headers=self._headers(), params=params, timeout=60
            )
            response.raise_for_status()
            js: Dict[str, Any] = response.json()
            self._register_cache = extract_register_values(js)
            return self._register_cache
        except Exception:
            # fallback empty => adapter will provide static fallback
            self._register_cache = {"datasets": [], "instruments": [], "observatories": []}
            return self._register_cache

    def search(self, *, q: str, page: int, size: int) -> list[ProductDTO]:
        url = f"{self.config.base_url}/api/v1/rs-access-project/dataobjects/search"
        params: Dict[str, Any] = {"page": page, "size": size}
        if q.strip():
            params["q"] = q

        try:
            response: Response = requests.get(
                url, headers=self._headers(), params=params, timeout=60
            )
            response.raise_for_status()
            js: Dict[str, Any] = response.json()
            return json_to_products(js, base_url=self.config.base_url, tenant=self.config.tenant)
        except Exception as exc:
            raise RegardsApiError(f"REGARDS search failed: {exc}") from exc

    def download_bytes(self, *, url: str) -> bytes:
        try:
            response: Response = requests.get(
                url, headers=self._headers(), timeout=120, stream=False
            )
            response.raise_for_status()
            return response.content
        except Exception as exc:
            raise RegardsApiError(f"Download failed: {exc}") from exc
