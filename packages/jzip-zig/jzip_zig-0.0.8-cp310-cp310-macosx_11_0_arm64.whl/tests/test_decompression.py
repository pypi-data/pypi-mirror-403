import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

import jzip


class TestDecompression(unittest.TestCase):
    def test_python_roundtrip_near_lossless(self):
        rng = np.random.default_rng(123)
        x = rng.standard_normal((1000, 384)).astype(np.float32)
        x /= np.linalg.norm(x, axis=1, keepdims=True)

        blob = jzip.compress(x, level=1, threads=4)
        y = jzip.decompress(blob, threads=4)

        self.assertEqual(x.shape, y.shape)
        self.assertEqual(x.dtype, y.dtype)

        max_err = float(np.max(np.abs(y - x)))
        self.assertLess(max_err, 1e-6)

    def test_python_and_c_decompress_match_bytes(self):
        repo_root = Path(__file__).resolve().parents[3]
        c_exe = repo_root / "jzip"
        if not (repo_root / "Makefile").exists():
            self.skipTest("Makefile not found; cannot build C reference")
        if not c_exe.exists():
            subprocess.check_call(["make"], cwd=repo_root)

        rng = np.random.default_rng(123)
        n, d = 1000, 384
        x = rng.standard_normal((n, d)).astype(np.float32)
        x /= np.linalg.norm(x, axis=1, keepdims=True)

        # Use Python-produced blob and compare Python vs C decompression outputs.
        blob = jzip.compress(x, level=1, threads=1)
        y = jzip.decompress(blob, threads=1)

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            py_out = td / "py_out.jz"
            c_dec = td / "c_dec.bin"

            py_out.write_bytes(blob)
            subprocess.check_call(
                [str(c_exe), "-d", str(py_out), str(c_dec)],
                cwd=repo_root,
                stdout=subprocess.DEVNULL,
            )

            c_bytes = c_dec.read_bytes()
            self.assertEqual(y.tobytes(), c_bytes)


if __name__ == "__main__":
    unittest.main()
