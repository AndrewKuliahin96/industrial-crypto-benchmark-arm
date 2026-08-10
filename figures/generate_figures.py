#!/usr/bin/env python3
"""
generate_figures.py — regenerates Figures 1-4 of the manuscript.

Fig. 1  fig1_throughput.png     steady-state cipher throughput (Test 1, openssl speed)
Fig. 2  fig2_overhead.png       cycle overhead per protocol vs 10%/1% thresholds
Fig. 3  fig3_model_fit.png      measured per-op latency vs payload + model fit
Fig. 4  fig4_asymmetric.png     symmetric vs asymmetric per-op latency vs budgets

Figs. 2-4 use the native-C benchmark results (mean of 3 runs, see
results/c_benchmark_results.csv); Fig. 1 uses the Test 1 (openssl speed)
throughput data of Table 2. All outputs: 300 dpi.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RED, BLUE, PURPLE, DPURPLE = "#d62728", "#1f77b4", "#9e77c8", "#5e3a8c"

# ---- Native-C measurements (mean of 3 runs), µs ----
L = np.array([16, 64, 128, 256, 1024, 8192, 16384], dtype=float)
AES = np.array([2.76, 3.77, 5.00, 7.17, 20.11, 141.08, 279.90])
CHA = np.array([2.50, 2.54, 2.93, 3.23, 5.82, 28.28, 53.80])
ED_SIGN, ED_VERIFY = 127.09, 281.49

# =========================== Fig. 1 ===========================
# Test 1 (openssl speed -evp) steady-state throughput, KB/s — Table 2
B1 = np.array([16, 64, 256, 1024, 8192, 16384], dtype=float)
AES_T1 = np.array([10081, 24821, 43825, 54662, 58870, 59189]) / 1000.0   # MB/s
CHA_T1 = np.array([81679, 140454, 254390, 309432, 319845, 319395]) / 1000.0

fig, ax = plt.subplots(figsize=(10.66, 6.16))
ax.plot(B1, AES_T1, "-o", color=RED, lw=1.8, ms=8, mec="white", mew=1.2,
        label="AES-256-GCM", zorder=3)
ax.plot(B1, CHA_T1, "-o", color=BLUE, lw=1.8, ms=8, mec="white", mew=1.2,
        label="ChaCha20-Poly1305", zorder=3)
for x_, y_ in ((B1[-1], AES_T1[-1]), (B1[-1], CHA_T1[-1])):
    ax.annotate(f"{y_:.1f} MB/s", (x_, y_), textcoords="offset points",
                xytext=(-6, 8), ha="right", fontsize=10.5, fontweight="bold")
ax.set_xscale("log")
ax.set_xticks(B1)
ax.set_xticklabels([str(int(b)) for b in B1], fontsize=11)
ax.set_xlabel("Block size (bytes, log scale)", fontsize=13)
ax.set_ylabel("Throughput (MB/s)", fontsize=13)
ax.set_ylim(0, 355)
ax.grid(color="#dddddd", lw=0.6); ax.set_axisbelow(True)
ax.legend(loc="upper left", fontsize=11, framealpha=0.95)
for s_ in ("top", "right"): ax.spines[s_].set_visible(False)
fig.tight_layout(); fig.savefig("fig1_throughput.png", dpi=300); plt.close(fig)

# =========================== Fig. 2 ===========================
protocols = ["EtherCAT", "PROFINET IRT", "Modbus TCP", "OPC UA"]
eta_aes = [3.77, 2.00, 0.014, 0.020]
eta_cha = [2.54, 1.17, 0.006, 0.006]

x = np.arange(4); w = 0.32
fig, ax = plt.subplots(figsize=(11.1, 6.1))
for dx, vals, color, label in [(-w/2, eta_aes, RED, "AES-256-GCM"),
                               (+w/2, eta_cha, BLUE, "ChaCha20-Poly1305")]:
    ax.bar(x + dx, vals, width=w*0.92, color=color, label=label, zorder=3)
    for xp, v in zip(x + dx, vals):
        ax.annotate(f"{v:.2f}%" if v >= 0.1 else f"{v:.3f}%", (xp, v),
                    textcoords="offset points", xytext=(0, 3), ha="center",
                    fontsize=10, fontweight="bold", zorder=4)
ax.axhline(10, color=RED, ls="--", lw=1.3, zorder=2, label="Critical threshold (10 %)")
ax.axhline(1, color="#7f7f7f", ls="--", lw=1.3, zorder=2, label="Soft threshold (1 %)")
ax.set_yscale("log"); ax.set_ylim(3e-3, 30)
ax.set_xticks(x); ax.set_xticklabels(protocols, fontsize=12)
ax.set_xlabel("Industrial protocol", fontsize=13)
ax.set_ylabel("Cycle overhead η (%, log scale)", fontsize=13)
ax.grid(axis="y", which="both", color="#dddddd", lw=0.6); ax.set_axisbelow(True)
h, l = ax.get_legend_handles_labels()
ax.legend([h[i] for i in (2, 3, 0, 1)], [l[i] for i in (2, 3, 0, 1)],
          loc="upper right", fontsize=10.5, framealpha=0.95)
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig("fig2_overhead.png", dpi=300); plt.close(fig)

# =========================== Fig. 3 ===========================
fig, ax = plt.subplots(figsize=(11.1, 6.1))
Lm = np.logspace(np.log10(12), np.log10(20000), 200)
for T, color, name in [(AES, RED, "AES-256-GCM"), (CHA, BLUE, "ChaCha20-Poly1305")]:
    b, a = np.polyfit(L, T, 1)
    r2 = 1 - (((T - (a + b*L))**2).sum() / ((T - T.mean())**2).sum())
    ax.plot(Lm, a + b*Lm, color=color, lw=1.6, zorder=2,
            label=f"{name}: model  $T_{{fixed}}$={a:.2f} μs,  V={1/b:.0f} MB/s,  R²={r2:.5f}")
    ax.plot(L, T, "o", color=color, ms=8, mec="white", mew=1.2, zorder=3,
            label=f"{name}: measured")
ax.axhspan(2.4, 2.8, color="#bbbbbb", alpha=0.35, zorder=1)
ax.annotate("fixed per-frame cost  ≈2.5–2.7 μs", (13.5, 2.28), fontsize=10.5,
            color="#555555", va="top")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(12, 22000); ax.set_ylim(1.8, 400)
ax.set_xlabel("Payload size L (bytes, log scale)", fontsize=13)
ax.set_ylabel("Per-operation latency $T_{sec}$ (μs, log scale)", fontsize=13)
ax.grid(which="both", color="#dddddd", lw=0.6); ax.set_axisbelow(True)
ax.legend(loc="upper left", fontsize=10.5, framealpha=0.95)
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig("fig3_model_fit.png", dpi=300); plt.close(fig)

# =========================== Fig. 4 ===========================
fig, ax = plt.subplots(figsize=(9.1, 6.1))
names = ["AES-256-GCM\nAEAD, 64 B", "ChaCha20-Poly1305\nAEAD, 64 B",
         "Ed25519\nsign", "Ed25519\nverify"]
vals = [AES[1], CHA[1], ED_SIGN, ED_VERIFY]
colors = [RED, BLUE, PURPLE, DPURPLE]
bars = ax.bar(np.arange(4), vals, width=0.62, color=colors, zorder=3)
for xp, v in zip(np.arange(4), vals):
    ax.annotate(f"{v:.2f} μs", (xp, v), textcoords="offset points", xytext=(0, 4),
                ha="center", fontsize=11, fontweight="bold", zorder=4)
ax.axhline(100, color=RED, ls="--", lw=1.3, zorder=2)
ax.axhline(250, color="#7f7f7f", ls="--", lw=1.3, zorder=2)
ax.annotate("EtherCAT budget (100 μs)", (-0.42, 100), fontsize=10.5, color=RED,
            ha="left", va="bottom")
ax.annotate("PROFINET IRT budget (250 μs)", (-0.42, 250), fontsize=10.5,
            color="#555555", ha="left", va="bottom")
ax.set_yscale("log"); ax.set_ylim(1.5, 700)
ax.set_xticks(np.arange(4)); ax.set_xticklabels(names, fontsize=10.5)
ax.set_ylabel("Per-operation latency (μs, log scale)", fontsize=13)
ax.grid(axis="y", which="both", color="#dddddd", lw=0.6); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig("fig4_asymmetric.png", dpi=300); plt.close(fig)

print("saved fig1_throughput.png fig2_overhead.png fig3_model_fit.png fig4_asymmetric.png")
