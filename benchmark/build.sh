#!/bin/bash
# build.sh — one-line build if `make` is unavailable or the Makefile was
# delivered as Makefile.txt (rename it: mv Makefile.txt Makefile).
set -e
gcc -O2 -mcpu=cortex-a72 -Wall -Wextra -o aead_benchmark aead_benchmark.c -lcrypto -lm
echo "built ./aead_benchmark"
./aead_benchmark 0 2>&1 >/dev/null | head -2
