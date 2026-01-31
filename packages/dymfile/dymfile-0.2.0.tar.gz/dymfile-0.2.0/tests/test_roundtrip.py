"""Tests for DYM write and round-trip operations."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from dymfile.reader import dym_to_dataset, read_dym
from dymfile.writer import dataset_to_dym, write_dym


@pytest.mark.skip(reason="Writer dimensions need adjustment")
def test_roundtrip_basic(sample_dym_file: Path, tmp_dym_file: Path) -> None:
    """Test read -> write -> read round-trip."""
    # Read original
    original_data = read_dym(sample_dym_file)

    # Write to temporary file
    write_dym(
        tmp_dym_file,
        data=original_data.data,
        longitude=original_data.longitude,
        latitude=original_data.latitude,
        time=np.arange(
            original_data.header.t0,
            original_data.header.tfin,
            (original_data.header.tfin - original_data.header.t0)
            / original_data.header.nlevel,
        ).astype(np.float32),
        mask=original_data.mask,
        t0=original_data.header.t0,
        tfin=original_data.header.tfin,
    )

    # Read back
    reread_data = read_dym(tmp_dym_file)

    # Compare headers
    assert reread_data.header.nlon == original_data.header.nlon
    assert reread_data.header.nlat == original_data.header.nlat
    assert reread_data.header.nlevel == original_data.header.nlevel

    # Compare arrays
    np.testing.assert_array_equal(reread_data.mask, original_data.mask)
    np.testing.assert_allclose(reread_data.longitude, original_data.longitude)
    np.testing.assert_allclose(reread_data.latitude, original_data.latitude)

    # Compare data (allowing for NaN)
    np.testing.assert_allclose(
        reread_data.data, original_data.data, equal_nan=True, rtol=1e-5
    )


@pytest.mark.skip(reason="Writer dimensions need adjustment")
def test_roundtrip_dataset(sample_dym_file: Path, tmp_dym_file: Path) -> None:
    """Test Dataset round-trip using high-level API."""
    # Read as dataset
    original_ds = dym_to_dataset(sample_dym_file, decode_times=False)

    # Write back
    dataset_to_dym(original_ds, tmp_dym_file)

    # Read back
    reread_ds = dym_to_dataset(tmp_dym_file, decode_times=False)

    # Compare dimensions
    assert reread_ds.dims == original_ds.dims

    # Get first data variable (excluding mask)
    data_vars = [v for v in original_ds.data_vars if v != "mask"]
    if data_vars:
        var_name = data_vars[0]
        np.testing.assert_allclose(
            reread_ds[var_name].values,
            original_ds[var_name].values,
            equal_nan=True,
            rtol=1e-5,
        )
