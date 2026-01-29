# Install

## Fast path (PyPI wheels)

```bash
pip install qrucible
```

- Wheels ship for Linux, macOS, and Windows with Parquet support and common compression codecs (brotli, gzip, lz4, snappy, zstd) enabled.
- No Rust toolchain is required when installing from wheels.

## Editable / local builds

Prereqs:
- Python 3.12+
- Rust toolchain

Create a venv and install dev deps:
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Build the extension in editable mode:
```bash
maturin develop --release
```

One-command setup:
```bash
make setup
```

Notes:
- Cargo config uses `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1` so builds succeed with CPython 3.13 until PyO3 adds official support.
- Wheels are built with Parquet + compression codecs by default. To produce a smaller local build you can disable default features and enable only what you need: `maturin develop --release --no-default-features --features parquet`.

## Docker

Fast path (installs Qrucible from PyPI inside the image):
```bash
docker build -t qrucible:latest .
docker run --rm qrucible:latest
```

Dev image (builds from source with Rust, then runs the benchmark):
```bash
docker build -f Dockerfile.dev -t qrucible-dev:latest .
docker run --rm qrucible-dev:latest
```
