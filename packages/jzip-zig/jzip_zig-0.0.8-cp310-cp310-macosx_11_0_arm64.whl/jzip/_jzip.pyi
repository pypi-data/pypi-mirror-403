from __future__ import annotations

from typing import Tuple

import numpy as np
import numpy.typing as npt


def header(blob: bytes) -> Tuple[int, int]:
    """Return (n, d) from a .jz blob."""


def compress(
    x: npt.NDArray[np.float32],
    n: int,
    d: int,
    level: int = 1,
    threads: int = 1,
) -> bytes:
    """Compress float32 data into .jz bytes."""


def decompress_into(
    blob: bytes,
    out: npt.NDArray[np.float32],
    threads: int = 1,
) -> None:
    """Decompress .jz blob into a preallocated float32 array."""


def ctx_new(threads: int = 1) -> object: ...


def ctx_compress(
    ctx: object,
    x: npt.NDArray[np.float32],
    n: int,
    d: int,
    level: int = 1,
) -> bytes: ...


def ctx_decompress_into(
    ctx: object,
    blob: bytes,
    out: npt.NDArray[np.float32],
) -> None: ...


class Context:
    ...
