"""
sunpy-regards

A SunPy Fido plugin for accessing the REGARDS archive at MEDOC.
"""

from __future__ import annotations

from .adapters.sunpy.client import REGARDSClient

__all__ = ["REGARDSClient", "__version__"]

__version__ = "0.1.2"
