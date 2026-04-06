#!/usr/bin/env python3
"""
Inline visualization script from the article appendix.
Generates Fig. 1 (throughput) and Fig. 2 (overhead) using hardcoded paper data.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

FIG_DIR = Path(__file__).resolve().parent
blocks = ['16 B', '64 B', '256 B', '1024 B', '8192 B', '16384 B']
aes_speed = [10081, 24821, 43825, 54662, 58870, 59189]
chacha_speed = [81679, 140454, 254390, 309432, 319845, 319395]

# Fig. 1: Encryption Throughput
plt.figure(figsize=(10, 6))
plt.plot(blocks, np.array(aes_speed)/1024, marker='o', label='AES-256-GCM', linewidth=2)
plt.plot(blocks, np.array(chacha_speed)/1024, marker='s', label='ChaCha20-Poly1305', linewidth=2)
plt.title('Encryption Speed Comparison (Cortex-A72 @ 1.5GHz)')
plt.ylabel('Throughput (MB/s)')
plt.xlabel('Block Size')
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()
out1 = FIG_DIR / 'fig1_throughput_inline.png'
plt.savefig(out1, dpi=300)
plt.close()
print(f"Saved: {out1}")

# Fig. 2: Security Overhead
protocols = ['EtherCAT', 'PROFINET IRT', 'Modbus TCP', 'OPC UA']
aes_overhead = [11.71, 0.94, 0.01, 0.02]
chacha_overhead = [2.06, 0.16, 0.00, 0.00]

x = np.arange(len(protocols))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(x - width/2, aes_overhead, width, label='AES-256-GCM', color='salmon')
ax.bar(x + width/2, chacha_overhead, width, label='ChaCha20-Poly1305', color='skyblue')
ax.set_ylabel('Cycle Overhead (%)')
ax.set_title('Security Overhead per Industrial Protocol Cycle')
ax.set_xticks(x)
ax.set_xticklabels(protocols)
ax.axhline(y=10, color='r', linestyle='--', label='Critical Threshold (10%)')
ax.legend()
plt.tight_layout()
out2 = FIG_DIR / 'fig2_overhead_inline.png'
plt.savefig(out2, dpi=300)
plt.close()
print(f"Saved: {out2}")

print("\nDone. Inline figures saved.")
