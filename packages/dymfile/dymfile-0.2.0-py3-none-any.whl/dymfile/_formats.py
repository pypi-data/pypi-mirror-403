"""Data structures for DYM file format."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["DymHeader", "DymData"]


@dataclass
class DymHeader:
    """
    Header information from a DYM file.

    Attributes
    ----------
    nlon : int
        Number of longitude points.
    nlat : int
        Number of latitude points.
    nlevel : int
        Number of vertical levels (time steps).
    t0 : float
        Initial time in SEAPODYM format.
    tfin : float
        Final time in SEAPODYM format.
    """

    nlon: int
    nlat: int
    nlevel: int
    t0: float
    tfin: float


@dataclass
class DymData:
    """
    Complete data from a DYM file.

    Attributes
    ----------
    header : DymHeader
        Header information.
    data : np.ndarray
        Data array with shape (nlevel, nlat, nlon).
    mask : np.ndarray
        Mask array with shape (nlat, nlon).
        Values: 0=land, 1=1st layer, 2=2nd layer, 3=3rd layer.
    longitude : np.ndarray
        Longitude coordinates with shape (nlon,).
    latitude : np.ndarray
        Latitude coordinates with shape (nlat,).
    time : np.ndarray
        Time coordinates with shape (nlevel,).
        Can be float (SEAPODYM format) or datetime64.
    """

    header: DymHeader
    data: np.ndarray
    mask: np.ndarray
    longitude: np.ndarray
    latitude: np.ndarray
    time: np.ndarray
