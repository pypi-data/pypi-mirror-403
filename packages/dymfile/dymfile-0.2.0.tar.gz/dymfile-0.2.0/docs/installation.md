# Installation

## Requirements

- Python 3.10 or later
- numpy
- xarray

## Install from source

Clone the repository and install with uv:

```bash
git clone https://github.com/Ash12H/dymfile.git
cd dymfile
uv sync
```

Or with pip:

```bash
git clone https://github.com/Ash12H/dymfile.git
cd dymfile
pip install -e .
```

## Development installation

For development, install with dev dependencies:

```bash
uv sync --extra dev --extra docs
```

This installs additional tools:
- pytest (testing)
- ruff (linting/formatting)
- pyright (type checking)
- mkdocs (documentation)
- pre-commit (git hooks)

## Verify installation

```python
import dymfile
print(dymfile.__version__)

# Test reading a file
from dymfile import dym_to_dataset
ds = dym_to_dataset("your_file.dym")
print(ds)
```
