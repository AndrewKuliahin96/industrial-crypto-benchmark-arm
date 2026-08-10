/*
 * aead_benchmark.c
 * ----------------
 * Per-operation AEAD latency benchmark for ARM Cortex-A72 (BCM2711)
 * without ARMv8 Crypto Extensions -- Test 2 of the paper.
 *
 * Every measured operation executes the FULL per-packet OpenSSL EVP
 * sequence (context creation, key/IV setup, encryption and finalization,
 * authentication-tag retrieval, context release), so the measured
 * per-operation latency captures the realistic per-frame framing cost
 * rather than amortized steady-state throughput (Test 1, openssl speed).
 *
 * Algorithms: AES-256-GCM, ChaCha20-Poly1305 (AEAD encrypt),
 *             Ed25519 (sign + verify, one-shot EVP_DigestSign/Verify).
 *
 * Payload sizes / iterations:
 *   16/64/128/256 B -> 50,000 iters; 1024 B -> 10,000; 8192/16384 B -> 2,000;
 *   2,000 warm-up iterations before each measured series; per-op timing via
 *   clock_gettime(CLOCK_MONOTONIC_RAW).
 *
 * Output: CSV to stdout:
 *   algorithm,operation,payload_bytes,run,iters,mean_ns,sd_ns,min_ns,p50_ns,p95_ns,p99_ns
 *
 * Build:   make          (or ./build.sh; needs libssl-dev >= 3.x)
 * Run:     ./run_benchmark_c.sh results/c_benchmark_results.csv
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <math.h>

#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/err.h>
#include <openssl/opensslv.h>

static const size_t PAYLOADS[] = {16, 64, 128, 256, 1024, 8192, 16384};
#define N_PAYLOADS (sizeof(PAYLOADS) / sizeof(PAYLOADS[0]))
#define WARMUP 2000
#define TAG_LEN 16
#define IV_LEN 12
#define ED25519_MSG_LEN 64   /* typical EtherCAT-frame-sized message */

static size_t iters_for(size_t payload)
{
    if (payload <= 256) return 50000;
    if (payload <= 1024) return 10000;
    return 2000;
}

static inline uint64_t now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

static void die(const char *msg)
{
    fprintf(stderr, "FATAL: %s\n", msg);
    ERR_print_errors_fp(stderr);
    exit(1);
}

static int cmp_u64(const void *a, const void *b)
{
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return (x > y) - (x < y);
}

static void report(const char *alg, const char *op, size_t payload, int run,
                   uint64_t *samples, size_t n)
{
    double mean = 0.0, sd = 0.0;
    for (size_t i = 0; i < n; i++) mean += (double)samples[i];
    mean /= (double)n;
    for (size_t i = 0; i < n; i++) {
        double dlt = (double)samples[i] - mean;
        sd += dlt * dlt;
    }
    sd = n > 1 ? sqrt(sd / (double)(n - 1)) : 0.0;
    qsort(samples, n, sizeof(uint64_t), cmp_u64);
    printf("%s,%s,%zu,%d,%zu,%.1f,%.1f,%llu,%llu,%llu,%llu\n",
           alg, op, payload, run, n, mean, sd,
           (unsigned long long)samples[0],
           (unsigned long long)samples[n / 2],
           (unsigned long long)samples[(size_t)((double)n * 0.95)],
           (unsigned long long)samples[(size_t)((double)n * 0.99)]);
    fflush(stdout);
}

/* One full per-packet AEAD operation: ctx create -> init -> encrypt ->
 * final -> get tag -> ctx free.  The EVP_CIPHER itself is fetched once
 * outside the loop (the Python `cryptography` library also caches the
 * algorithm object across calls). */
static uint64_t aead_once(const EVP_CIPHER *cipher,
                          const unsigned char *key,
                          const unsigned char *iv,
                          const unsigned char *pt, size_t pt_len,
                          unsigned char *ct, unsigned char *tag)
{
    uint64_t t0 = now_ns();
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) die("EVP_CIPHER_CTX_new");
    int len = 0, len2 = 0;
    if (EVP_EncryptInit_ex(ctx, cipher, NULL, NULL, NULL) != 1) die("init1");
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_SET_IVLEN, IV_LEN, NULL) != 1) die("ivlen");
    if (EVP_EncryptInit_ex(ctx, NULL, NULL, key, iv) != 1) die("init2");
    if (EVP_EncryptUpdate(ctx, ct, &len, pt, (int)pt_len) != 1) die("update");
    if (EVP_EncryptFinal_ex(ctx, ct + len, &len2) != 1) die("final");
    if (EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_AEAD_GET_TAG, TAG_LEN, tag) != 1) die("tag");
    EVP_CIPHER_CTX_free(ctx);
    return now_ns() - t0;
}

