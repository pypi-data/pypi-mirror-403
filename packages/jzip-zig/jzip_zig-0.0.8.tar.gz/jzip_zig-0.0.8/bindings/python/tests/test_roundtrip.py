import unittest

import numpy as np

import jzip


class TestRoundtrip(unittest.TestCase):
    def test_roundtrip(self):
        rng = np.random.default_rng(123)
        x = rng.standard_normal((1000, 384)).astype(np.float32)
        x /= np.linalg.norm(x, axis=1, keepdims=True)

        blob = jzip.compress(x, level=1, threads=4)
        n, d = jzip.header(blob)
        self.assertEqual((n, d), x.shape)

        y = jzip.decompress(blob, threads=4)
        self.assertEqual(y.shape, x.shape)
        self.assertEqual(y.dtype, np.float32)

        max_err = float(np.max(np.abs(y - x)))
        self.assertLess(max_err, 1e-6)


if __name__ == "__main__":
    unittest.main()
