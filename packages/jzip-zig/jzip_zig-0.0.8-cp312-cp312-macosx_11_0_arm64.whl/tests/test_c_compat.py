import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

import jzip


class TestCCompatibility(unittest.TestCase):
    def test_compressed_bytes_match_c(self):
        repo_root = Path(__file__).resolve().parents[3]
        c_exe = repo_root / "jzip"

        if not (repo_root / "Makefile").exists():
            self.skipTest("Makefile not found; cannot build C reference")

        # Build C reference binary if needed.
        if not c_exe.exists():
            subprocess.check_call(["make"], cwd=repo_root)

        # Deterministic unit-norm test input.
        rng = np.random.default_rng(123)
        n, d = 1000, 384
        x = rng.standard_normal((n, d)).astype(np.float32)
        x /= np.linalg.norm(x, axis=1, keepdims=True)

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            in_bin = td / "input.bin"
            py_out = td / "py_out.jz"
            c_out = td / "c_out.jz"

            x.tofile(in_bin)

            blob = jzip.compress(x, level=1, threads=1)
            py_out.write_bytes(blob)

            subprocess.check_call(
                [str(c_exe), "-c", str(in_bin), str(c_out), str(n), str(d), "1"],
                cwd=repo_root,
                stdout=subprocess.DEVNULL,
            )

            a = py_out.read_bytes()
            b = c_out.read_bytes()
            self.assertEqual(len(a), len(b))
            self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
