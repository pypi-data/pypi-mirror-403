"""Write DYM binary files."""

from __future__ import annotations

import struct
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from dymfile._formats import DymData, DymHeader
from dymfile._utils import LabelsCoordinates

if TYPE_CHECKING:
    import io

    import xarray as xr

__all__ = ["write_dym", "dataset_to_dym"]

DYM_INVALID_VALUE = -999


def _write_header(file: io.BufferedWriter, header: DymHeader) -> None:
    """
    Write DYM file header.

    Parameters
    ----------
    file : io.BufferedWriter
        File object to write to.
    header : DymHeader
        Header information to write.
    """
    # Write unknown header bytes (matching reader format)
    file.write(struct.pack("i", 0))  # Unknown int
    file.write(struct.pack("i", 0))  # Unknown int
    file.write(struct.pack("f", 0.0))  # Unknown float
    file.write(struct.pack("f", 0.0))  # Unknown float

    # Write dimensions and time bounds
    file.write(struct.pack("i", header.nlon))
    file.write(struct.pack("i", header.nlat))
    file.write(struct.pack("i", header.nlevel))
    file.write(struct.pack("f", header.t0))
    file.write(struct.pack("f", header.tfin))


def _write_coordinates_and_mask(
    file: io.BufferedWriter,
    longitude: np.ndarray,
    latitude: np.ndarray,
    time: np.ndarray,
    mask: np.ndarray,
) -> None:
    """
    Write coordinate arrays and mask to DYM file.

    Parameters
    ----------
    file : io.BufferedWriter
        File object to write to.
    longitude : np.ndarray
        Longitude array (nlon,).
    latitude : np.ndarray
        Latitude array (nlat,).
    time : np.ndarray
        Time array (nlevel,) - should be float in SEAPODYM format.
    mask : np.ndarray
        Mask array (nlat, nlon).
    """
    nlat, nlon = mask.shape

    # Create 2D grids from 1D coordinates
    xlon = np.tile(longitude, (nlat, 1)).astype(np.float32)
    ylat = np.tile(latitude[:, np.newaxis], (1, nlon)).astype(np.float32)

    # Write longitude grid
    for i in range(nlat):
        for val in xlon[i, :]:
            file.write(struct.pack("f", val))

    # Write latitude grid
    for i in range(nlat):
        for val in ylat[i, :]:
            file.write(struct.pack("f", val))

    # Write time vector
    for val in time.astype(np.float32):
        file.write(struct.pack("f", float(val)))

    # Write mask
    for i in range(nlat):
        for val in mask[i, :]:
            file.write(struct.pack("i", int(val)))


def _write_data(
    file: io.BufferedWriter, data: np.ndarray, mask: np.ndarray
) -> None:
    """
    Write data array to DYM file.

    Parameters
    ----------
    file : io.BufferedWriter
        File object to write to.
    data : np.ndarray
        Data array with shape (nlevel, nlat, nlon).
    mask : np.ndarray
        Mask array with shape (nlat, nlon).
        Used to set land points to invalid value.
    """
    nlevel, nlat, nlon = data.shape

    # Replace NaN with invalid value
    data_out = data.copy()
    data_out[np.isnan(data_out)] = DYM_INVALID_VALUE

    # Apply mask (set land points to invalid value)
    for time_idx in range(nlevel):
        data_out[time_idx, mask == 0] = DYM_INVALID_VALUE

    # Write data
    for time_idx in range(nlevel):
        for lat_idx in range(nlat):
            for val in data_out[time_idx, lat_idx, :]:
                file.write(struct.pack("f", float(val)))


