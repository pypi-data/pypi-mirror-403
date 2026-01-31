"""Xarray backend for DYM files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xarray.backends import BackendEntrypoint

from dymfile.reader import dym_to_dataset

if TYPE_CHECKING:
    import xarray as xr

__all__ = ["DymBackendEntrypoint"]


class DymBackendEntrypoint(BackendEntrypoint):
    """
    Xarray backend for reading DYM files.

    This backend allows opening DYM files directly with xarray:
        >>> import xarray as xr
        >>> ds = xr.open_dataset("file.dym", engine="dym")

    The backend is automatically registered when dymfile is installed.
    """

    def open_dataset(
        self,
        filename_or_obj,
        *,
        drop_variables=None,
        decode_times=True,
        normalize_longitude=False,
        delta_time=30,
    ) -> xr.Dataset:
        """
        Open a DYM file as an xarray Dataset.

        Parameters
        ----------
        filename_or_obj : str or Path
            Path to DYM file.
        drop_variables : list of str, optional
            Variables to drop from the dataset.
        decode_times : bool, default=True
            If True, decode time coordinates to datetime64.
        normalize_longitude : bool, default=False
            If True, normalize longitude to [-180, 180] range.
        delta_time : int, default=30
            Time step in days (default 30 for monthly data).

        Returns
        -------
        xr.Dataset
            Dataset with data and mask variables.
        """
        ds = dym_to_dataset(
            filename_or_obj,
            decode_times=decode_times,
            normalize_longitude=normalize_longitude,
            delta_time=delta_time,
        )

        if drop_variables:
            ds = ds.drop_vars(drop_variables, errors="ignore")

        return ds

    def guess_can_open(self, filename_or_obj) -> bool:
        """
        Guess if the backend can open the given file.

        Parameters
        ----------
        filename_or_obj : str or Path
            Path to file.

        Returns
        -------
        bool
            True if filename ends with .dym
        """
        return str(filename_or_obj).endswith(".dym")

    description = "Read DYM files from SEAPODYM project"
    url = "https://github.com/Ash12H/dymfile"
