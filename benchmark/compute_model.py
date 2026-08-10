#!/usr/bin/env python3
"""
compute_model.py
----------------
Aggregates the C benchmark CSV (3 runs) and reproduces the paper's
Tables 3-4: per-protocol cycle overhead (equation (4)), the two-parameter
latency model fit T_sec = T_fixed + L / V_alg (equation (3)), and the
feasibility boundaries for 64-byte frames.

Usage:
    python3 compute_model.py c_benchmark_results.csv
"""

import argparse
import csv
import statistics as st

PROTOCOLS = [
    # name, cycle budget µs, payload B
    ("EtherCAT", 100, 64),
    ("PROFINET IRT", 250, 128),
    ("Modbus TCP", 50_000, 256),
    ("OPC UA", 100_000, 1024),
]

# Steady-state throughput from Test 1 (openssl speed), KB/s — for cross-validation
TEST1_V = {"AES-256-GCM": 59189, "ChaCha20-Poly1305": 319395}


def fit_linear(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    a = my - b * mx
    pred = [a + b * x for x in xs]
    ss_res = sum((y - p) ** 2 for y, p in zip(ys, pred))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return a, b, 1 - ss_res / ss_tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_file")
    args = ap.parse_args()

    acc = {}
    with open(args.csv_file, newline="") as f:
        for row in csv.DictReader(f):
            key = (row["algorithm"], row["operation"], int(row["payload_bytes"]))
            acc.setdefault(key, []).append(float(row["mean_ns"]))

    mean_us = {k: st.mean(v) / 1000.0 for k, v in acc.items()}
    cv = {k: (st.stdev(v) / st.mean(v) * 100 if len(v) > 1 else 0.0) for k, v in acc.items()}

    print("## Per-operation latency (mean of runs)\n")
    print("| Algorithm | Op | Payload, B | T_sec, µs | CV, % |")
    print("|---|---|---|---|---|")
    for k in sorted(mean_us, key=lambda k: (k[0], k[1], k[2])):
        print(f"| {k[0]} | {k[1]} | {k[2]} | {mean_us[k]:.2f} | {cv[k]:.2f} |")

    print("\n## Table 3 — protocol cycle overhead (equation (4))\n")
    print("| Protocol | T_cyc, µs | Payload, B | T_sec(AES), µs | AES, % | T_sec(ChaCha), µs | ChaCha, % |")
    print("|---|---|---|---|---|---|---|")
    for proto, budget, payload in PROTOCOLS:
        ta = mean_us.get(("AES-256-GCM", "encrypt", payload))
        tc = mean_us.get(("ChaCha20-Poly1305", "encrypt", payload))
        print(f"| {proto} | {budget:,} | {payload} | {ta:.2f} | {ta/budget*100:.3f} | "
              f"{tc:.2f} | {tc/budget*100:.3f} |")

    print("\n## Table 4 — model fit T_sec = T_fixed + L/V and feasibility boundaries\n")
    print("| Algorithm | T_fixed, µs | V fit, MB/s | V Test 1, MB/s | dev, % | R² | "
          "min T_cyc @10% (64 B), µs | min T_cyc @1% (64 B), µs |")
    print("|---|---|---|---|---|---|---|---|")
    for alg in ("AES-256-GCM", "ChaCha20-Poly1305"):
        pts = sorted((k[2], v) for k, v in mean_us.items() if k[0] == alg and k[1] == "encrypt")
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        a, b, r2 = fit_linear(xs, ys)
        v_fit = 1 / b            # bytes/µs == MB/s (decimal)
        v_t1 = TEST1_V[alg] / 1000.0
        t64 = mean_us[(alg, "encrypt", 64)]
        print(f"| {alg} | {a:.2f} | {v_fit:.1f} | {v_t1:.1f} | {(v_fit-v_t1)/v_t1*100:+.1f} | "
              f"{r2:.5f} | {t64/0.10:.1f} | {t64/0.01:.0f} |")

    ed = mean_us.get(("Ed25519", "verify", 64))
    sign = mean_us.get(("Ed25519", "sign", 64))
    if ed:
        print(f"\nEd25519: sign {sign:.2f} µs (~{1e6/sign:,.0f} op/s), "
              f"verify {ed:.2f} µs (~{1e6/ed:,.0f} op/s) = {ed/100:.2f}x the EtherCAT budget.")


if __name__ == "__main__":
    main()