static void bench_aead(const char *alg_name, const char *fetch_name, int run)
{
    EVP_CIPHER *cipher = EVP_CIPHER_fetch(NULL, fetch_name, NULL);
    if (!cipher) die("EVP_CIPHER_fetch");

    unsigned char key[32], iv[IV_LEN], tag[TAG_LEN];
    if (RAND_bytes(key, sizeof key) != 1 || RAND_bytes(iv, sizeof iv) != 1)
        die("RAND_bytes");

    unsigned char *pt = malloc(16384), *ct = malloc(16384 + 16);
    if (!pt || !ct) die("malloc");
    RAND_bytes(pt, 16384);

    for (size_t p = 0; p < N_PAYLOADS; p++) {
        size_t payload = PAYLOADS[p];
        size_t iters = iters_for(payload);
        uint64_t *samples = malloc(iters * sizeof(uint64_t));
        if (!samples) die("malloc samples");

        for (size_t i = 0; i < WARMUP; i++)
            aead_once(cipher, key, iv, pt, payload, ct, tag);
        for (size_t i = 0; i < iters; i++)
            samples[i] = aead_once(cipher, key, iv, pt, payload, ct, tag);

        report(alg_name, "encrypt", payload, run, samples, iters);
        free(samples);
    }
    free(pt); free(ct);
    EVP_CIPHER_free(cipher);
}

static void bench_ed25519(int run)
{
    EVP_PKEY *pkey = EVP_PKEY_Q_keygen(NULL, NULL, "ED25519");
    if (!pkey) die("Ed25519 keygen");

    unsigned char msg[ED25519_MSG_LEN], sig[64];
    size_t siglen = sizeof sig;
    RAND_bytes(msg, sizeof msg);

    /* one signature for the verify loop */
    {
        EVP_MD_CTX *md = EVP_MD_CTX_new();
        if (EVP_DigestSignInit(md, NULL, NULL, NULL, pkey) != 1) die("signinit");
        if (EVP_DigestSign(md, sig, &siglen, msg, sizeof msg) != 1) die("sign");
        EVP_MD_CTX_free(md);
    }

    const size_t iters = 10000;
    uint64_t *samples = malloc(iters * sizeof(uint64_t));
    if (!samples) die("malloc");

    /* --- sign: full per-op sequence (ctx create -> init -> sign -> free) --- */
    for (size_t i = 0; i < WARMUP; i++) {
        EVP_MD_CTX *md = EVP_MD_CTX_new();
        size_t sl = sizeof sig;
        EVP_DigestSignInit(md, NULL, NULL, NULL, pkey);
        EVP_DigestSign(md, sig, &sl, msg, sizeof msg);
        EVP_MD_CTX_free(md);
    }
    for (size_t i = 0; i < iters; i++) {
        uint64_t t0 = now_ns();
        EVP_MD_CTX *md = EVP_MD_CTX_new();
        size_t sl = sizeof sig;
        if (EVP_DigestSignInit(md, NULL, NULL, NULL, pkey) != 1) die("signinit");
        if (EVP_DigestSign(md, sig, &sl, msg, sizeof msg) != 1) die("sign");
        EVP_MD_CTX_free(md);
        samples[i] = now_ns() - t0;
    }
    report("Ed25519", "sign", ED25519_MSG_LEN, run, samples, iters);

    /* --- verify --- */
    for (size_t i = 0; i < WARMUP; i++) {
        EVP_MD_CTX *md = EVP_MD_CTX_new();
        EVP_DigestVerifyInit(md, NULL, NULL, NULL, pkey);
        EVP_DigestVerify(md, sig, siglen, msg, sizeof msg);
        EVP_MD_CTX_free(md);
    }
    for (size_t i = 0; i < iters; i++) {
        uint64_t t0 = now_ns();
        EVP_MD_CTX *md = EVP_MD_CTX_new();
        if (EVP_DigestVerifyInit(md, NULL, NULL, NULL, pkey) != 1) die("verinit");
        if (EVP_DigestVerify(md, sig, siglen, msg, sizeof msg) != 1) die("verify");
        EVP_MD_CTX_free(md);
        samples[i] = now_ns() - t0;
    }
    report("Ed25519", "verify", ED25519_MSG_LEN, run, samples, iters);

    free(samples);
    EVP_PKEY_free(pkey);
}

int main(int argc, char **argv)
{
    int run = (argc > 1) ? atoi(argv[1]) : 1;

    fprintf(stderr, "OpenSSL runtime: %s\n",
            OpenSSL_version(OPENSSL_VERSION));
    fprintf(stderr, "OpenSSL headers: %s\n", OPENSSL_VERSION_TEXT);

    printf("algorithm,operation,payload_bytes,run,iters,mean_ns,sd_ns,min_ns,p50_ns,p95_ns,p99_ns\n");

    bench_aead("AES-256-GCM", "AES-256-GCM", run);
    bench_aead("ChaCha20-Poly1305", "ChaCha20-Poly1305", run);
    bench_ed25519(run);

    return 0;
}
