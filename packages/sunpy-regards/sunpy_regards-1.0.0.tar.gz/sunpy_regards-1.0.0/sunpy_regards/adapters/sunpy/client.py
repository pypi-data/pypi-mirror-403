"""
sunpy_regards.adapters.sunpy.client

SunPy/Fido client for accessing REGARDS (MEDOC/Solar) data via the API:

  - /api/v1/rs-authentication/oauth/token
  - /api/v1/rs-access-project/dataobjects/search
  - /api/v1/rs-dam/datasets
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple
from urllib.parse import urlparse

import astropy.table
import requests
import sunpy.net.attrs as a
import urllib3
from requests import Response
from sunpy import log
from sunpy.net.attr import and_
from sunpy.net.base_client import BaseClient, QueryResponseTable

from ...application.use_cases import FetchProducts, RegisterValues, SearchProducts
from ...config import RegardsConfig
from ...infrastructure.http.regards_client import RegardsApi
from ._attrs import Dataset, Observatory, walker

__all__ = ["REGARDSClient"]

MetadataMap = Dict[str, List[Tuple[str, str]]]

# ---------------------------------------------------------------------
# Presentation policy (SunPy adapter only): keep columns in data,
# but limit what gets displayed when user prints QueryResponseTable.
# ---------------------------------------------------------------------

DISPLAY_COLUMNS = [
    "Observatory",
    "Instrument",
    "Dataset",
    "Start time",
    "End time",
    "Wavelength [Å] (minimum)",
    "X-center [arcsec]",
    "Y-center [arcsec]",
]

# Explicitly hide these even if present; they remain accessible by indexing.
HIDE_COLUMNS = [
    "Product URN",
    "Download URL",
    "Filename",
    "Wavelength type",
    "Scientific objective",
    "Data type",
    "Sun distance",
]


class REGARDSClient(BaseClient):
    """
    SunPy client for the REGARDS archive (MEDOC/Solar tenant).
    """

    def __init__(self, config: RegardsConfig | None = None) -> None:
        super().__init__()
        self.config: RegardsConfig = config or RegardsConfig.from_env()
        self._repo = RegardsApi(self.config)
        self._uc_search = SearchProducts(self._repo)
        self._uc_fetch = FetchProducts(self._repo)
        self._uc_register = RegisterValues(self._repo)

    @classmethod
    def _attrs_module(cls) -> tuple[str, str]:
        # This tells SunPy where to find attrs at a.<provider>.<AttrName>
        return "regards", "sunpy_regards.adapters.sunpy.attrs"

    @classmethod
    def register_values(cls) -> Dict[type, List[Tuple[str, str]]]:
        # Build a repo instance from env (SunPy expects classmethod)
        try:
            cfg = RegardsConfig.from_env()
            repo = RegardsApi(cfg)
            meta = RegisterValues(repo).execute()
            datasets = meta.get("datasets") or []
            instruments = meta.get("instruments") or []
            observatories = meta.get("observatories") or []
        except Exception as exc:
            log.warning("[REGARDS META] No dynamic metadata; using fallback. (%s)", exc)
            datasets, instruments, observatories = [], [], []

        if not datasets and not instruments and not observatories:
            log.warning("[REGARDS META] No dynamic metadata, using static fallback.")
            datasets = [("GAIA-DEM data", "SDO AIA GAIA-DEM dataset in REGARDS.")]
            instruments = [("AIA", "SDO AIA instrument.")]
            observatories = [("SDO", "Solar Dynamics Observatory.")]

        return {
            Dataset: datasets,
            a.Instrument: instruments,
            Observatory: observatories,
            a.Provider: [("REGARDS", "REGARDS archive at MEDOC.")],
        }

    @classmethod
    def _can_handle_query(cls, *query: Any) -> bool:
        required = {a.Time}
        optional = {a.Time, a.Instrument, Dataset, Observatory, a.Provider}

        if not cls.check_attr_types_in_query(query, required, optional):
            return False

        for x in query:
            if isinstance(x, a.Provider) and str(x.value).lower() != "regards":
                return False
        return True

    @staticmethod
    def _apply_display_policy(full_qr: QueryResponseTable) -> QueryResponseTable:
        """
        Return a *view* table for display (columns reduced),
        while keeping the full table attached for fetch/debug.
        """
        display = [c for c in DISPLAY_COLUMNS if c in full_qr.colnames]

        # Build a display-only view table
        view = full_qr[display] if display else full_qr
        view_qr = QueryResponseTable(view, client=full_qr.client)

        # Keep full table (for fetch/debug)
        setattr(view_qr, "_regards_full_table", full_qr)

        return view_qr

    def search(self, *query: Any, **kwargs: Any) -> QueryResponseTable:
        query_tree = and_(*query)
        query_branches = walker.create(query_tree)

        page = int(kwargs.get("page", 0))
        size = int(kwargs.get("size", 500))

        tables: List[astropy.table.QTable] = []

        for clauses in query_branches:
            filtered = [c for c in clauses if not c.lower().startswith("provider=")]
            q = " AND ".join(filtered) if filtered else ""
            products = self._uc_search.execute(q=q, page=page, size=size)
            table = self._products_to_table(products)
            if len(table) > 0:
                tables.append(table)

        if not tables:
            empty_full = QueryResponseTable(astropy.table.QTable(), client=self)
            return self._apply_display_policy(empty_full)

        full = astropy.table.vstack(tables)
        full_qr = QueryResponseTable(full, client=self)

        return self._apply_display_policy(full_qr)

    @staticmethod
    def _products_to_table(products: list[Any]) -> astropy.table.QTable:
        if not products:
            return astropy.table.QTable()

        obs_list: List[str | None] = []
        inst_list: List[str | None] = []
        dset_list: List[str | None] = []
        start_list: List[str | None] = []
        end_list: List[str | None] = []
        urn_list: List[str | None] = []
        download_list: List[str | None] = []
        filename_list: List[str | None] = []

        dyn_cols: Dict[str, List[Any]] = {
            "Telescope": [],
            "Detector": [],
            "Date-end": [],
            "Wavelength [Å] (minimum)": [],
            "Wavelength type": [],
            "Scientific objective": [],
            "Jop": [],
            "Observation mode": [],
            "Observation type": [],
            "X-center [arcsec]": [],
            "Y-center [arcsec]": [],
            "Data type": [],
            "File size": [],
            "Exposure time": [],
            "Descriptor": [],
            "Level": [],
            "total_binning_factor": [],
            "Sun distance": [],
            "hg_latitude_obsv": [],
            "hg_longitud_obsv": [],
            "Slit width [arcsec]": [],
        }

        for p in products:
            # ProductDTO
            extra = getattr(p, "extra", {}) or {}

            obs_list.append(getattr(p, "observatory", None))
            inst_list.append(getattr(p, "instrument", None))
            dset_list.append(getattr(p, "dataset", None))
            start_list.append(getattr(p, "start_time", None))
            end_list.append(getattr(p, "end_time", None))
            urn_list.append(getattr(p, "urn", None))
            download_list.append(getattr(p, "download_url", None))
            filename_list.append(getattr(p, "filename", None))

            dyn_cols["Telescope"].append(extra.get("telescope"))
            dyn_cols["Detector"].append(extra.get("detector"))
            dyn_cols["Date-end"].append(extra.get("date_end"))

            wmin = (
                extra.get("wavemin")
                or extra.get("wavelength_min")
                or extra.get("wave_min")
                or extra.get("waveminimum")
                or extra.get("wavemin_fallback")
            )
            dyn_cols["Wavelength [Å] (minimum)"].append(wmin)

            dyn_cols["Wavelength type"].append(extra.get("wavetype"))
            dyn_cols["Scientific objective"].append(extra.get("sci_obj"))
            dyn_cols["Jop"].append(extra.get("jop"))
            dyn_cols["Observation mode"].append(extra.get("obs_mode"))
            dyn_cols["Observation type"].append(extra.get("obs_type"))
            dyn_cols["X-center [arcsec]"].append(extra.get("xcen"))
            dyn_cols["Y-center [arcsec]"].append(extra.get("ycen"))
            dyn_cols["Data type"].append(extra.get("datatype"))
            dyn_cols["File size"].append(extra.get("filesize"))
            dyn_cols["Exposure time"].append(extra.get("exposure"))
            dyn_cols["Descriptor"].append(extra.get("descriptor"))
            dyn_cols["Level"].append(extra.get("level"))
            dyn_cols["total_binning_factor"].append(extra.get("total_binning_factor"))
            dyn_cols["Sun distance"].append(extra.get("dsun_obs"))
            dyn_cols["hg_latitude_obsv"].append(extra.get("hg_latitude_obsv"))
            dyn_cols["hg_longitud_obsv"].append(extra.get("hg_longitud_obsv"))
            dyn_cols["Slit width [arcsec]"].append(extra.get("slitwidth"))

        table_data: Dict[str, List[Any]] = {
            "Observatory": obs_list,
            "Instrument": inst_list,
            "Dataset": dset_list,
            "Start time": start_list,
            "End time": end_list,
            "Product URN": urn_list,
            "Download URL": download_list,
            "Filename": filename_list,
        }

        for col_name, values in dyn_cols.items():
            if any(v is not None for v in values):
                table_data[col_name] = values

        n = len(obs_list)
        table_data.setdefault("Wavelength [Å] (minimum)", [None] * n)
        table_data.setdefault("X-center [arcsec]", [None] * n)
        table_data.setdefault("Y-center [arcsec]", [None] * n)

        return astropy.table.QTable(table_data)

    def fetch(
        self,
        query_results: Iterable[Mapping[str, Any]],
        *,
        path: str,
        downloader: Any,
        **_: Any,
    ) -> None:
        full = getattr(query_results, "_regards_full_table", None)
        if full is not None:
            query_results = full

        base_url = self.config.base_url.rstrip("/")
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        for row in query_results:
            url = row.get("Download URL")
            if not url:
                log.debug("[REGARDS FETCH] No Download URL for this row, skipping.")
                continue

            filename = row.get("Filename")
            if not filename:
                urn = row.get("Product URN") or "regards_product"
                filename = f"{str(urn).replace(':', '_')}.fits"

            filepath = str(path).format(file=filename, **getattr(row, "response_block_map", {}))
            filepath_path = Path(filepath)
            filepath_path.parent.mkdir(parents=True, exist_ok=True)

            url_str = str(url)
            parsed = urlparse(url_str)

            # REGARDS direct download (authorized)
            if url_str.startswith(base_url):
                log.debug("[REGARDS FETCH] direct GET %s -> %s", url_str, filepath)
                try:
                    content = self._uc_fetch.download(url=url_str)
                except Exception as exc:
                    log.error(
                        "[REGARDS FETCH] Failed to download %s -> %s (%s)", url_str, filepath, exc
                    )
                    continue

                with filepath_path.open("wb") as f:
                    f.write(content)
                continue

            # SOAR direct download (no auth)
            if parsed.hostname and parsed.hostname.endswith("soar.esac.esa.int"):
                log.debug("[REGARDS FETCH] SOAR direct GET %s -> %s", url_str, filepath)
                try:
                    resp: Response = requests.get(url_str, timeout=120, verify=False, stream=True)
                    resp.raise_for_status()
                except Exception as exc:
                    log.error(
                        "[REGARDS FETCH] Failed SOAR download %s -> %s (%s)", url_str, filepath, exc
                    )
                    continue

                with filepath_path.open("wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

                log.debug("[REGARDS FETCH] SOAR download OK -> %s", filepath)
                continue

            # Anything else: parfive downloader
            log.debug("[REGARDS FETCH] enqueue external %s -> %s", url_str, filepath)
            downloader.enqueue_file(url_str, filename=filepath)
