<div style="text-align: center;" align="center">
   <a href="https://pypi.org/project/cl-forge/" style="text-decoration: none;">
      <img src="https://img.shields.io/pypi/v/cl-forge.svg" alt="pypi">
   </a>
   <a href="https://github.com/mschiaff/cl-forge/actions/workflows/python-package.yml" style="text-decoration: none;">
      <img src="https://github.com/mschiaff/cl-forge/actions/workflows/python-package.yml/badge.svg?branch=main" alt="python package">
   </a>
   <a href="https://github.com/mschiaff/cl-forge/actions/workflows/release-python.yml" style="text-decoration: none;">
      <img src="https://github.com/mschiaff/cl-forge/actions/workflows/release-python.yml/badge.svg" alt="python release">
   </a>
</div>

# cl-forge 🇨🇱

Simple yet powerful Chilean and other tools written in Rust and Python.

`cl-forge` provides a collection of high-performance utilities for common Chilean data formats and API integrations. The core logic is implemented in Rust for maximum speed, with a clean and easy-to-use Python interface.

## Features

- **Verify**: Efficiently validate and manipulate Chilean RUT/RUN and PPU (License Plates).
- **CMF API**: A simple client to interact with the Chilean Financial Market Commission (CMF) API.
- **High Performance**: Core logic written in Rust.
- **Lazy Loading**: Submodules are loaded only when needed to keep the initial import fast.
- **Type Safety**: Full type hints and `.pyi` stubs for excellent IDE support.

## Installation

### From PyPI

```bash
pip install cl-forge
```

Or using `uv`:

```bash
uv add cl-forge
```

### From Source

#### Using `uv` (Recommended)

```bash
uv pip install git+https://github.com/mschiaff/cl-forge.git
```

#### Using `pip`

```bash
pip install git+https://github.com/mschiaff/cl-forge.git
```

*Note: Building from source requires a Rust toolchain installed on your system.*

## Usage

### Verification (RUT & PPU)

```python
from cl_forge import verify

# Validate a RUT
is_valid = verify.validate_rut("12345678", "5")
print(f"RUT is valid: {is_valid}")

# Calculate RUT verifier
dv = verify.calculate_verifier("12345678")
print(f"Verifier digit: {dv}")

# Generate random RUTs
ruts = verify.generate(n=3, min=1_000_000, max=2_000_000, seed=42)
print(ruts)
# [{'correlative': 1133512, 'verifier': '9'}, ...]

# Work with PPUs (License Plates)
ppu = verify.Ppu("PHZF55")
print(f"Normalized: {ppu.normalized}")  # PHZF55
print(f"Verifier: {ppu.verifier}")      # K
print(f"Complete: {ppu.complete}")      # PHZF55-K
```

### CMF API Client

To use the CMF API, you need an API key. You can request one at [CMF Chile](https://api.cmfchile.cl/api_cmf/contactanos.jsp).

#### Generic Client

```python
from cl_forge.cmf import CmfClient

client = CmfClient(api_key="your_api_key_here")

# Get IPC data
ipc_data = client.get(path="/ipc")
print(ipc_data) # {'IPCs': [{'Valor': '-0,2', 'Fecha': '2025-12-01'}]}
```

#### IPC Specialist Client

The `Ipc` class provides a more convenient way to interact with IPC-related endpoints, returning parsed `Pydantic` objects.

```python
from cl_forge.cmf import Ipc

ipc_client = Ipc(api_key="your_api_key_here")

# Get current IPC
current_ipc = ipc_client.current()
print(f"Date: {current_ipc.date}, Value: {current_ipc.value}")

# Get IPC for a specific year
year_ipc = ipc_client.year(2024)
for record in year_ipc:
    print(f"{record.date.strftime('%Y-%m')}: {record.value}")
```

See the [CMF API documentation](https://api.cmfchile.cl/documentacion/index.html) for details about the available endpoints.

## Development

This project uses [maturin](https://github.com/PyO3/maturin) to build the Rust extension.

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/mschiaff/cl-forge.git
   cd cl-forge
   ```

2. Install development dependencies (using [uv](https://github.com/astral-sh/uv)):
   ```bash
   uv sync --all-groups
   ```

3. Build the Rust extension in develop mode:
   ```bash
   uv run maturin develop
   ```

### Running Tests

```bash
uv run pytest
```

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
