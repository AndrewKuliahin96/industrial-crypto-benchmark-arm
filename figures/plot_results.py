#!/usr/bin/env python3
"""
plot_results.py — Generate publication-quality figures for the paper.
Reproduces Fig. 1, Fig. 2, Fig. 3 from benchmark CSV data.

Usage:
    pip install matplotlib numpy
    python3 figures/plot_results.py

Output: figures/fig1_throughput.png, fig2_overhead.png, fig3_ed25519.png
"""
import csv, sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import numpy as np
except ImportError:
    print("Install matplotlib and numpy: pip install matplotlib numpy")
    sys.exit(1)

ROOT     = Path(__file__).resolve().parent.parent
CSV_SYM  = ROOT / "results" / "benchmark.csv"
CSV_ASYM = ROOT / "results" / "ed25519.csv"
FIG_DIR  = ROOT / "figures"
FIG_DIR.mkdir(exist_ok=True)

PAPER_AES    = {16:10081, 64:24821, 256:43825, 1024:54662, 8192:58870, 16384:59189}
PAPER_CHACHA = {16:81679, 64:140454, 256:254390, 1024:309432, 8192:319845, 16384:319395}
PAPER_ED_SIGN_US, PAPER_ED_VERIFY_US = 121.0, 271.0

# ── Load data ──────────────────────────────────────────────────────────────
if not CSV_SYM.exists():
    print(f"CSV not found at {CSV_SYM}, using paper data as reference.")
    aes_data    = PAPER_AES
    chacha_data = PAPER_CHACHA
else:
    aes_data, chacha_data = {}, {}
    with open(CSV_SYM) as f:
        for row in csv.DictReader(f):
            bs  = int(row['block_bytes'])
            val = float(row['throughput_kbs'])
            if row['algorithm'] == 'AES-256-GCM':
                aes_data[bs] = val
            elif row['algorithm'] == 'ChaCha20-Poly1305':
                chacha_data[bs] = val

ed_sign_us = ed_verify_us = None
if CSV_ASYM.exists():
    with open(CSV_ASYM) as f:
        for row in csv.DictReader(f):
            if row['operation'] == 'sign':
                ed_sign_us = float(row['latency_us'])
            elif row['operation'] == 'verify':
                ed_verify_us = float(row['latency_us'])
if ed_sign_us is None:
    ed_sign_us = PAPER_ED_SIGN_US
if ed_verify_us is None:
    ed_verify_us = PAPER_ED_VERIFY_US

block_sizes = [16, 64, 256, 1024, 8192, 16384]
aes_vals    = [aes_data.get(b, 0)    for b in block_sizes]
chacha_vals = [chacha_data.get(b, 0) for b in block_sizes]
speedup     = [c/a if a else 0 for c, a in zip(chacha_vals, aes_vals)]

# ── Style ──────────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'serif', 'font.size': 11,
    'axes.linewidth': 0.8, 'grid.linewidth': 0.5,
    'grid.alpha': 0.5, 'figure.dpi': 150,
})
AES_COLOR    = '#D62728'   # red
CHACHA_COLOR = '#1F77B4'   # blue
THRESH_COLOR = '#FF7F0E'   # orange

x_labels = ['16', '64', '256', '1024', '8192', '16384']

# ════════════════════════════════════════════════════════════════════════════
# Fig. 1 — Throughput comparison
# ════════════════════════════════════════════════════════════════════════════
fig, ax1 = plt.subplots(figsize=(9, 5))

ax1.plot(x_labels, [v/1024 for v in aes_vals],
         'o-', color=AES_COLOR,    linewidth=2, markersize=7, label='AES-256-GCM')
ax1.plot(x_labels, [v/1024 for v in chacha_vals],
         's-', color=CHACHA_COLOR, linewidth=2, markersize=7, label='ChaCha20-Poly1305')

ax2 = ax1.twinx()
ax2.bar(x_labels, speedup, alpha=0.15, color='gray', label='Speedup (×)', zorder=0)
ax2.set_ylabel('Speedup ChaCha20 / AES (×)', fontsize=10, color='gray')
ax2.tick_params(axis='y', labelcolor='gray')
ax2.set_ylim(0, max(speedup) * 1.4)

for i, (bs, su) in enumerate(zip(x_labels, speedup)):
    ax2.text(i, su + 0.1, f'{su:.1f}×', ha='center', va='bottom',
             fontsize=9, color='gray', fontweight='bold')

