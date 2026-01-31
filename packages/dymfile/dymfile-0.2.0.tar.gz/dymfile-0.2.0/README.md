# dymfile

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Read and write DYM file format with xarray integration**

DYM is a binary format used by the SEAPODYM project for oceanographic data. This package provides a modern Python interface with native xarray support.

## Features

- ✅ Read DYM files as xarray Datasets
- ✅ Write xarray Datasets to DYM format
- ✅ Native xarray backend: `xr.open_dataset("file.dym", engine="dym")`
- ✅ Command-line tools for format conversion
- ✅ Fully typed with pyright
- ✅ Tested with pytest

## Installation

```bash
git clone https://github.com/Ash12H/dymfile.git
cd dymfile
uv sync
```

Or with pip:

```bash
pip install git+https://github.com/Ash12H/dymfile.git
```

## Quick Start

### Reading

```python
import xarray as xr

# Via xarray backend (recommended)
ds = xr.open_dataset("data.dym", engine="dym")

# Or high-level API
from dymfile import dym_to_dataset
ds = dym_to_dataset("data.dym")
```

### Writing

```python
from dymfile.writer import dataset_to_dym

ds = xr.open_dataset("input.nc")
dataset_to_dym(ds, "output.dym")
```

### CLI Tools

```bash
# Convert DYM to NetCDF
dym-to-dataset input.dym -o output.nc

# Convert NetCDF to DYM
dataset-to-dym input.nc -o output.dym --variable temperature
```

## Documentation

Full documentation available at: [https://ash12h.github.io/dymfile](https://ash12h.github.io/dymfile)

- [Installation Guide](https://ash12h.github.io/dymfile/installation/)
- [Usage Examples](https://ash12h.github.io/dymfile/usage/)
- [Format Specification](https://ash12h.github.io/dymfile/format/)
- [API Reference](https://ash12h.github.io/dymfile/api/)

## Development

### Setup

```bash
# Install with dev dependencies
uv sync --extra dev --extra docs

# Install pre-commit hooks
pre-commit install
```

### Testing

```bash
pytest tests/
```

### Documentation

```bash
mkdocs serve
```

## Project Structure

```
dymfile/
├── src/dymfile/        # Source code
│   ├── reader.py       # Read DYM files
│   ├── writer.py       # Write DYM files
│   ├── backend.py      # Xarray backend
│   ├── cli.py          # Command-line tools
│   ├── _formats.py     # Data structures
│   └── _utils.py       # Utilities
├── tests/              # Test suite
├── docs/               # Documentation
└── data/               # Sample files

```

## Technologies

- **Language**: Python 3.10+
- **Package manager**: uv
- **Linter/Formatter**: ruff
- **Type checker**: pyright
- **Testing**: pytest
- **Documentation**: MkDocs + Material theme

## License

MIT License - see [LICENSE](LICENSE) file

## Acknowledgments

DYM format developed by the SEAPODYM project for oceanographic modeling.
