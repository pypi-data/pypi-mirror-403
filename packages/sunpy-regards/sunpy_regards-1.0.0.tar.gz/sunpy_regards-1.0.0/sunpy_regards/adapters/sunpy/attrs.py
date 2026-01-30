"""
Public SunPy attributes for the REGARDS client.

This module re-exports the attributes from ``sunpy_regards.adapters.sunpy._attrs``
so that SunPy's attr discovery mechanism and the documentation
see them as being defined here.
"""

from __future__ import annotations

from ._attrs import Dataset, Observatory

__all__ = ["Dataset", "Observatory"]

# Trick the docs (and sunpy.net.attrs) into thinking these attrs
# are defined in this module.
for _a in (Dataset, Observatory):
    _a.__module__ = __name__
