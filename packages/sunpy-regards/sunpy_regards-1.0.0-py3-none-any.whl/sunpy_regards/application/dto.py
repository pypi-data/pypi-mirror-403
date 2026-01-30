from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class ProductDTO:
    observatory: Optional[str]
    instrument: Optional[str]
    dataset: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    urn: Optional[str]
    download_url: Optional[str]
    filename: Optional[str]
    extra: dict[str, Any]
