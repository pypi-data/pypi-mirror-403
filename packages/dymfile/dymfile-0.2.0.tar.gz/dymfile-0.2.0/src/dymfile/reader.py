"""Read DYM binary files."""

from __future__ import annotations

import datetime
import struct
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import xarray as xr

from dymfile._formats import DymData, DymHeader
from dymfile._utils import (
    LabelsCoordinates,
    gen_monthly_dates,
    generate_coordinates_attrs,
    generate_name,
    get_date_sea,
    iter_unpack_numbers,
    year_month_sea,
)

if TYPE_CHECKING:
    import io

__all__ = ["read_dym", "dym_to_dataset"]

DYM_INVALID_VALUE = -999
NB_DAY_MONTHLY = 30


def _read_header(file: io.BufferedReader | io.BytesIO) -> DymHeader:
    """
    Read header from DYM file.

    Parameters
    ----------
    file : io.BufferedReader | io.BytesIO
        File object positioned at start.

    Returns
    -------
    DymHeader
        Parsed header information.
    """
    # Skip first 12 bytes (3 floats/ints - unknown purpose)
    file.read(4)
    struct.unpack("i", file.read(4))
    struct.unpack("f", file.read(4))
    struct.unpack("f", file.read(4))

    # Read dimensions and time bounds
    nlon = struct.unpack("i", file.read(4))[0]
    nlat = struct.unpack("i", file.read(4))[0]
    nlevel = struct.unpack("i", file.read(4))[0]
    t0 = struct.unpack("f", file.read(4))[0]
    tfin = struct.unpack("f", file.read(4))[0]

    return DymHeader(nlon=nlon, nlat=nlat, nlevel=nlevel, t0=t0, tfin=tfin)


