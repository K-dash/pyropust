# Benchmarks

This document records reproducible benchmark results for pyropust. The goal is to show where Blueprint helps, where it does not, and how results depend on workload shape. Treat these as measurements, not guarantees.

## How to Run

```bash
uv run python bench/bench_blueprint_vs_python.py
```

The benchmark builds the Blueprint in setup and measures `run()` only. This isolates execution from pipeline construction.

## Benchmark Cases

The benchmark script exposes the following cases:

- `pipeline`: compares a multi-op Python pipeline vs Blueprint of equivalent logic.
- `tiny_op`: compares a single tiny operation overhead.
- `multi_run`: compares repeated `run()` calls on a single-op Blueprint vs a single `run()` on a multi-op Blueprint (boundary-crossing cost).
- `map_py`: compares repeated Python callback execution in Blueprint vs equivalent pure-Python loop.
- `json_decode_str`: compares JSON parsing + field access + uppercase on string input (Blueprint turbo path vs `json.loads`).
- `json_decode_bytes`: same as above but input is UTF-8 bytes.

Common parameters:
- `BENCH_TARGET_TIME`: target time per measurement
- `BENCH_REPEAT`: number of repeats
- `BENCH_SIZES`: input sizes (e.g., medium, large)
- `BENCH_PIPE_COUNTS`: number of pipeline steps
- `BENCH_CASES`: which cases to run

## Results

### Latest Run

Environment:
- OS/CPU: Darwin 25.1.0 (arm64)
- Python: 3.13.7
- Rust: 1.92.0
- pyropust: 5f2d321
- Parameters: BENCH_TARGET_TIME=0.5, BENCH_REPEAT=7, BENCH_PIPE_COUNTS=10, BENCH_SIZES=medium,large

Summary tables (seconds, lower is better):

Medium (pipe_count=10)

| Case | Python (s) | Blueprint (s) | Ratio |
| --- | --- | --- | --- |
| pipeline | 0.088251 | 0.153107 | 1.73x |
| tiny_op | 0.131521 | 0.171186 | 1.30x |
| multi_run | 0.105338 | 0.155974 | 1.48x |
| json_decode_str | 0.111899 | 0.177877 | 1.59x |
| json_decode_bytes | 0.110190 | 0.100701 | 0.91x |

Large (pipe_count=10)

| Case | Python (s) | Blueprint (s) | Ratio |
| --- | --- | --- | --- |
| pipeline | 0.190850 | 0.162010 | 0.85x |
| tiny_op | 0.141386 | 0.121089 | 0.86x |
| multi_run | 0.176107 | 0.164124 | 0.93x |
| json_decode_str | 0.118346 | 0.099097 | 0.84x |
| json_decode_bytes | 0.118416 | 0.198751 | 1.68x |

MapPy (pipe_count=10, target_time=0.5, repeat=7)

| Size | Python (s) | Blueprint (s) | Ratio |
| --- | --- | --- | --- |
| medium | 0.629757 | 0.913751 | 1.45x |
| large | 0.809909 | 0.943101 | 1.16x |

## Interpretation Notes

- Performance is workload-dependent; small ops can be dominated by overhead.
- Larger pipelines and repeated runs can benefit from fewer Python/Rust boundary crossings.
- Changes in input size or operator mix can flip results.
- Always compare against the same environment and parameters.

## When Blueprint Is Likely to Help

- Pipelines with multiple operations where boundary-crossing dominates
- Workloads with heavier per-step logic
- Cases where JSON decoding runs on the Rust side first

## When Blueprint Is Likely to Be Slower

- Single tiny operators
- Workloads dominated by Python-level overhead or type conversions
- Small inputs where setup dominates