def write_dym(
    filepath: str | Path,
    data: np.ndarray,
    longitude: np.ndarray,
    latitude: np.ndarray,
    time: np.ndarray,
    mask: np.ndarray | None = None,
    *,
    t0: float | None = None,
    tfin: float | None = None,
) -> None:
    """
    Write a DYM file from numpy arrays.

    Parameters
    ----------
    filepath : str | Path
        Path to output DYM file.
    data : np.ndarray
        Data array with shape (nlevel, nlat, nlon).
    longitude : np.ndarray
        Longitude array (nlon,).
    latitude : np.ndarray
        Latitude array (nlat,).
    time : np.ndarray
        Time array (nlevel,) in SEAPODYM float format.
    mask : np.ndarray | None
        Mask array (nlat, nlon). If None, creates mask with all 1s.
    t0 : float | None
        Initial time in SEAPODYM format. If None, uses time[0].
    tfin : float | None
        Final time in SEAPODYM format. If None, uses time[-1].

    Examples
    --------
    >>> import numpy as np
    >>> data = np.random.rand(12, 10, 20)  # 12 months, 10 lats, 20 lons
    >>> lon = np.linspace(-180, 180, 20)
    >>> lat = np.linspace(-90, 90, 10)
    >>> time = np.arange(2020.0, 2021.0, 1/12)  # SEAPODYM format
    >>> write_dym("output.dym", data, lon, lat, time)
    """
    filepath = Path(filepath)
    nlevel, nlat, nlon = data.shape

    # Validate shapes
    if len(longitude) != nlon:
        raise ValueError(f"longitude length {len(longitude)} doesn't match data nlon={nlon}")
    if len(latitude) != nlat:
        raise ValueError(f"latitude length {len(latitude)} doesn't match data nlat={nlat}")
    if len(time) != nlevel:
        raise ValueError(f"time length {len(time)} doesn't match data nlevel={nlevel}")

    # Create default mask if not provided
    if mask is None:
        mask = np.ones((nlat, nlon), dtype=np.int32)
    elif mask.shape != (nlat, nlon):
        raise ValueError(f"mask shape {mask.shape} doesn't match data (nlat={nlat}, nlon={nlon})")

    # Create header
    if t0 is None:
        t0 = float(time[0])
    if tfin is None:
        tfin = float(time[-1])

    header = DymHeader(
        nlon=nlon,
        nlat=nlat,
        nlevel=nlevel,
        t0=t0,
        tfin=tfin,
    )

    # Write file
    with filepath.open("wb") as file:
        _write_header(file, header)
        _write_coordinates_and_mask(file, longitude, latitude, time, mask)
        _write_data(file, data, mask)


def dataset_to_dym(
    ds: xr.Dataset,
    filepath: str | Path,
    *,
    variable: str | None = None,
) -> None:
    """
    Write an xarray Dataset to DYM format.

    Parameters
    ----------
    ds : xr.Dataset
        Dataset to write. Must contain time, latitude, longitude coordinates.
    filepath : str | Path
        Path to output DYM file.
    variable : str | None
        Name of data variable to write. If None, uses first data variable.

    Raises
    ------
    ValueError
        If required coordinates are missing or data has wrong dimensions.

    Examples
    --------
    >>> import xarray as xr
    >>> ds = xr.open_dataset("input.nc")
    >>> dataset_to_dym(ds, "output.dym", variable="temperature")
    """
    # Select variable
    if variable is None:
        data_vars = list(ds.data_vars)
        if not data_vars:
            raise ValueError("Dataset has no data variables")
        if "mask" in data_vars:
            data_vars.remove("mask")
        if not data_vars:
            raise ValueError("Dataset only contains mask variable")
        variable = data_vars[0]

    if variable not in ds:
        raise ValueError(f"Variable {variable!r} not found in dataset")

    data_var = ds[variable]

    # Check coordinates
    required_coords = {"time", LabelsCoordinates.latitude, LabelsCoordinates.longitude}
    missing_coords = required_coords - set(data_var.dims)
    if missing_coords:
        raise ValueError(f"Missing required coordinates: {missing_coords}")

    # Extract arrays
    data = data_var.values  # shape: (nlevel, nlat, nlon)
    longitude = ds[LabelsCoordinates.longitude].values
    latitude = ds[LabelsCoordinates.latitude].values
    time_coord = ds["time"]

    # Convert time to SEAPODYM format (simplified: use year as float)
    # TODO: Implement proper conversion from datetime64 to SEAPODYM format
    if np.issubdtype(time_coord.dtype, np.datetime64):
        # Simple conversion: extract year + day_of_year/365
        times_dt = time_coord.values.astype("datetime64[D]")
        years = times_dt.astype("datetime64[Y]").astype(int) + 1970
        day_of_year = (times_dt - times_dt.astype("datetime64[Y]")).astype(int) + 1
        time = years + day_of_year / 365.0
    else:
        time = time_coord.values.astype(np.float32)

    # Extract or create mask
    if "mask" in ds:
        mask = ds["mask"].values.astype(np.int32)
    else:
        # Create mask from non-NaN values
        mask = (~np.isnan(data[0, :, :])).astype(np.int32)

    # Write DYM file
    write_dym(
        filepath=filepath,
        data=data,
        longitude=longitude,
        latitude=latitude,
        time=time,
        mask=mask,
    )
