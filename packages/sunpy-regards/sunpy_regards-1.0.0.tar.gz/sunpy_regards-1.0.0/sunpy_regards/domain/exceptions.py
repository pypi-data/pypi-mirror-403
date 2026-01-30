from __future__ import annotations


class RegardsError(RuntimeError):
    """Base error for the project."""


class RegardsAuthError(RegardsError):
    """Authentication failed."""


class RegardsApiError(RegardsError):
    """HTTP/API error when calling REGARDS."""
