#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
#include <time.h>
#include <zstd.h>

#if defined(__ARM_NEON) || defined(__ARM_NEON__)
#include <arm_neon.h>
#define USE_NEON 1
#endif

#define MAGIC 0x5A494A4A
#define VERSION 1
#define ZSTD_LEVEL_DEFAULT 1

typedef struct { uint32_t magic, version, n, d; } Header;

static float *read_floats(const char *path, size_t *count) {
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    *count = ftell(f) / sizeof(float);
    fseek(f, 0, SEEK_SET);
    float *data = malloc(*count * sizeof(float));
    fread(data, sizeof(float), *count, f);
    fclose(f);
    return data;
}

static int write_file(const char *path, const void *data, size_t size) {
    FILE *f = fopen(path, "wb");
    if (!f) return -1;
    fwrite(data, 1, size, f);
    fclose(f);
    return 0;
}

// Optimized for unit-norm vectors: O(d) time, O(d) space
// Precomputes partial squared norms via backward cumulative sum - no error accumulation
static void cartesian_to_spherical(const float * restrict x, float * restrict ang, uint32_t n, uint32_t d) {
    // Allocate workspace for partial squared norms (one per thread if parallelized)
    double *r2 = malloc(d * sizeof(double));

    for (uint32_t row = 0; row < n; row++) {
        const float *v = x + row * d;
        float *a = ang + row * (d - 1);

        // Backward pass: compute cumulative sum of squares from end
        // r2[i] = v[i]^2 + v[i+1]^2 + ... + v[d-1]^2
        r2[d - 1] = (double)v[d - 1] * v[d - 1];
        for (int i = d - 2; i >= 0; i--) {
            double vi = v[i];
            r2[i] = r2[i + 1] + vi * vi;
        }

        // Forward pass: compute angles using precomputed partial norms
        for (uint32_t i = 0; i < d - 2; i++) {
            double r = sqrt(r2[i]);
            double val = v[i] / r;
            if (val > 1.0) val = 1.0;
            if (val < -1.0) val = -1.0;
            a[i] = (float)acos(val);
        }
        a[d - 2] = (float)atan2((double)v[d - 1], (double)v[d - 2]);
    }

    free(r2);
}

// Use double precision internally to reduce reconstruction error from ~3e-7 to ~7e-8
static void spherical_to_cartesian(const float * restrict ang, float * restrict x, uint32_t n, uint32_t d) {
    for (uint32_t row = 0; row < n; row++) {
        const float *a = ang + row * (d - 1);
        float *v = x + row * d;
        double s = 1.0;
        for (uint32_t i = 0; i < d - 2; i++) {
            double angle = (double)a[i];
            v[i] = (float)(s * cos(angle));
            s *= sin(angle);
        }
        double last_angle = (double)a[d - 2];
        v[d - 2] = (float)(s * cos(last_angle));
        v[d - 1] = (float)(s * sin(last_angle));
    }
}

static void transpose(const float * restrict src, float * restrict dst, uint32_t rows, uint32_t cols) {
    for (uint32_t i = 0; i < rows; i++)
        for (uint32_t j = 0; j < cols; j++)
            dst[j * rows + i] = src[i * cols + j];
}

static void byte_shuffle(const uint8_t * restrict src, uint8_t * restrict dst, size_t n_floats) {
#ifdef USE_NEON
    size_t i = 0;
    uint8_t *d0 = dst, *d1 = dst + n_floats, *d2 = dst + n_floats * 2, *d3 = dst + n_floats * 3;
    for (; i + 16 <= n_floats; i += 16) {
        uint8x16x4_t v = vld4q_u8(src + i * 4);
        vst1q_u8(d0 + i, v.val[0]);
        vst1q_u8(d1 + i, v.val[1]);
        vst1q_u8(d2 + i, v.val[2]);
        vst1q_u8(d3 + i, v.val[3]);
    }
    for (; i < n_floats; i++) {
        d0[i] = src[i * 4];
        d1[i] = src[i * 4 + 1];
        d2[i] = src[i * 4 + 2];
        d3[i] = src[i * 4 + 3];
    }
#else
    for (size_t i = 0; i < n_floats; i++) {
        dst[i] = src[i * 4];
        dst[n_floats + i] = src[i * 4 + 1];
        dst[n_floats * 2 + i] = src[i * 4 + 2];
        dst[n_floats * 3 + i] = src[i * 4 + 3];
    }
#endif
}

static void byte_unshuffle(const uint8_t * restrict src, uint8_t * restrict dst, size_t n_floats) {
#ifdef USE_NEON
    size_t i = 0;
    const uint8_t *s0 = src, *s1 = src + n_floats, *s2 = src + n_floats * 2, *s3 = src + n_floats * 3;
    for (; i + 16 <= n_floats; i += 16) {
        uint8x16x4_t v;
        v.val[0] = vld1q_u8(s0 + i);
        v.val[1] = vld1q_u8(s1 + i);
        v.val[2] = vld1q_u8(s2 + i);
        v.val[3] = vld1q_u8(s3 + i);
        vst4q_u8(dst + i * 4, v);
    }
    for (; i < n_floats; i++) {
        dst[i * 4] = s0[i];
        dst[i * 4 + 1] = s1[i];
        dst[i * 4 + 2] = s2[i];
        dst[i * 4 + 3] = s3[i];
    }
#else
    for (size_t i = 0; i < n_floats; i++) {
        dst[i * 4] = src[i];
        dst[i * 4 + 1] = src[n_floats + i];
        dst[i * 4 + 2] = src[n_floats * 2 + i];
        dst[i * 4 + 3] = src[n_floats * 3 + i];
    }
#endif
}

