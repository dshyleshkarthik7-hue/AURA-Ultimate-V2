import unittest
import numpy as np
from aura.features import FeatureExtractor


class FeatureContractTests(unittest.TestCase):
    def test_canonical_contract_is_329_finite_values(self):
        self.assertEqual(FeatureExtractor.CONTRACT, 'opencv-v1-329')
        fx = FeatureExtractor(size=32, roi={"mode": "center", "width_ratio": .82, "height_ratio": .82})
        rng = np.random.default_rng(123)
        frame = rng.integers(0, 256, size=(64, 80, 3), dtype=np.uint8)
        first = fx.extract(frame)
        second = fx.extract(frame)
        self.assertEqual(first.shape, (329,))
        self.assertTrue(np.isfinite(first).all())
        np.testing.assert_array_equal(first, second)

    def test_uniform_frame_has_stable_normalized_histograms(self):
        fx = FeatureExtractor(size=32)
        frame = np.full((64, 64, 3), 128, dtype=np.uint8)
        out = fx.extract(frame)
        self.assertAlmostEqual(float(out[:288].sum()), 1.0, places=5)
        self.assertAlmostEqual(float(out[288:297].sum()), 0.0, places=6)
