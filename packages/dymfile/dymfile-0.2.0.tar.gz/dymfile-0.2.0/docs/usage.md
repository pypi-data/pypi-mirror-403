# Usage Guide

## Reading DYM files

### Using xarray backend (recommended)

```python
import xarray as xr

# Open with xarray
ds = xr.open_dataset("data.dym", engine="dym")

# With options
ds = xr.open_dataset(
    "data.dym",
    engine="dym",
    decode_times=True,  # Convert to datetime64
    normalize_longitude=True,  # Normalize to [-180, 180]
)
```

### Using high-level API

```python
from dymfile import dym_to_dataset

ds = dym_to_dataset(
    "data.dym",
    decode_times=True,
    normalize_longitude=False,
    delta_time=30,  # Time step in days
)
```

### Using low-level API

```python
from dymfile.reader import read_dym

dym_data = read_dym("data.dym")

# Access components
print(dym_data.header)
print(dym_data.data.shape)  # (nlevel, nlat, nlon)
print(dym_data.mask.shape)  # (nlat, nlon)
```

## Writing DYM files

### From xarray Dataset

```python
from dymfile.writer import dataset_to_dym
import xarray as xr

ds = xr.open_dataset("input.nc")
dataset_to_dym(ds, "output.dym", variable="temperature")
```

### From numpy arrays

```python
from dymfile.writer import write_dym
import numpy as np

data = np.random.rand(12, 10, 20)  # (time, lat, lon)
lon = np.linspace(-180, 180, 20)
lat = np.linspace(-90, 90, 10)
time = np.arange(2020.0, 2021.0, 1/12)  # SEAPODYM format

write_dym("output.dym", data, lon, lat, time)
```

## Command-line tools

### DYM to NetCDF/Zarr

```bash
# Basic conversion
dym-to-dataset input.dym -o output.nc

# With options
dym-to-dataset input.dym -o output.nc \
    --no-decode-times \
    --normalize-longitude \
    --compression gzip

# To Zarr format
dym-to-dataset input.dym -o output.zarr --format zarr
```

### NetCDF/Zarr to DYM

```bash
# Basic conversion
dataset-to-dym input.nc -o output.dym

# Select specific variable
dataset-to-dym input.nc -o output.dym --variable temperature

# From Zarr
dataset-to-dym input.zarr -o output.dym --engine zarr
```

## Working with the mask

The mask indicates ocean layers:
- 0 = land
- 1 = first layer
- 2 = second layer
- 3 = third layer

```python
ds = dym_to_dataset("data.dym")

# Access mask
mask = ds["mask"]

# Filter by layer
layer1 = ds.where(mask == 1)
ocean_only = ds.where(mask > 0)
```

## Time handling

DYM files use SEAPODYM date format (year + day_of_year/365):

```python
# Auto-decode to datetime64 (default)
ds = dym_to_dataset("data.dym", decode_times=True)
print(ds.time.dtype)  # datetime64[ns]

# Keep as float
ds = dym_to_dataset("data.dym", decode_times=False)
print(ds.time.dtype)  # float32
```
