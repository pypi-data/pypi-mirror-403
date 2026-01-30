from __future__ import annotations

from sunpy_regards.infrastructure.mappers.regards_mapper import json_to_products


def test_json_to_products_features_shape_and_fallback_download_url():
    js = {
        "features": [
            {
                "id": "URN:FEATURE:1",
                "feature": {
                    "properties": {
                        "instrument": "AIA",
                        "observatory": "SDO",
                        "date_obs": "bad-date",
                    }
                },
                "files": {"RAWDATA": [{"data_item_oid": "FILE1", "filename": "x.fits"}]},
            }
        ]
    }
    out = json_to_products(js, base_url="https://regards.example", tenant="Solar")
    assert len(out) == 1
    assert out[0].urn is not None
    # fallback URL built from urn + file_id if no uri
    assert out[0].download_url is not None
