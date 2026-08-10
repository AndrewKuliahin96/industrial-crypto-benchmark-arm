# Industrial Crypto Benchmark — ARM Cortex-A72

Benchmarks of cryptographic processing overhead on ARM Cortex-A72 (Raspberry Pi 4,
BCM2711, no ARMv8 Crypto Extensions) against the timing budgets of real-time
industrial protocols: EtherCAT, PROFINET IRT, Modbus TCP, and OPC UA.

Companion repository for the paper *"Cryptographic overhead in ARM-based IIoT
Edge nodes: AES-256-GCM, ChaCha20-Poly1305 and Ed25519 impact on hard real-time
industrial protocol determinism"* (Kuliahin, Msallam, Saienko).

## Repository layout

- **benchmark/** — measurement code: `openssl speed` harness (Test 1) and the
  native C per-operation AEAD benchmark (Test 2)
- **figures/** — figure-generation scripts and rendered charts
- **results/** — aggregated measurement data (CSV)
- **docs/** — the two-parameter latency model and derived feasibility boundaries

## Test 1 — steady-state cipher throughput

```bash
./benchmark/run_benchmark.sh          # openssl speed -evp, 3 s per block size, 3 runs
```

Measures amortized steady-state throughput V_alg (KB/s) for AES-256-GCM and
ChaCha20-Poly1305 over block sizes 16–16384 B. Executed on OpenSSL 3.5.5.

## Test 2 — per-operation AEAD latency (native C)

```bash
cd benchmark
make                                  # or ./build.sh   (needs libssl-dev >= 3.x)
sudo ./run_benchmark_c.sh ../results/c_benchmark_results.csv
python3 compute_model.py ../results/c_benchmark_results.csv
```

Every measured operation executes the full per-packet OpenSSL EVP sequence
(context creation, key/IV setup, encryption, finalization, tag retrieval,
context release), timed individually via `clock_gettime(CLOCK_MONOTONIC_RAW)`:
2,000 warm-up + 50,000 measured iterations for payloads ≤256 B (10,000 for
1024 B; 2,000 for 8–16 KiB), 3 independent runs, CPU pinning (`taskset`),
performance governor, thermal control. Ed25519 sign/verify are measured with
the same per-operation discipline. Executed on OpenSSL 3.5.6. The CSV also
records p50/p95/p99 percentiles per series for tail-latency analysis.

`compute_model.py` reproduces the paper's Table 3 (protocol cycle overhead),
the two-parameter model fit T_sec = T_fixed + L/V_alg, and the feasibility
boundaries (Table 4).

## Key findings (native C, mean of 3 runs)

- Per-frame cost follows T_sec = T_fixed + L/V_alg with R² ≥ 0.9999; the fitted
  V_alg matches the independent Test 1 throughput within 0.2%.
- Fixed framing cost: **2.71 µs** (AES-256-GCM) / **2.48 µs** (ChaCha20-Poly1305) —
  dominates for short industrial frames (≤256 B).
- EtherCAT (100 µs cycle, 64 B): **3.77%** (AES) / **2.54%** (ChaCha) of the cycle
  budget — below the 10% critical criterion, above the 1% conservative margin.
  Feasibility boundaries for 64-B frames: cycles ≥ 37.7/25.4 µs (10%) and
  ≥ 377/254 µs (1%).
- Ed25519 verification: **281.49 µs** = 2.81× the EtherCAT cycle budget —
  per-frame asymmetric authentication is not viable; session establishment only.

## Figures

```bash
cd figures
python3 generate_figures.py           # fig1_throughput, fig2_overhead, fig3_model_fit, fig4_asymmetric
```

## Hardware / software

Raspberry Pi 4 Model B (BCM2711, 4× Cortex-A72 @ 1.5 GHz, no ARMv8 Crypto
Extensions), passive cooling (Armor Case), 64-bit Raspberry Pi OS,
OpenSSL 3.5.x, GCC 14.

## License

Apache 2.0
