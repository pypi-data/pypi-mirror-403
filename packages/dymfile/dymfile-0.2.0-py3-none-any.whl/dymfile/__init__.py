"""
dymfile - Read and write DYM file format with xarray integration.

DYM is a binary format used by the SEAPODYM project for oceanographic data.
This package provides:
- Native xarray backend for seamless integration
- Low-level reader/writer functions
- CLI tools for format conversion
"""

from __future__ import annotations

__version__ = "0.1.0"

# Public API
from dymfile.reader import dym_to_dataset, read_dym

__all__ = [
    "__version__",
    "read_dym",
    "dym_to_dataset",
]


def __getattr__(name: str):
    """Lazy loading for optional modules."""
    if name == "DymBackendEntrypoint":
        try:
            from dymfile.backend import DymBackendEntrypoint

            return DymBackendEntrypoint
        except ImportError:
            raise AttributeError(
                "Backend not yet implemented. Install xarray to use backend features."
            ) from None
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
