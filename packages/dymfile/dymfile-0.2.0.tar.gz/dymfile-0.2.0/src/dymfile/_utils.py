"""Utility functions for DYM file processing."""

from __future__ import annotations

import datetime
import itertools
import struct
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import xarray as xr

__all__ = [
    "LabelsCoordinates",
    "get_date_sea",
    "year_month_sea",
    "gen_monthly_dates",
    "iter_unpack_numbers",
    "normalize_longitude",
    "generate_coordinates_attrs",
    "generate_name",
]


class LabelsCoordinates:
    """Standard coordinate names for DYM format."""

    latitude = "latitude"
    longitude = "longitude"
    time = "time"


def get_date_sea(ndat: float) -> datetime.date:
    """
    Convert SEAPODYM date format to datetime.date.

    SEAPODYM format: integer part is year, fractional part is day of year / 365.

    Parameters
    ----------
    ndat : float
        Date in SEAPODYM format.

    Returns
    -------
    datetime.date
        Converted date.

    Examples
    --------
    >>> get_date_sea(2020.5)
    datetime.date(2020, 7, 2)
    """
    year = int(ndat)
    days = int((ndat - year) * 365)
    return datetime.date(year, 1, 1) + datetime.timedelta(days=days - 1)


def year_month_sea(ndat: float) -> list[int]:
    """
    Extract year and month from SEAPODYM date format.

    Parameters
    ----------
    ndat : float
        Date in SEAPODYM format.

    Returns
    -------
    list[int]
        [year, month]

    Examples
    --------
    >>> year_month_sea(2020.5)
    [2020, 7]
    """
    year = int(ndat)
    days = int((ndat - year) * 365)
    date = datetime.date(year, 1, 1) + datetime.timedelta(days=days - 1)
    month = date.month
    return [year, month]


def gen_monthly_dates(t0: list[int], tfin: list[int]) -> np.ndarray:
    """
    Generate monthly dates between two [year, month] pairs.

    Dates are set to the 15th of each month.

    Parameters
    ----------
    t0 : list[int]
        Start [year, month].
    tfin : list[int]
        End [year, month].

    Returns
    -------
    np.ndarray
        Array of datetime64 dates.

    Examples
    --------
    >>> gen_monthly_dates([2020, 1], [2020, 3])
    array(['2020-01-15', '2020-02-15', '2020-03-15'], dtype='datetime64[D]')
    """
    dates = [
        datetime.date(year, month, 15)
        for year, month in itertools.product(
            range(t0[0], tfin[0] + 1), range(t0[1], tfin[1] + 1)
        )
    ]
    return np.array(dates, dtype="datetime64")


def iter_unpack_numbers(
    buf_format: str, buffer: bytes
) -> np.ndarray:
    """
    Unpack numbers from binary buffer.

    Parameters
    ----------
    buf_format : str
        struct format string ('f' for float, 'i' for int).
    buffer : bytes
        Binary buffer to unpack.

    Returns
    -------
    np.ndarray
        Unpacked numbers.
    """
    result = struct.iter_unpack(buf_format, buffer)
    return np.array([x[0] for x in result])


def normalize_longitude(data: xr.DataArray) -> xr.DataArray:
    """
    Normalize longitude to [-180, 180] range and sort.

    Parameters
    ----------
    data : xr.DataArray
        DataArray with longitude coordinate.

    Returns
    -------
    xr.DataArray
        DataArray with normalized longitude.
    """
    data = data.assign_coords(
        {
            LabelsCoordinates.longitude: (
                ((data[LabelsCoordinates.longitude] + 180) % 360) - 180
            )
        }
    )
    return data.sortby(list(data.coords.keys()))


def generate_coordinates_attrs(data: xr.DataArray) -> xr.DataArray:
    """
    Add CF-compliant attributes to longitude and latitude coordinates.

    Parameters
    ----------
    data : xr.DataArray
        DataArray to modify.

    Returns
    -------
    xr.DataArray
        DataArray with updated coordinate attributes.
    """
    data.coords[LabelsCoordinates.longitude] = data[
        LabelsCoordinates.longitude
    ].assign_attrs(
        standard_name="longitude",
        long_name="longitude",
        units="degrees_east",
    )
    data.coords[LabelsCoordinates.latitude] = data[
        LabelsCoordinates.latitude
    ].assign_attrs(
        standard_name="latitude",
        long_name="latitude",
        units="degrees_north",
    )
    return data


def generate_name(
    data: xr.DataArray, name: str, units: str | None = None
) -> xr.DataArray:
    """
    Set name and attributes for a DataArray.

    Parameters
    ----------
    data : xr.DataArray
        DataArray to modify.
    name : str
        Variable name.
    units : str | None
        Units string (optional).

    Returns
    -------
    xr.DataArray
        DataArray with updated name and attributes.
    """
    data.name = name
    attrs = {
        "standard_name": name,
        "long_name": name,
    }
    if units is not None:
        attrs["units"] = units
    data.attrs.update(attrs)
    return data
