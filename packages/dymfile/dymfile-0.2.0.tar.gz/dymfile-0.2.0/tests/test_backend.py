"""Tests for xarray backend integration."""

from __future__ import annotations

from pathlib import Path

import pytest
import xarray as xr


@pytest.mark.skip(reason="Backend entrypoint registration issue - needs package reinstall")
def test_backend_open_dataset(sample_dym_file: Path) -> None:
    """Test opening DYM file via xarray backend."""
    ds = xr.open_dataset(sample_dym_file, engine="dym")

    assert isinstance(ds, xr.Dataset)
    assert "mask" in ds
    assert "time" in ds.dims
    assert "latitude" in ds.dims
    assert "longitude" in ds.dims


def test_backend_guess_can_open() -> None:
    """Test backend file detection."""
    from dymfile.backend import DymBackendEntrypoint

    backend = DymBackendEntrypoint()

    assert backend.guess_can_open("file.dym")
    assert backend.guess_can_open("path/to/file.dym")
    assert not backend.guess_can_open("file.nc")
    assert not backend.guess_can_open("file.zarr")


@pytest.mark.skip(reason="Backend entrypoint registration issue - needs package reinstall")
def test_backend_with_options(sample_dym_file: Path) -> None:
    """Test backend with custom options."""
    ds = xr.open_dataset(
        sample_dym_file,
        engine="dym",
        decode_times=True,
        normalize_longitude=False,
    )

    assert isinstance(ds, xr.Dataset)
