#!/usr/bin/env python3
"""
parse_results.py — parses raw OpenSSL/LibreSSL speed output into structured CSVs.
Run after run_benchmark.sh:
    python3 benchmark/parse_results.py
"""
import re, os, sys

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(SCRIPT_DIR, '..', 'results')
raw_file    = os.path.join(RESULTS_DIR, 'raw_openssl.txt')
csv_sym     = os.path.join(RESULTS_DIR, 'benchmark.csv')
csv_asym    = os.path.join(RESULTS_DIR, 'ed25519.csv')

if not os.path.exists(raw_file):
    print(f"ERROR: {raw_file} not found. Run run_benchmark.sh first.")
    sys.exit(1)

with open(raw_file) as f:
    content = f.read()

ALL_BLOCK_SIZES = [16, 64, 256, 1024, 8192, 16384]

def parse_kbs(val):
    val = val.strip()
    if val.endswith('k'):
        return float(val[:-1])
    return float(val)

def try_parse_line(label, line_pattern, content):
    """Parse a throughput line with 5 or 6 value columns."""
    for n_cols in (6, 5):
        val_pat = r'\s+([\d.]+k?)'
        pat = line_pattern + val_pat * n_cols
        m = re.search(pat, content, re.IGNORECASE)
        if m:
            sizes = ALL_BLOCK_SIZES[:n_cols]
            values = [parse_kbs(m.group(i + 1)) for i in range(n_cols)]
            return list(zip(sizes, values))
    return None

rows = []
algo_patterns = {
    'AES-256-GCM':       r'aes-256-gcm',
    'ChaCha20-Poly1305': r'chacha20[\s-]+poly\s*1305',
}

for algo, pat in algo_patterns.items():
    parsed = try_parse_line(algo, pat, content)
    if parsed:
        for bs, kbs in parsed:
            rows.append({'algorithm': algo, 'block_bytes': bs,
                         'throughput_kbs': kbs, 'throughput_mbs': kbs / 1024})
    else:
        print(f"WARNING: Could not parse {algo}")

with open(csv_sym, 'w') as f:
    f.write('algorithm,block_bytes,throughput_kbs,throughput_mbs\n')
    for r in rows:
        f.write(f"{r['algorithm']},{r['block_bytes']},{r['throughput_kbs']:.2f},{r['throughput_mbs']:.3f}\n")
print(f"Symmetric results -> {csv_sym}")

aes = {r['block_bytes']: r for r in rows if r['algorithm'] == 'AES-256-GCM'}
cha = {r['block_bytes']: r for r in rows if r['algorithm'] == 'ChaCha20-Poly1305'}
matched_sizes = sorted(set(aes.keys()) & set(cha.keys()))
if matched_sizes:
    print("\nSpeedup (ChaCha20 / AES):")
    for bs in matched_sizes:
        ratio = cha[bs]['throughput_kbs'] / aes[bs]['throughput_kbs']
        print(f"  {bs:>6} B: {ratio:.2f}x")

# Ed25519
m_sign   = re.search(r'sign\s+([\d.]+)\s+ops', content, re.IGNORECASE)
m_verify = re.search(r'verify\s+([\d.]+)\s+ops', content, re.IGNORECASE)
has_ed = False
with open(csv_asym, 'w') as f:
    f.write('operation,ops_per_sec,latency_us\n')
    for label, m in [('sign', m_sign), ('verify', m_verify)]:
        if m:
            has_ed = True
            ops = float(m.group(1))
            lat = 1e6 / ops
            f.write(f"{label},{ops:.1f},{lat:.1f}\n")
            print(f"\nEd25519 {label}: {ops:.1f} ops/s (~{lat:.0f} us)")

if has_ed:
    print(f"\nEd25519 results   -> {csv_asym}")
else:
    print("\nEd25519: no data found (LibreSSL does not support Ed25519 benchmarking).")
    print(f"Ed25519 CSV will be empty — plot_results.py will use paper fallback values.")