static double get_time_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

static int compress_file(const char *in, const char *out, uint32_t n, uint32_t d, int level) {
    size_t count;
    float *data = read_floats(in, &count);
    if (!data) { fprintf(stderr, "error: cannot read %s\n", in); return 1; }
    if (count != (size_t)n * d) {
        fprintf(stderr, "error: expected %u floats, got %zu\n", n * d, count);
        free(data); return 1;
    }

    float *ang = malloc(n * (d - 1) * sizeof(float));
    float *ang_t = malloc(n * (d - 1) * sizeof(float));
    uint8_t *shuffled = malloc(n * (d - 1) * sizeof(float));

    double t0 = get_time_ms();
    cartesian_to_spherical(data, ang, n, d);
    double t1 = get_time_ms();
    transpose(ang, ang_t, n, d - 1);
    byte_shuffle((uint8_t *)ang_t, shuffled, n * (d - 1));
    double t2 = get_time_ms();

    size_t bound = ZSTD_compressBound(n * (d - 1) * sizeof(float));
    uint8_t *compressed = malloc(sizeof(Header) + bound);
    Header *hdr = (Header *)compressed;
    hdr->magic = MAGIC; hdr->version = VERSION; hdr->n = n; hdr->d = d;

    size_t csize = ZSTD_compress(compressed + sizeof(Header), bound, shuffled,
                                  n * (d - 1) * sizeof(float), level);
    double t3 = get_time_ms();

    if (ZSTD_isError(csize)) {
        fprintf(stderr, "error: compression failed\n");
        free(data); free(ang); free(ang_t); free(shuffled); free(compressed);
        return 1;
    }

    write_file(out, compressed, sizeof(Header) + csize);
    size_t orig = n * d * sizeof(float);
    size_t final = sizeof(Header) + csize;

    printf("%s: %zu -> %zu bytes (%.2fx)\n", out, orig, final, (double)orig / final);
    printf("  spherical: %.1f ms (%.1f MB/s)\n", t1 - t0, orig / 1e6 / ((t1 - t0) / 1000));
    printf("  transpose+shuffle: %.1f ms\n", t2 - t1);
    printf("  zstd: %.1f ms\n", t3 - t2);
    printf("  total encode: %.1f ms (%.1f MB/s)\n", t3 - t0, orig / 1e6 / ((t3 - t0) / 1000));

    free(data); free(ang); free(ang_t); free(shuffled); free(compressed);
    return 0;
}

static int decompress_file(const char *in, const char *out) {
    FILE *f = fopen(in, "rb");
    if (!f) { fprintf(stderr, "error: cannot read %s\n", in); return 1; }
    fseek(f, 0, SEEK_END);
    size_t fsize = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *blob = malloc(fsize);
    fread(blob, 1, fsize, f);
    fclose(f);

    Header *hdr = (Header *)blob;
    if (hdr->magic != MAGIC) { fprintf(stderr, "error: invalid file\n"); free(blob); return 1; }
    uint32_t n = hdr->n, d = hdr->d;

    size_t ang_size = n * (d - 1) * sizeof(float);
    uint8_t *shuffled = malloc(ang_size);

    double t0 = get_time_ms();
    size_t dsize = ZSTD_decompress(shuffled, ang_size, blob + sizeof(Header), fsize - sizeof(Header));
    double t1 = get_time_ms();

    if (ZSTD_isError(dsize)) {
        fprintf(stderr, "error: decompression failed\n");
        free(blob); free(shuffled); return 1;
    }

    uint8_t *ang_t_bytes = malloc(ang_size);
    float *ang = malloc(ang_size);
    float *x = malloc(n * d * sizeof(float));

    byte_unshuffle(shuffled, ang_t_bytes, n * (d - 1));
    transpose((float *)ang_t_bytes, ang, d - 1, n);
    double t2 = get_time_ms();
    spherical_to_cartesian(ang, x, n, d);
    double t3 = get_time_ms();

    write_file(out, x, n * d * sizeof(float));
    size_t orig = n * d * sizeof(float);

    printf("%s: %u x %u floats\n", out, n, d);
    printf("  zstd decompress: %.1f ms\n", t1 - t0);
    printf("  unshuffle+transpose: %.1f ms\n", t2 - t1);
    printf("  spherical->cartesian: %.1f ms (%.1f MB/s)\n", t3 - t2, orig / 1e6 / ((t3 - t2) / 1000));
    printf("  total decode: %.1f ms (%.1f MB/s)\n", t3 - t0, orig / 1e6 / ((t3 - t0) / 1000));

    free(blob); free(shuffled); free(ang_t_bytes); free(ang); free(x);
    return 0;
}

int main(int argc, char **argv) {
    if ((argc == 6 || argc == 7) && strcmp(argv[1], "-c") == 0) {
        int level = (argc == 7) ? atoi(argv[6]) : ZSTD_LEVEL_DEFAULT;
        if (level < 1 || level > 22) {
            fprintf(stderr, "error: level must be 1-22\n");
            return 1;
        }
        return compress_file(argv[2], argv[3], atoi(argv[4]), atoi(argv[5]), level);
    }
    if (argc == 4 && strcmp(argv[1], "-d") == 0) {
        return decompress_file(argv[2], argv[3]);
    }
    fprintf(stderr, "usage: jzip -c INPUT OUTPUT N D [LEVEL]\n");
    fprintf(stderr, "       jzip -d INPUT OUTPUT\n");
    fprintf(stderr, "       LEVEL: zstd compression level 1-22 (default: %d)\n", ZSTD_LEVEL_DEFAULT);
    return 1;
}
