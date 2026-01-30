from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Product:
    urn: Optional[str]
    observatory: Optional[str]
    instrument: Optional[str]
    dataset: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    download_url: Optional[str]
    filename: Optional[str]
