# Cryptographic Overhead Benchmark — ARM Cortex-A72 (Raspberry Pi 4)

## Overview

This repository contains the complete benchmark suite used to obtain experimental results in the article. It measures cryptographic processing overhead of three algorithm classes on ARM Cortex-A72 (BCM2711) **without ARMv8 Crypto Extensions** (software-only), and evaluates their impact on the determinism of industrial real-time protocols: EtherCAT, PROFINET IRT, Modbus TCP, OPC UA, and MQTT.

## Repository Structure

```
.
├── benchmark/
│   ├── run_benchmark.sh     # Main entry point — runs all OpenSSL speed tests
│   └── parse_results.py     # Parses raw output into structured CSV files
├── figures/
│   ├── plot_results.py      # Reproduces Figures 1-3 from benchmark CSV data
│   └── plot_article_inline.py  # Standalone script from article appendix (hardcoded data)
├── results/                 # Auto-created by run_benchmark.sh; holds raw output + CSV data
│   ├── raw_openssl.txt
│   ├── benchmark.csv        # Symmetric cipher throughput (KB/s per block size)
│   ├── ed25519.csv          # Ed25519 ops/sec and latency (µs)
│   └── platform_info.txt    # CPU, OS, OpenSSL version, temperature
├── docs/
│   └── overhead_model.md    # Mathematical model — formulas (1)-(4) from Section 2
└── README.md
```

## Requirements

| Component   | Requirement |
|-------------|-------------|
| Hardware    | Raspberry Pi 4 Model B (BCM2711 / ARM Cortex-A72) |
| OS          | Raspberry Pi OS 64-bit (Debian-based) |
| OpenSSL     | >= 3.0 (tested with 3.5.4) |
| Python      | >= 3.9 |
| Python libs | `matplotlib`, `numpy` |

```bash
pip install matplotlib numpy
```

## Running the Benchmark

### On Raspberry Pi (full pipeline)

```bash
# 1. Clone and enter the repo
git clone https://github.com/AndrewKuliahin96/industrial-crypto-benchmark-arm.git
cd industrial-crypto-benchmark-arm

# 2. Run benchmark (takes approx. 2-3 minutes)
chmod +x benchmark/run_benchmark.sh
./benchmark/run_benchmark.sh

# 3. Parse raw output into CSV
python3 benchmark/parse_results.py

# 4. Generate figures (PNG, 150 dpi)
python3 figures/plot_results.py
```

### On any machine (figures only, using paper data)

If no benchmark CSV is present, `plot_results.py` falls back to hardcoded paper data:

```bash
pip install matplotlib numpy
python3 figures/plot_results.py
```

Or use the standalone inline script from the article appendix:

```bash
python3 figures/plot_article_inline.py
```

## Algorithms Tested

| Algorithm | Category | Purpose |
|-----------|----------|---------|
| AES-256-GCM | Block cipher (AEAD) | Industry standard |
| ChaCha20-Poly1305 | Stream cipher (AEAD) | Software-optimized alternative |
| Ed25519 | Asymmetric (EdDSA) | Device authentication / signatures |

Block sizes: **16, 64, 256, 1024, 8192, 16384 bytes** — matching typical frame sizes in the tested industrial protocols.

## Key Results

| Protocol | Cycle | AES overhead | ChaCha20 overhead |
|----------|-------|--------------|-------------------|
| EtherCAT | 100 µs | **11.71%** ⚠ | **2.06%** ✓ |
| PROFINET IRT | 250 µs | 0.94% ✓ | 0.16% ✓ |
| Modbus TCP | 50 ms | 0.01% ✓ | ~0% ✓ |
| OPC UA | 100 ms | 0.02% ✓ | ~0% ✓ |

**Ed25519 verify: ~271 µs — exceeds EtherCAT 100 µs cycle by 2.7×, precludes per-frame authentication.**

ChaCha20-Poly1305 is **5.4–5.8× faster** than AES-256-GCM for block sizes 256–16384 bytes.

## Reproducibility Notes

- Each test runs for **10 seconds** to obtain a statistically significant average
- Measurements are CPU-bound (local, no network jitter)
- Cooling: aluminum Armor Case with active cooling (38–42 °C under load)
- BCM2711 has **no ARMv8 Crypto Extensions** — AES runs entirely in software (worst-case for AES, expected baseline for ChaCha20)
- Minimum background processes during measurements

## Mathematical Model

See [`docs/overhead_model.md`](docs/overhead_model.md) for the determinism criterion and overhead formulas (1)–(4) from Section 2 of the article.

## License

Licensed under the [Apache License 2.0](LICENSE). All data and figures are provided for research reproducibility.
