"""Tests for DYM file reading."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import xarray as xr

from dymfile.reader import dym_to_dataset, read_dym


def test_read_dym_basic(sample_dym_file: Path) -> None:
    """Test basic DYM file reading."""
    dym_data = read_dym(sample_dym_file)

    assert dym_data.header.nlon > 0
    assert dym_data.header.nlat > 0
    assert dym_data.header.nlevel > 0
    assert dym_data.data.shape == (
        dym_data.header.nlevel,
        dym_data.header.nlat,
        dym_data.header.nlon,
    )
    assert dym_data.mask.shape == (dym_data.header.nlat, dym_data.header.nlon)
    assert len(dym_data.longitude) == dym_data.header.nlon
    assert len(dym_data.latitude) == dym_data.header.nlat
    assert len(dym_data.time) == dym_data.header.nlevel


def test_dym_to_dataset(sample_dym_file: Path) -> None:
    """Test conversion of DYM to xarray Dataset."""
    ds = dym_to_dataset(sample_dym_file)

    assert isinstance(ds, xr.Dataset)
    assert "mask" in ds
    assert len(ds.data_vars) >= 1

    # Check dimensions
    assert "time" in ds.dims
    assert "latitude" in ds.dims
    assert "longitude" in ds.dims


def test_dym_to_dataset_decode_times(sample_dym_file: Path) -> None:
    """Test time decoding."""
    ds = dym_to_dataset(sample_dym_file, decode_times=True)
    assert np.issubdtype(ds["time"].dtype, np.datetime64)

    ds_no_decode = dym_to_dataset(sample_dym_file, decode_times=False)
    assert np.issubdtype(ds_no_decode["time"].dtype, np.floating)


def test_dym_to_dataset_normalize_longitude(sample_dym_file: Path) -> None:
    """Test longitude normalization."""
    ds = dym_to_dataset(sample_dym_file, normalize_longitude=True)
    lon = ds["longitude"].values
    assert lon.min() >= -180
    assert lon.max() <= 180


def test_read_nonexistent_file() -> None:
    """Test error handling for nonexistent files."""
    with pytest.raises(FileNotFoundError):
        read_dym("nonexistent.dym")
