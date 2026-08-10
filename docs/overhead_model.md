# Two-parameter per-frame latency model

## Model

Per-operation (per-frame) cryptographic cost on a CPU-bound path:

```
T_sec(L) = T_fixed + L / V_alg          (equation (3) of the paper)
```

- `T_fixed` — fixed per-packet AEAD framing cost: EVP context creation, key/IV
  setup, finalization, authentication-tag retrieval, context release;
- `V_alg` — steady-state cipher throughput;
- `L` — payload size in bytes.

Relative cycle overhead against a protocol budget `T_cyc`:

```
eta = T_sec / T_cyc * 100%              (equation (4))
```

Design criteria adopted in the paper: `eta <= 10%` (critical) and `eta <= 1%`
(conservative soft margin). These are engineering design assumptions, not
normative limits.

## Fitted parameters (native C, Cortex-A72 @ 1.5 GHz, OpenSSL 3.5.6)

Least-squares fit over payloads {16, 64, 128, 256, 1024, 8192, 16384} B,
mean of 3 runs (`benchmark/compute_model.py`):

| Algorithm | T_fixed, µs | V_alg (fit), MB/s | V_alg (Test 1), MB/s | deviation | R² |
|---|---|---|---|---|---|
| AES-256-GCM | 2.71 | 59.1 | 59.2 | −0.1% | 1.00000 |
| ChaCha20-Poly1305 | 2.48 | 318.9 | 319.4 | −0.2% | 0.99997 |

The fitted `V_alg` matches the independent `openssl speed` measurement (Test 1)
within 0.2%, cross-validating the two measurement paths. Residuals ≤ 0.25 µs.

## Feasibility boundaries

Minimum admissible cycle time for per-frame software AEAD (solve
`T_sec(L) <= crit * T_cyc`):

| Frames of 64 B | AES-256-GCM | ChaCha20-Poly1305 |
|---|---|---|
| η ≤ 10% (critical) | T_cyc ≥ 37.7 µs | T_cyc ≥ 25.4 µs |
| η ≤ 1% (soft margin) | T_cyc ≥ 377 µs | T_cyc ≥ 254 µs |

For any other payload, recompute `T_sec(L)` from the fitted parameters above.

## Asymmetric reference point

Ed25519 (per-operation, full context cycle): sign 127.09 µs, verify 281.49 µs
= 2.81× the EtherCAT 100 µs budget → per-frame asymmetric authentication is not
viable at hard real-time cycle times; reserve for session establishment.
