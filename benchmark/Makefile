# Makefile for aead_benchmark.c
#
# IMPORTANT: link against the SAME OpenSSL 3.5.5 build that the Python
# benchmark used. If it lives in a non-standard prefix (e.g. /opt/openssl-3.5.5),
# set OPENSSL_PREFIX:
#
#   make OPENSSL_PREFIX=/opt/openssl-3.5.5
#
# Check afterwards that the runtime version printed by the binary says 3.5.5.

CC ?= gcc
CFLAGS = -O2 -mcpu=cortex-a72 -Wall -Wextra
TARGET = aead_benchmark

ifdef OPENSSL_PREFIX
CFLAGS += -I$(OPENSSL_PREFIX)/include
LDFLAGS += -L$(OPENSSL_PREFIX)/lib -Wl,-rpath,$(OPENSSL_PREFIX)/lib
# some builds install to lib64:
LDFLAGS += -L$(OPENSSL_PREFIX)/lib64 -Wl,-rpath,$(OPENSSL_PREFIX)/lib64
endif

LDLIBS = -lcrypto -lm

all: $(TARGET)

$(TARGET): aead_benchmark.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS) $(LDLIBS)

clean:
	rm -f $(TARGET)

.PHONY: all clean
