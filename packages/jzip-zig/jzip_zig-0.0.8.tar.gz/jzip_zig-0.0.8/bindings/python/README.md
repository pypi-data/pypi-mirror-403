# jzip Python Bindings

Python bindings for `jzip` (near-lossless compression for unit-norm embedding vectors).

## Install (dev)

Requires Zig and Python 3.10+.

```bash
pip install -e .
```

## Usage

```python
import numpy as np
import jzip

x = np.random.randn(1000, 384).astype(np.float32)
x /= np.linalg.norm(x, axis=1, keepdims=True)

blob = jzip.compress(x, level=1, threads=8)
y = jzip.decompress(blob, threads=8)
```

## PyPI

```bash
pip install jzip-zig
```
