"""jzip - near-lossless embedding compression."""

from __future__ import annotations

from importlib.metadata import version as _pkg_version
import os
from typing import Tuple

import numpy as np

from . import _jzip as _ext

__version__ = _pkg_version("jzip-zig")


def _default_threads() -> int:
    try:
        return int(os.getenv("JZIP_THREADS", "1"))
    except Exception:
        return 1


def header(blob: bytes) -> Tuple[int, int]:
    """Return (n, d) from a .jz blob."""
    return _ext.header(blob)


def compress(x: np.ndarray, *, level: int = 1, threads: int | None = None) -> bytes:
    """Compress float32 array (n, d) into .jz bytes."""
    if threads is None:
        threads = _default_threads()

    x = np.ascontiguousarray(x, dtype=np.float32)
    if x.ndim != 2:
        raise ValueError("x must be a 2D array")
    n, d = x.shape
    return _ext.compress(x, int(n), int(d), int(level), int(threads))


def decompress(blob: bytes, *, threads: int | None = None) -> np.ndarray:
    """Decompress .jz bytes into float32 array (n, d)."""
    if threads is None:
        threads = _default_threads()

    n, d = _ext.header(blob)
    out = np.empty((n, d), dtype=np.float32)
    _ext.decompress_into(blob, out, int(threads))
    return out


class Context:
    """Reusable native context (thread pool + scratch)."""

    def __init__(self, threads: int = 1) -> None:
        self._ctx = _ext.ctx_new(int(threads))

    def compress(self, x: np.ndarray, n: int, d: int, level: int = 1) -> bytes:
        x = np.ascontiguousarray(x, dtype=np.float32)
        return _ext.ctx_compress(self._ctx, x, int(n), int(d), int(level))

    def decompress_into(self, blob: bytes, out: np.ndarray) -> None:
        out = np.ascontiguousarray(out, dtype=np.float32)
        _ext.ctx_decompress_into(self._ctx, blob, out)


__all__ = [
    "Context",
    "compress",
    "decompress",
    "header",
]
