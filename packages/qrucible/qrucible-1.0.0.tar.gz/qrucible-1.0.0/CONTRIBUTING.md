# Contributing to Qrucible

Thanks for helping improve Qrucible. This guide covers local setup, testing, docs, and releases.

## Environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
maturin develop --release
```

## Tests

- Rust unit tests: `cargo test --lib`
- Python parity tests: `pytest`

## Benchmarks

Run and capture Markdown output for reporting:

```bash
python scripts/benchmark.py
```

## Docs

- Build locally:  
  ```bash
  python -m pip install .[docs]
  mkdocs serve
  ```
- Deploy: pushed changes to `main` are built and published via `.github/workflows/docs.yml` (GitHub Pages must be enabled in repo settings).

## Release flow

- Update `CHANGELOG.md` under `[Unreleased]` with user-facing changes.
- Bump the version in `pyproject.toml` if needed.
- Tag a release (`git tag v0.x.y && git push origin v0.x.y`). The `Release (PyPI)` workflow builds wheels and sdist for Linux/macOS/Windows and publishes via PyPI Trusted Publishing (OIDC). Ensure PyPI trust is configured or provide an API token in repo secrets if you prefer token-based publishing.
