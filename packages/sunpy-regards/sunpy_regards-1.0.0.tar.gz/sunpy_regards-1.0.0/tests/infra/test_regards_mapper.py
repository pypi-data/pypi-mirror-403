from __future__ import annotations

import json
from pathlib import Path

from sunpy_regards.infrastructure.mappers.regards_mapper import json_to_products


def test_json_to_products_minimal_fixture():
    p = Path(__file__).parent / "fixtures" / "regards_search_sample.json"
    js = json.loads(p.read_text(encoding="utf-8"))

    out = json_to_products(js, base_url="https://regards.example", tenant="Solar")
    assert isinstance(out, list)
    assert len(out) >= 1

    first = out[0]
    assert first.download_url is not None
    assert first.urn is not None
