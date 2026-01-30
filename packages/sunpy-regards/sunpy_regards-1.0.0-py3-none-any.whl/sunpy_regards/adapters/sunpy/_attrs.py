"""
sunpy_regards.adapters.sunpy._attrs

SunPy attributes -> REGARDS query clauses.

This module defines:
  - Dataset(...)      → properties.dataset_name:"..."
  - Observatory(...)  → properties.observatory:"..."
  - a.Instrument(...) → properties.instrument:"..."
  - a.Time(...)       → properties.date_obs:[START TO END]

The walker returns a list of lists of strings, each string being a
"field:condition" clause. Lists are joined with " AND " to build the
`q=` parameter of the rs-access-project API.
"""

from __future__ import annotations

import sunpy.net.attrs as a
from sunpy.net.attr import AttrAnd, AttrOr, AttrWalker, DataAttr, SimpleAttr

__all__ = ["Dataset", "Observatory", "walker"]


class Dataset(SimpleAttr):
    """
    REGARDS dataset (e.g. "GAIA-DEM data", "SOHO data", ...).

    The value must correspond to `properties.dataset_name` (or `dataset`)
    in the REGARDS index.
    """


class Observatory(SimpleAttr):
    """
    REGARDS observatory (e.g. "SDO", "SOHO", "STEREO", ...).

    The value must correspond to `properties.observatory`.
    """


walker = AttrWalker()


# Creators
@walker.add_creator(AttrOr)
def _create_or(wlk: AttrWalker, tree: AttrOr) -> list[list[str]]:
    """
    Creator for OR.

    Returns a list of "branches" of the query.
    Each branch is a list of "field:condition" strings.
    """
    return [wlk.create(sub) for sub in tree.attrs]


@walker.add_creator(AttrAnd, DataAttr)
def _create_and(wlk: AttrWalker, tree: DataAttr) -> list[list[str]]:
    """
    Creator for AND (and simple DataAttr).

    Delegates work to appliers.
    """
    result: list[str] = []
    wlk.apply(tree, result)
    return [result]


@walker.add_applier(AttrAnd)
def _apply_and(wlk: AttrWalker, and_attr: AttrAnd, params: list[str]) -> None:
    """
    Applier for AND: apply each attribute to the same params list.
    """
    for iattr in and_attr.attrs:
        wlk.apply(iattr, params)


# Individual appliers
@walker.add_applier(a.Time)
def _apply_time(_wlk: AttrWalker, attr: a.Time, params: list[str]) -> None:
    """
    Time constraint on properties.date_obs.
    """
    start = attr.start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end = attr.end.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    params.append(f"properties.date_obs:[{start} TO {end}]")


@walker.add_applier(a.Instrument)
def _apply_instrument(_wlk: AttrWalker, attr: a.Instrument, params: list[str]) -> None:
    """
    Filter on instrument (not limited to AIA).
    """
    params.append(f'properties.instrument:"{attr.value}"')


@walker.add_applier(Dataset)
def _apply_dataset(_wlk: AttrWalker, attr: Dataset, params: list[str]) -> None:
    """
    Filter on dataset_name.
    """
    params.append(f'properties.dataset_name:"{attr.value}"')


@walker.add_applier(Observatory)
def _apply_observatory(_wlk: AttrWalker, attr: Observatory, params: list[str]) -> None:
    """
    Filter on observatory.
    """
    params.append(f'properties.observatory:"{attr.value}"')


@walker.add_applier(a.Provider)
def _apply_provider(_wlk: AttrWalker, _attr: a.Provider, _params: list[str]) -> None:
    """
    Provider("REGARDS") is handled in _can_handle_query; we do not put it
    into the q= string. The applier is intentionally a no-op.
    """
    return