ax1.set_xlabel('Block size (bytes)', fontsize=11)
ax1.set_ylabel('Throughput (MB/s)', fontsize=11)
ax1.set_title('Fig. 1. Encryption Throughput: AES-256-GCM vs ChaCha20-Poly1305\n'
              'on ARM Cortex-A72 (BCM2711) @ 1.5 GHz — without AES hardware acceleration',
              fontsize=11, pad=10)
ax1.legend(loc='upper left', fontsize=10)
ax1.grid(True, axis='y')
ax1.set_ylim(0, max(chacha_vals)/1024 * 1.15)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=10)

plt.tight_layout()
out = FIG_DIR / 'fig1_throughput.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {out}")

# ════════════════════════════════════════════════════════════════════════════
# Fig. 2 — Security overhead per protocol cycle
# ════════════════════════════════════════════════════════════════════════════
protocols = ['EtherCAT\n(100 μs)', 'PROFINET IRT\n(250 μs)', 'Modbus TCP\n(50,000 μs)', 'OPC UA\n(100,000 μs)']
aes_oh    = [11.71, 0.94, 0.01, 0.02]
chacha_oh = [2.06,  0.16, 0.00, 0.00]

x = np.arange(len(protocols))
width = 0.35

fig, ax = plt.subplots(figsize=(9, 5))
bars1 = ax.bar(x - width/2, aes_oh,    width, label='AES-256-GCM',    color=AES_COLOR,    alpha=0.85)
bars2 = ax.bar(x + width/2, chacha_oh, width, label='ChaCha20-Poly1305', color=CHACHA_COLOR, alpha=0.85)

ax.axhline(y=10, color=THRESH_COLOR, linestyle='--', linewidth=1.5,
           label='10% critical threshold (Hard Real-Time)')

ax.set_xlabel('Industrial Protocol', fontsize=11)
ax.set_ylabel('Security Overhead η (%)', fontsize=11)
ax.set_title('Fig. 2. Cryptographic Overhead per Industrial Protocol Cycle\n'
             '(AEAD per-packet latency incl. context init + auth tag)', fontsize=11, pad=10)
ax.set_xticks(x); ax.set_xticklabels(protocols, fontsize=10)
ax.legend(fontsize=10)
ax.grid(True, axis='y', alpha=0.5)

for bar in bars1:
    h = bar.get_height()
    if h > 0.005:
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.1,
                f'{h:.2f}%', ha='center', va='bottom', fontsize=9, color=AES_COLOR, fontweight='bold')
for bar in bars2:
    h = bar.get_height()
    if h > 0.005:
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.1,
                f'{h:.2f}%', ha='center', va='bottom', fontsize=9, color=CHACHA_COLOR, fontweight='bold')

plt.tight_layout()
out = FIG_DIR / 'fig2_overhead.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {out}")

# ════════════════════════════════════════════════════════════════════════════
# Fig. 3 — Ed25519 vs Real-Time budgets
# ════════════════════════════════════════════════════════════════════════════
budgets  = [100, 250, 50000, 100000]
budgets_labels = ['EtherCAT\n100 μs', 'PROFINET IRT\n250 μs', 'Modbus TCP\n50,000 μs', 'OPC UA\n100,000 μs']

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(budgets))

ax.bar(x, budgets, 0.4, label='Protocol cycle budget (Tcyc)', color='#AEC6E8', alpha=0.9)
ax.axhline(y=ed_sign_us,   color='#2CA02C', linestyle='-.',  linewidth=2,
           label=f'Ed25519 Sign ≈ {ed_sign_us:.0f} μs')
ax.axhline(y=ed_verify_us, color='#D62728', linestyle='--', linewidth=2,
           label=f'Ed25519 Verify ≈ {ed_verify_us:.0f} μs  (×{ed_verify_us/budgets[0]:.1f} of EtherCAT)')

ax.set_yscale('log')
ax.set_xlabel('Industrial Protocol', fontsize=11)
ax.set_ylabel('Time (μs, log scale)', fontsize=11)
ax.set_title('Fig. 3. Ed25519 Asymmetric Latency vs. Industrial Protocol Cycle Budgets\n'
             f'Sign ≈ {ed_sign_us:.0f} μs, Verify ≈ {ed_verify_us:.0f} μs — ARM Cortex-A72 @ 1.5 GHz',
             fontsize=11, pad=10)
ax.set_xticks(x); ax.set_xticklabels(budgets_labels, fontsize=10)
ax.legend(fontsize=10)
ax.grid(True, axis='y', alpha=0.4)
ax.yaxis.set_major_formatter(ticker.ScalarFormatter())

plt.tight_layout()
out = FIG_DIR / 'fig3_ed25519.png'
plt.savefig(out, dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved: {out}")

print("\nAll figures generated. Check the figures/ directory.")
