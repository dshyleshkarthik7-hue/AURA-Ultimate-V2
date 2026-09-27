"""Lightweight unit tests covering the core aura/ modules.

Run with:  python -m unittest discover -s tests
No test framework beyond the stdlib is required.
"""
import sys
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aura.quality import assess
from aura.temporal import TemporalConsensus
from aura.features import FeatureExtractor
from aura.model import AuraSoftmax
from aura.perception import PerceptionEngine


CFG = {
    'quality': {'min_sharpness': 45.0, 'min_brightness': 35.0, 'max_brightness': 220.0},
    'model': {'path': '/nonexistent/model.npz', 'image_size': 32,
              'confidence_threshold': 0.72, 'margin_threshold': 0.12, 'temperature': 1.0},
    'stability': {'window': 12, 'min_votes': 8, 'min_mean_confidence': 0.70},
}


def solid_frame(value, size=64):
    return np.full((size, size, 3), value, dtype=np.uint8)


class QualityTests(unittest.TestCase):
    def test_flat_dark_frame_rejected_for_both_reasons(self):
        frame = solid_frame(5)  # flat -> no sharpness; dark -> low brightness
        result = assess(frame, CFG)
        self.assertFalse(result['ok'])
        self.assertIn('blurred', result['reason'])
        self.assertIn('lighting', result['reason'])

    def test_flat_midtone_frame_rejected_for_blur_only(self):
        frame = solid_frame(128)
        result = assess(frame, CFG)
        self.assertFalse(result['ok'])
        self.assertEqual(result['reason'], 'blurred')

    def test_textured_midtone_frame_can_pass(self):
        rng = np.random.default_rng(0)
        frame = rng.integers(0, 255, size=(64, 64, 3), dtype=np.uint8)
        result = assess(frame, CFG)
        self.assertTrue(result['ok'])
        self.assertEqual(result['reason'], 'ok')


class TemporalConsensusTests(unittest.TestCase):
    def test_no_votes_returns_none(self):
        tc = TemporalConsensus(window=5)
        self.assertIsNone(tc.result(min_votes=1, min_mean_confidence=0.5))

    def test_becomes_stable_after_enough_confident_votes(self):
        tc = TemporalConsensus(window=12)
        for _ in range(8):
            tc.update('tomato', 0.9)
        result = tc.result(min_votes=8, min_mean_confidence=0.7)
        self.assertIsNotNone(result)
        label, mean_conf, votes = result
        self.assertEqual(label, 'tomato')
        self.assertGreaterEqual(votes, 8)

    def test_not_stable_when_confidence_too_low(self):
        tc = TemporalConsensus(window=12)
        for _ in range(10):
            tc.update('tomato', 0.5)
        self.assertIsNone(tc.result(min_votes=8, min_mean_confidence=0.7))

    def test_window_drops_oldest_entries(self):
        tc = TemporalConsensus(window=3)
        for label in ['a', 'a', 'b', 'b', 'b']:
            tc.update(label, 0.9)
        # window=3 keeps only the last 3 updates: b, b, b
        self.assertEqual(len(tc.items), 3)
        self.assertTrue(all(item[0] == 'b' for item in tc.items))


class FeatureExtractorTests(unittest.TestCase):
    def test_output_shape_and_normalization(self):
        fx = FeatureExtractor(size=64)
        frame = np.random.default_rng(1).integers(0, 255, size=(80, 100, 3), dtype=np.uint8)
        feats = fx.extract(frame)
        # 12*6*4 color hist + 9 gradient hist + 16 patches * 2 stats
        self.assertEqual(feats.shape, (12 * 6 * 4 + 9 + 16 * 2,))
        self.assertTrue(np.isfinite(feats).all())


class ModelTests(unittest.TestCase):
    def test_fit_and_predict_separates_two_easy_classes(self):
        rng = np.random.default_rng(0)
        n = 60
        X0 = rng.normal(loc=-2, scale=0.3, size=(n, 5)).astype(np.float32)
        X1 = rng.normal(loc=2, scale=0.3, size=(n, 5)).astype(np.float32)
        X = np.concatenate([X0, X1])
        y = np.concatenate([np.zeros(n, dtype=np.int64), np.ones(n, dtype=np.int64)])

        model = AuraSoftmax()
        model.fit(X, y, labels=['a', 'b'], epochs=300, lr=0.2, l2=1e-4)
        pred = model.predict_proba(X).argmax(1)
        acc = (pred == y).mean()
        self.assertGreater(acc, 0.95)

    def test_save_and_load_roundtrip(self):
        import tempfile
        rng = np.random.default_rng(0)
        X = rng.normal(size=(20, 4)).astype(np.float32)
        y = rng.integers(0, 2, size=20).astype(np.int64)
        model = AuraSoftmax()
        model.fit(X, y, labels=['x', 'y'], epochs=50, lr=0.1, l2=1e-4)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.npz'
            model.save(path)
            loaded = AuraSoftmax.load(path)
            np.testing.assert_allclose(model.predict_proba(X), loaded.predict_proba(X), atol=1e-6)
            self.assertEqual(loaded.labels, ['x', 'y'])


class PerceptionEngineTests(unittest.TestCase):
    def test_bad_quality_frame_returns_raw_label_none(self):
        engine = PerceptionEngine(CFG)
        frame = solid_frame(5)
        result = engine.predict(frame)
        self.assertEqual(result['label'], 'unknown')
        self.assertIsNone(result['raw_label'])

    def test_missing_model_returns_raw_label_none(self):
        engine = PerceptionEngine(CFG)
        self.assertIsNone(engine.model)
        rng = np.random.default_rng(2)
        frame = rng.integers(0, 255, size=(64, 64, 3), dtype=np.uint8)
        result = engine.predict(frame)
        self.assertEqual(result['reason'], 'model_not_trained')
        self.assertIsNone(result['raw_label'])


if __name__ == '__main__':
    unittest.main()
