import tempfile,unittest
from pathlib import Path
import numpy as np
from aura.model import AuraSoftmax
class ModelTests(unittest.TestCase):
 def test_roundtrip_preserves_calibration(self):
  m=AuraSoftmax();X=np.random.default_rng(1).normal(size=(30,4)).astype(np.float32);y=np.tile([0,1,2],10);m.fit(X,y,['a','b','c'],epochs=5);m.temperature=1.7;m.unknown_threshold=.63
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'m.npz';m.save(p);q=AuraSoftmax.load(p);self.assertEqual(q.labels,m.labels);self.assertAlmostEqual(q.temperature,1.7);self.assertAlmostEqual(q.unknown_threshold,.63);np.testing.assert_allclose(q.predict_proba(X),m.predict_proba(X))
if __name__=="__main__":unittest.main()
