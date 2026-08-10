#!/bin/bash
# run_benchmark_c.sh — run the native-C AEAD benchmark (Test 2) on Raspberry Pi 4
# under controlled conditions: performance governor, CPU pinning, cool-downs.
#
# Usage:  ./run_benchmark_c.sh [output.csv]
set -euo pipefail

OUT="${1:-c_benchmark_results.csv}"
BIN=./aead_benchmark
CPU=3   # pin to an isolated core; core 3 is usually least loaded

[ -x "$BIN" ] || { echo "Build first: make (or ./build.sh)"; exit 1; }

echo "== Environment =="
uname -a
grep -m1 "^model name\|^Model" /proc/cpuinfo || true
echo "Crypto extensions (should NOT list aes on BCM2711):"
grep -m1 Features /proc/cpuinfo || true

if command -v vcgencmd >/dev/null; then
  echo "Temp before: $(vcgencmd measure_temp)"
  vcgencmd get_throttled
fi

if [ -w /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]; then
  for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance | sudo tee "$g" >/dev/null
  done
  echo "Governor set to performance"
else
  echo "NOTE: run with sudo to set the performance governor" >&2
fi

echo "== Running 3 independent runs (pinned to CPU $CPU) =="
rm -f "$OUT"
for run in 1 2 3; do
  echo "--- run $run ---"
  if [ "$run" -eq 1 ]; then
    taskset -c $CPU nice -n -10 "$BIN" "$run" >> "$OUT"
  else
    taskset -c $CPU nice -n -10 "$BIN" "$run" | tail -n +2 >> "$OUT"
  fi
  sleep 10   # cool-down between runs
  if command -v vcgencmd >/dev/null; then
    echo "Temp after run $run: $(vcgencmd measure_temp)"
  fi
done

echo "== Done: $OUT =="
echo "Next: python3 compute_model.py $OUT"
