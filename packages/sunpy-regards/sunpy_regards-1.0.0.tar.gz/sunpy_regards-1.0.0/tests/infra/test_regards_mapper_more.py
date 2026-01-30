from __future__ import annotations

from sunpy_regards.infrastructure.mappers.regards_mapper import (
    extract_register_values,
    extract_wavelength_numbers,
    json_to_products,
)


def test_extract_wavelength_numbers_nested():
    payload = {
        "a": {"wave_min": "171", "other": [{"wavemin": 193}, {"x": {"wavelength_min": 211}}]}
    }
    out = extract_wavelength_numbers(payload, dedup=True)
    assert set(out) >= {171.0, 193.0, 211.0}


def test_extract_register_values_empty():
    out = extract_register_values({"content": []})
    assert out["datasets"] == []
    assert out["instruments"] == []
    assert out["observatories"] == []


def test_json_to_products_handles_unknown_shape():
    out = json_to_products({"unexpected": 123}, base_url="https://x", tenant="Solar")
    assert out == []
