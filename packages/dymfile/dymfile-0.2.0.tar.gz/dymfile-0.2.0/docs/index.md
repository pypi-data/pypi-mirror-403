# dymfile

**Read and write DYM file format with xarray integration**

DYM is a binary format used by the SEAPODYM project for oceanographic data storage. This package provides a modern Python interface for reading and writing DYM files, with native xarray integration.

## Features

- ✅ **Read DYM files** as xarray Datasets
- ✅ **Write xarray Datasets** to DYM format
- ✅ **Native xarray backend** - use `xr.open_dataset("file.dym", engine="dym")`
- ✅ **Command-line tools** for format conversion
- ✅ **Well-typed** with full type hints
- ✅ **Tested** with pytest

## Quick Start

```python
import xarray as xr

# Read DYM file via xarray backend
ds = xr.open_dataset("data.dym", engine="dym")
print(ds)

# Or use the high-level API
from dymfile import dym_to_dataset
ds = dym_to_dataset("data.dym")

# Work with your data using xarray
subset = ds.sel(time="2020", latitude=slice(-10, 10))
mean = ds.mean(dim="time")

# Save back to DYM format
from dymfile.writer import dataset_to_dym
dataset_to_dym(ds, "output.dym")
```

## Command-line tools

```bash
# Convert DYM to NetCDF
dym-to-dataset input.dym -o output.nc

# Convert NetCDF to DYM
dataset-to-dym input.nc -o output.dym --variable temperature
```

## Why dymfile?

- **Modern tooling**: Built with uv, ruff, and pyright
- **xarray-native**: Seamless integration with the xarray ecosystem
- **Simple API**: High-level functions for common tasks
- **Well-documented**: Comprehensive docs and examples

## Project Info

- **GitHub**: [Ash12H/dymfile](https://github.com/Ash12H/dymfile)
- **License**: MIT
- **Python**: 3.10+
