PYTHON_BIN ?= python3

.PHONY: setup develop benchmark

setup:
	@PYTHON_BIN=$(PYTHON_BIN) ./scripts/setup.sh

develop:
	@. .venv/bin/activate && python -m maturin develop --release

benchmark:
	@. .venv/bin/activate && python scripts/benchmark.py