def _read_coordinates_and_mask(
    file: io.BufferedReader | io.BytesIO, header: DymHeader
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Read coordinate arrays and mask from DYM file.

    Parameters
    ----------
    file : io.BufferedReader | io.BytesIO
        File object positioned after header.
    header : DymHeader
        Header information.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]
        longitude (nlon,), latitude (nlat,), time (nlevel,), mask (nlat, nlon)
    """
    # Read longitude grid (nlat, nlon)
    xlon = np.zeros((header.nlat, header.nlon), dtype=np.float32)
    for i in range(header.nlat):
        xlon[i, :] = iter_unpack_numbers("f", file.read(4 * header.nlon))

    # Read latitude grid (nlat, nlon)
    ylat = np.zeros((header.nlat, header.nlon), dtype=np.float32)
    for i in range(header.nlat):
        ylat[i, :] = iter_unpack_numbers("f", file.read(4 * header.nlon))

    # Read time vector
    time_vect = iter_unpack_numbers("f", file.read(4 * header.nlevel))

    # Read mask (nlat, nlon)
    mask = np.zeros((header.nlat, header.nlon), dtype=np.int32)
    for i in range(header.nlat):
        mask[i, :] = iter_unpack_numbers("i", file.read(4 * header.nlon))

    # Extract 1D coordinates (assume regular grid)
    longitude = xlon[0, :]
    latitude = ylat[:, 0]

    return longitude, latitude, time_vect, mask


def _read_data(file: io.BufferedReader | io.BytesIO, header: DymHeader) -> np.ndarray:
    """
    Read data array from DYM file.

    Parameters
    ----------
    file : io.BufferedReader | io.BytesIO
        File object positioned after coordinates/mask.
    header : DymHeader
        Header information.

    Returns
    -------
    np.ndarray
        Data array with shape (nlevel, nlat, nlon).
        Invalid values (-999) are replaced with NaN.
    """
    data = np.zeros(
        (header.nlevel, header.nlat, header.nlon),
        dtype=np.float32,
    )

    for time_idx in range(header.nlevel):
        for lat_idx in range(header.nlat):
            row = struct.iter_unpack("f", file.read(4 * header.nlon))
            data[time_idx, lat_idx, :] = np.array([x[0] for x in row])

    # Replace invalid values with NaN
    data[data == DYM_INVALID_VALUE] = np.nan

    return data


def _format_time(
    time_vect: np.ndarray,
    header: DymHeader,
    *,
    delta_time: int = NB_DAY_MONTHLY,
    decode_times: bool = True,
) -> np.ndarray:
    """
    Format time vector to datetime64 if requested.

    Parameters
    ----------
    time_vect : np.ndarray
        Raw time vector from file.
    header : DymHeader
        Header information.
    delta_time : int
        Time delta in days (default 30 for monthly).
    decode_times : bool
        If True, convert to datetime64. If False, keep as float.

    Returns
    -------
    np.ndarray
        Formatted time array (datetime64 or float).
    """
    if not decode_times:
        return time_vect

    if delta_time == NB_DAY_MONTHLY:
        # Monthly data
        dates = gen_monthly_dates(
            year_month_sea(header.t0),
            year_month_sea(header.tfin),
        )
    else:
        # Custom time delta
        start_date = get_date_sea(header.t0)
        dates = [
            start_date + datetime.timedelta(days=int(i * delta_time))
            for i in range(header.nlevel)
        ]

    return np.array(dates, dtype="datetime64[ns]")


def read_dym(
    filepath: str | Path,
    *,
    delta_time: int = NB_DAY_MONTHLY,
    decode_times: bool = True,
) -> DymData:
    """
    Read a DYM file and return structured data.

    Parameters
    ----------
    filepath : str | Path
        Path to DYM file.
    delta_time : int
        Time delta in days (default 30 for monthly).
    decode_times : bool
        If True, convert times to datetime64. If False, keep as float.

    Returns
    -------
    DymData
        Structured data with header, arrays, coordinates.

    Examples
    --------
    >>> dym_data = read_dym("file.dym")
    >>> print(dym_data.header)
    >>> print(dym_data.data.shape)
    """
    filepath = Path(filepath)
    with filepath.open("rb") as file:
        header = _read_header(file)
        longitude, latitude, time_vect, mask = _read_coordinates_and_mask(file, header)
        data = _read_data(file, header)
        time = _format_time(
            time_vect, header, delta_time=delta_time, decode_times=decode_times
        )

    return DymData(
        header=header,
        data=data,
        mask=mask,
        longitude=longitude,
        latitude=latitude,
        time=time,
    )


def dym_to_dataset(
    filepath: str | Path,
    *,
    delta_time: int = NB_DAY_MONTHLY,
    decode_times: bool = True,
    normalize_longitude: bool = False,
    name: str | None = None,
    units: str | None = None,
) -> xr.Dataset:
    """
    Read a DYM file and convert to xarray Dataset.

    Parameters
    ----------
    filepath : str | Path
        Path to DYM file.
    delta_time : int
        Time delta in days (default 30 for monthly).
    decode_times : bool
        If True, convert times to datetime64.
    normalize_longitude : bool
        If True, normalize longitude to [-180, 180] and sort.
    name : str | None
        Variable name (default: filename stem).
    units : str | None
        Units for the data variable.

    Returns
    -------
    xr.Dataset
        Dataset with data and mask variables.

    Examples
    --------
    >>> ds = dym_to_dataset("file.dym", name="temperature", units="degC")
    >>> print(ds)
    """
    filepath = Path(filepath)
    if name is None:
        name = filepath.stem

    dym_data = read_dym(filepath, delta_time=delta_time, decode_times=decode_times)

    # Create mask DataArray
    mask_da = xr.DataArray(
        dym_data.mask,
        dims=(LabelsCoordinates.latitude, LabelsCoordinates.longitude),
        coords={
            LabelsCoordinates.latitude: dym_data.latitude,
            LabelsCoordinates.longitude: dym_data.longitude,
        },
        name="mask",
    )
    mask_da = generate_coordinates_attrs(mask_da)
    mask_da = generate_name(
        mask_da,
        name="mask",
        units="0=land, 1=1st layer, 2=2nd layer, 3=3rd layer",
    )

    # Create data DataArray
    data_da = xr.DataArray(
        dym_data.data,
        dims=("time", LabelsCoordinates.latitude, LabelsCoordinates.longitude),
        coords={
            "time": dym_data.time,
            LabelsCoordinates.latitude: dym_data.latitude,
            LabelsCoordinates.longitude: dym_data.longitude,
        },
    )

    # Apply mask (set land points to NaN)
    data_da = xr.where(mask_da == 0, np.nan, data_da)

    # Sort and add attributes
    data_da = data_da.sortby(
        ["time", LabelsCoordinates.latitude, LabelsCoordinates.longitude]
    )
    mask_da = mask_da.sortby([LabelsCoordinates.latitude, LabelsCoordinates.longitude])

    data_da = generate_coordinates_attrs(data_da)
    data_da = generate_name(data_da, name, units)

    if normalize_longitude:
        from dymfile._utils import normalize_longitude as _normalize_lon

        data_da = _normalize_lon(data_da)
        mask_da = _normalize_lon(mask_da)

    # Create Dataset
    return xr.Dataset({name: data_da, "mask": mask_da})
