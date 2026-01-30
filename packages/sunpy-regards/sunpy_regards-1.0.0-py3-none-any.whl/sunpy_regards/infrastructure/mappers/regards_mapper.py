from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sunpy.time import parse_time  # NOTE: this is okay in infra mapper; domain/app stay SunPy-free

from ...application.dto import ProductDTO

_WAVE_KEY_TOKENS = ("wav", "wave")


def _as_float(v: Any) -> float | None:
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except Exception:
            return None
    return None


def extract_wavelength_numbers(
    obj: Any,
    *,
    key_tokens: Tuple[str, ...] = _WAVE_KEY_TOKENS,
    dedup: bool = False,
) -> List[float]:
    out: List[float] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(k, str):
                    lk = k.lower()
                    if any(tok in lk for tok in key_tokens):
                        if isinstance(v, list):
                            for it in v:
                                fv = _as_float(it)
                                if fv is not None:
                                    out.append(fv)
                        else:
                            fv = _as_float(v)
                            if fv is not None:
                                out.append(fv)
                walk(v)
        elif isinstance(x, list):
            for it in x:
                walk(it)

    walk(obj)

    if dedup:
        seen: set[float] = set()
        uniq: List[float] = []
        for w in out:
            if w not in seen:
                uniq.append(w)
                seen.add(w)
        return uniq

    return out


def extract_register_values(js: Dict[str, Any]) -> dict[str, list[tuple[str, str]]]:
    items = js.get("content") or []
    dataset_map: Dict[str, str] = {}
    instrument_map: Dict[str, str] = {}
    observatory_map: Dict[str, str] = {}

    for item in items:
        content = item.get("content") or {}
        feature = content.get("feature") or {}
        props = feature.get("properties") or {}

        dataset_name = props.get("dataset_name")
        instrument = props.get("instrument")
        observatory = props.get("observatory")
        label = feature.get("label") or dataset_name or ""

        if dataset_name:
            dataset_map.setdefault(dataset_name, f"{label} dataset in REGARDS (MEDOC)")
        if instrument:
            instrument_map.setdefault(
                instrument, f"{instrument} on {observatory}" if observatory else instrument
            )
        if observatory:
            observatory_map.setdefault(observatory, f"{observatory} mission")

    return {
        "datasets": sorted(dataset_map.items()),
        "instruments": sorted(instrument_map.items()),
        "observatories": sorted(observatory_map.items()),
    }


def json_to_products(
    js: Dict[str, Any],
    *,
    base_url: str,
    tenant: Optional[str],
) -> List[ProductDTO]:
    TARGET_KEYS = (
        "observatory",
        "instrument",
        "dataset_name",
        "dataset",
        "date_obs",
        "timeStart",
        "start_time",
    )

    def find_props(d: Any) -> Dict[str, Any] | None:
        if not isinstance(d, dict):
            return None
        if any(k in d for k in TARGET_KEYS):
            return d
        for v in d.values():
            if isinstance(v, dict):
                found = find_props(v)
                if found is not None:
                    return found
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        found = find_props(item)
                        if found is not None:
                            return found
        return None

    def find_urn(d: Any) -> str | None:
        if not isinstance(d, dict):
            return None
        if "urn" in d:
            return str(d["urn"])
        if "id" in d:
            return str(d["id"])
        for v in d.values():
            if isinstance(v, dict):
                res = find_urn(v)
                if res is not None:
                    return res
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        res = find_urn(item)
                        if res is not None:
                            return res
        return None

    def find_files(d: Any) -> Dict[str, Any] | None:
        if not isinstance(d, dict):
            return None
        if "files" in d and isinstance(d["files"], dict):
            return d["files"]
        for v in d.values():
            if isinstance(v, dict):
                res = find_files(v)
                if res is not None:
                    return res
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        res = find_files(item)
                        if res is not None:
                            return res
        return None

    if "content" in js:
        items = js.get("content") or []
    elif "features" in js:
        items = js.get("features") or []
    else:
        return []

    out: List[ProductDTO] = []
    base_url = base_url.rstrip("/")

    for item in items:
        props = find_props(item) or {}
        files = find_files(item) or {}

        obs = props.get("observatory")
        inst = props.get("instrument")
        dset = props.get("dataset_name") or props.get("dataset")

        start = props.get("date_obs") or props.get("timeStart") or props.get("start_time")
        end = props.get("date_end") or start

        urn = find_urn(item)

        if start is not None:
            try:
                start = parse_time(start).isot
            except Exception:
                start = str(start)
        if end is not None:
            try:
                end = parse_time(end).isot
            except Exception:
                end = str(end)

        download_url: str | None = None
        file_id: str | None = None
        raw_uri: str | None = None
        filename: str | None = None

        if isinstance(files, dict):
            raw_list = files.get("RAWDATA") or []
            if isinstance(raw_list, list) and raw_list:
                raw = raw_list[0]
                raw_uri = raw.get("uri")
                filename = raw.get("filename")
                file_id_any = raw.get("data_item_oid") or raw.get("id") or raw.get("oid")
                if file_id_any is not None:
                    file_id = str(file_id_any)

        if raw_uri:
            download_url = str(raw_uri)
        elif urn and file_id:
            if tenant:
                download_url = (
                    f"{base_url}/api/v1/rs-catalog/{tenant}/downloads/{urn}/files/{file_id}"
                )
            else:
                download_url = f"{base_url}/api/v1/rs-catalog/downloads/{urn}/files/{file_id}"

        if filename is None:
            filename = props.get("filename")

        extra = dict(props)

        # optional: wavelength fallback hint in extra
        if (
            extra.get("wavemin") is None
            and extra.get("wavelength_min") is None
            and extra.get("wave_min") is None
        ):
            waves = extract_wavelength_numbers(item, dedup=True)
            if waves:
                extra["wavemin_fallback"] = min(waves)

        out.append(
            ProductDTO(
                observatory=obs,
                instrument=inst,
                dataset=dset,
                start_time=start,
                end_time=end,
                urn=urn,
                download_url=download_url,
                filename=filename,
                extra=extra,
            )
        )

    return out
