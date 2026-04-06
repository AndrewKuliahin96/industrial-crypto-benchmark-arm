#!/usr/bin/env bash
# =============================================================================
# ARM Cryptographic Benchmark — Raspberry Pi 4 (BCM2711 / Cortex-A72)
# Paper: Cryptographic Overhead in ARM-Based IIoT Edge Nodes
# Compatible with: OpenSSL >= 3.0 (full) and LibreSSL (limited)
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/../results"
mkdir -p "$RESULTS_DIR"

RAW_FILE="$RESULTS_DIR/raw_openssl.txt"
META_FILE="$RESULTS_DIR/platform_info.txt"
DURATION=10

SSL_VERSION="$(openssl version 2>&1)"
IS_LIBRESSL=false
if echo "$SSL_VERSION" | grep -qi libressl; then
  IS_LIBRESSL=true
fi

# 1. Metadata
{
  echo "Date: $(date '+%Y-%m-%dT%H:%M:%S%z')"
  echo "SSL:  $SSL_VERSION"
  echo "CPU Features: $(grep -m1 'Features' /proc/cpuinfo 2>/dev/null || sysctl -n machdep.cpu.brand_string 2>/dev/null || echo N/A)"
  vcgencmd measure_temp 2>/dev/null || true
} | tee "$META_FILE"

if $IS_LIBRESSL; then
  echo ""
  echo "WARNING: LibreSSL detected. Using compatible flags (no -seconds/-bytes)."
  echo "         For full benchmark with custom block sizes, use OpenSSL >= 3.0."
  echo "         On macOS: brew install openssl && export PATH=\"\$(brew --prefix openssl)/bin:\$PATH\""
  echo ""
fi

# 2. AES-256-GCM
echo "=== AES-256-GCM ===" | tee "$RAW_FILE"
if $IS_LIBRESSL; then
  openssl speed -evp aes-256-gcm 2>&1 | tee -a "$RAW_FILE"
else
  openssl speed -evp aes-256-gcm -seconds "$DURATION" -bytes 16 64 256 1024 8192 16384 2>&1 | tee -a "$RAW_FILE"
fi
echo "" >> "$RAW_FILE"

# 3. ChaCha20-Poly1305
echo "=== ChaCha20-Poly1305 ===" | tee -a "$RAW_FILE"
if $IS_LIBRESSL; then
  openssl speed chacha20-poly1305 2>&1 | tee -a "$RAW_FILE"
else
  openssl speed -evp chacha20-poly1305 -seconds "$DURATION" -bytes 16 64 256 1024 8192 16384 2>&1 | tee -a "$RAW_FILE"
fi
echo "" >> "$RAW_FILE"

# 4. Ed25519
echo "=== Ed25519 ===" | tee -a "$RAW_FILE"
if $IS_LIBRESSL; then
  echo "SKIPPED: LibreSSL does not support Ed25519 benchmarking." | tee -a "$RAW_FILE"
else
  openssl speed ed25519 -seconds "$DURATION" 2>&1 | tee -a "$RAW_FILE"
fi

echo ""
echo "Done. Raw output saved to: $RAW_FILE"
echo "Next steps:"
echo "  python3 benchmark/parse_results.py   # parse into CSV"
echo "  python3 figures/plot_results.py       # generate figures"
