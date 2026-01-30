from __future__ import annotations

from typing import Any, Dict

import requests
from requests import Response

from ...config import RegardsConfig
from ...domain.exceptions import RegardsAuthError


def request_token(config: RegardsConfig) -> str:
    """
    Fetch OAuth token from REGARDS.

    Endpoint:
      /api/v1/rs-authentication/oauth/token
    """
    if not config.username or not config.password:
        raise RegardsAuthError(
            "REGARDS credentials are missing. Please set REGARDS_USERNAME and REGARDS_PASSWORD."
        )

    url = f"{config.base_url}/api/v1/rs-authentication/oauth/token"
    payload: Dict[str, str] = {
        "grant_type": "password",
        "username": config.username,
        "password": config.password,
        "scope": config.tenant,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic Y2xpZW50OnNlY3JldA==",
    }

    try:
        response: Response = requests.post(url, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        return str(data["access_token"])
    except Exception as exc:
        raise RegardsAuthError(f"Could not obtain REGARDS token: {exc}") from exc
