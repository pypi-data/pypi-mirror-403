# Benchmarks

Benchmark script: `scripts/benchmark.py`.

What it does:
- Uses a synthetic intraday dataset (repeatable, licensing-safe) to stress stateful logic and grid search.
- Runs a parity check between the pure Python loop and the Rust loop on a single config (single-asset mode).
- Runs an RSI grid search in Python vs Rust and reports wall-clock timing (single-asset mode).
- Prints Markdown tables plus environment info for easy pasting into issues/docs.

## How to run

```bash
python -m pip install -r requirements.txt
maturin develop --release  # or pip install qrucible
python scripts/benchmark.py
```

## Dataset and scaling

The benchmark dataset is a synthetic intraday stream with equity-like minute returns. It is not a market model; it's designed to be repeatable and to isolate engine throughput.

You can scale dataset size via env vars:

- `QRUCIBLE_BENCH_MINUTES` (default: `200000`)
- `QRUCIBLE_BENCH_ASSETS` (default: `1`)

Example (Rust-only multi-asset run):
```bash
QRUCIBLE_BENCH_MINUTES=50000 QRUCIBLE_BENCH_ASSETS=200 python scripts/benchmark.py
```

Note: Python-vs-Rust parity and speedup is printed only when `QRUCIBLE_BENCH_ASSETS=1` (the Python reference implementation is single-asset).

## Output format

- Parity check: Python vs Rust stats for a single configuration.
- Timing table: Markdown table with implementation, configs, time, throughput, and speedup.
- Environment: OS, Python, NumPy, Qrucible version, CPU model.

## Sharing results

- Run on hardware that matches your target users.
- Paste the Markdown table and environment section into README or docs when publishing results.
- For reproducibility, keep the RNG seed and dataset size unchanged unless you also publish those changes.

## Published Results

### Apple Silicon (M-series)

**Dataset:** Synthetic intraday (200,000 bars, 1 asset)

| Implementation | Configs | Time (s) | Throughput (cfg/s) | Speedup vs Python |
| --- | --- | --- | --- | --- |
| Python loop | 21 | 8.761 | 2.4 | 1.0x |
| Rust loop | 21 | 0.020 | 1,035.2 | **431.9x** |

**Environment:**
- OS: macOS (Darwin 25.2.0, arm64)
- Python: 3.12.12
- NumPy: 2.4.1
- Qrucible: 0.1.0
- CPU: Apple Silicon (arm64)

**Key takeaways:**
- The Rust + Rayon parallel grid search achieves **430x+ speedup** over sequential Python
- Grid search throughput: **1,000+ configs/second** using Rayon thread pool (scales with cores)
- Speedup reflects both the Rust hot loop efficiency and Rayon parallelization
- Python baseline runs configs sequentially; Rust uses all available cores by default
