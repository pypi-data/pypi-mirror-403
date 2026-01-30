# jzip-zig

Near-lossless compression for unit-norm embedding vectors using spherical coordinates (typically ~1.5x compression).

This repo contains:

- `jzip.c`: the original C reference implementation
- `src/jzip.zig`: a Zig 0.15.2 port which is byte-for-byte compatible with the C format on the same platform
- `jzip-zig` (PyPI): CPython extension + NumPy-friendly API (`pip install jzip-zig`, then `import jzip`)

> [!NOTE]
> “Near-lossless” here means reconstruction error is below ~1e-7 (float32 machine epsilon). Indistinguishable at float32 precision, but not bit-exact. See the paper: https://jina.ai/embedding-compression.pdf

![jzip pipeline](pipeline.png)



## Build

### C reference

```bash
make
```

### Zig CLI

```bash
zig build -Doptimize=ReleaseFast
```

This produces `zig-out/bin/jzip`.

## Usage

```bash
# Compress: input.bin (N vectors of D dimensions) -> output.jz
jzip -c input.bin output.jz N D [LEVEL]

# Decompress: output.jz -> output.bin
jzip -d output.jz output.bin
```

LEVEL is the zstd compression level (1-22, default: 1). Higher levels are slower with negligible compression gain because the spherical transform already minimizes entropy.

The Zig CLI also supports threads:

```bash
zig-out/bin/jzip -t 8 -c input.bin output.jz N D 1
```

## Example

```bash
# Compress 1000 vectors of 384 dimensions
jzip -c embeddings.bin compressed.jz 1000 384

# Compress with higher zstd level (slower, same ratio)
jzip -c embeddings.bin compressed.jz 1000 384 19

# Decompress
jzip -d compressed.jz restored.bin
```

## Python

Install from PyPI:

```bash
pip install jzip-zig
```

Usage:

```python
import numpy as np
import jzip

# float32 and unit-normalized
embeddings = np.asarray(embeddings, dtype=np.float32)
embeddings /= np.linalg.norm(embeddings, axis=1, keepdims=True)

blob = jzip.compress(embeddings, level=1, threads=8)
restored = jzip.decompress(blob, threads=8)
```

Development install (from repo root):

```bash
pip install -e .
```

The bindings are implemented as a native CPython extension using the buffer protocol (zero-copy for NumPy inputs/outputs).

### Exporting embeddings for the CLI

```python
import numpy as np

# Ensure float32 and unit-normalized
embeddings = embeddings.astype(np.float32)
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

# Save to binary
embeddings.tofile('embeddings.bin')
n, d = embeddings.shape  # use these for jzip -c
```

With sentence-transformers:

```python
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(texts).astype(np.float32)
embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
embeddings.tofile('embeddings.bin')
# jzip -c embeddings.bin out.jz {len(texts)} {model.get_sentence_embedding_dimension()}
```

Load decompressed embeddings back:

```python
restored = np.fromfile('restored.bin', dtype=np.float32).reshape(n, d)
```

## Compatibility

- File format is: 16-byte header + zstd-compressed spherical angles.
- The Zig implementation is intended to be compatible with `jzip.c`:
  - compressed bytes match for the same input on the same platform/libm
  - decoded float32 output matches the C decoder byte-for-byte

Note: using platform `libm` for `acos`/`atan2` means the compressed bytes may differ across OS/libc versions (still decodes correctly).

## File Format

Input: raw float32 binary (N x D floats, row-major)

Output: 16-byte header + zstd-compressed spherical angles

The input embeddings must be unit-normalized (L2 norm = 1).

## Algorithm

1. Convert Cartesian coordinates to spherical angles (N x D -> N x D-1)
2. Transpose angle matrix to group same-position angles
3. Byte-shuffle to group IEEE 754 exponent bytes
4. Compress with zstd

Decompression reverses these steps. Reconstruction error is ~7e-8, below float32 machine epsilon.

## Licensing

- Project code: MIT (see `LICENSE`)
- Vendored dependencies:
  - zstd (BSD license): see `third_party/zstd/LICENSE` and `THIRD_PARTY_NOTICES.md`
