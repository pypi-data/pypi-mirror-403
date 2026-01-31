"""Command-line interface tools for DYM format conversion."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import xarray as xr

from dymfile.reader import dym_to_dataset
from dymfile.writer import dataset_to_dym


def dym_to_dataset_main() -> None:
    """
    CLI tool to convert DYM files to NetCDF/Zarr format.

    Usage:
        dym-to-dataset input.dym -o output.nc
        dym-to-dataset input.dym -o output.zarr --format zarr
    """
    parser = argparse.ArgumentParser(
        prog="dym-to-dataset",
        description="Convert DYM files to NetCDF or Zarr format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input",
        type=str,
        help="Input DYM file path",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output file path (.nc for NetCDF, .zarr for Zarr)",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["netcdf", "zarr"],
        default="netcdf",
        help="Output format",
    )

    parser.add_argument(
        "--no-decode-times",
        action="store_true",
        help="Don't decode times to datetime64",
    )

    parser.add_argument(
        "--normalize-longitude",
        action="store_true",
        help="Normalize longitude to [-180, 180] range",
    )

    parser.add_argument(
        "--delta-time",
        type=int,
        default=30,
        help="Time delta in days (default: 30 for monthly)",
    )

    parser.add_argument(
        "--compression",
        type=str,
        choices=["none", "gzip", "lzf"],
        default="gzip",
        help="Compression for NetCDF output",
    )

    args = parser.parse_args()

    # Check input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Read DYM file
    try:
        ds = dym_to_dataset(
            input_path,
            decode_times=not args.no_decode_times,
            normalize_longitude=args.normalize_longitude,
            delta_time=args.delta_time,
        )
    except Exception as e:
        print(f"Error reading DYM file: {e}", file=sys.stderr)
        sys.exit(1)

    # Write output
    output_path = Path(args.output)
    try:
        if args.format == "netcdf":
            encoding = {}
            if args.compression != "none":
                for var in ds.data_vars:
                    encoding[var] = {"zlib": True, "complevel": 4}
            ds.to_netcdf(output_path, encoding=encoding if args.compression != "none" else None)
            print(f"✓ Converted to NetCDF: {output_path}")
        elif args.format == "zarr":
            ds.to_zarr(output_path, mode="w")
            print(f"✓ Converted to Zarr: {output_path}")
    except Exception as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)


def dataset_to_dym_main() -> None:
    """
    CLI tool to convert NetCDF/Zarr files to DYM format.

    Usage:
        dataset-to-dym input.nc -o output.dym
        dataset-to-dym input.zarr -o output.dym --variable temperature
    """
    parser = argparse.ArgumentParser(
        prog="dataset-to-dym",
        description="Convert NetCDF or Zarr files to DYM format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "input",
        type=str,
        help="Input NetCDF or Zarr file path",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output DYM file path",
    )

    parser.add_argument(
        "--variable",
        type=str,
        default=None,
        help="Variable name to extract (default: first data variable)",
    )

    parser.add_argument(
        "--engine",
        type=str,
        choices=["netcdf4", "zarr", "h5netcdf"],
        default=None,
        help="Engine for reading input file (auto-detected if not specified)",
    )

    args = parser.parse_args()

    # Check input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Read input dataset
    try:
        if args.engine:
            ds = xr.open_dataset(input_path, engine=args.engine)
        else:
            ds = xr.open_dataset(input_path)
    except Exception as e:
        print(f"Error reading input file: {e}", file=sys.stderr)
        sys.exit(1)

    # Write DYM file
    output_path = Path(args.output)
    try:
        dataset_to_dym(ds, output_path, variable=args.variable)
        print(f"✓ Converted to DYM: {output_path}")
    except Exception as e:
        print(f"Error writing DYM file: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        ds.close()


if __name__ == "__main__":
    # This allows running the module directly for testing
    print("Use 'dym-to-dataset' or 'dataset-to-dym' commands")
    sys.exit(1)
