
import unittest, numpy as np, tempfile
from pathlib import Path
from aura.features import FeatureExtractor
from aura.model import AuraSoftmax
from aura.temporal import TemporalConsensus
from aura.i18n import LANGUAGES, object_name
class Regression(unittest.TestCase):
 def test_feature_dim_compatibility(self):
  fx=FeatureExtractor(128,{"mode":"center","width_ratio":.82,"height_ratio":.82})
  self.assertEqual(fx.extract(np.zeros((64,64,3),np.uint8)).shape[0],329)
 def test_model_roundtrip(self):
  rng=np.random.default_rng(1);X=rng.normal(size=(30,4)).astype(np.float32);y=np.array([0]*15+[1]*15)
  m=AuraSoftmax();m.fit(X,y,["a","b"],epochs=20,batch_size=8)
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/"m.npz";m.save(p);m2=AuraSoftmax.load(p)
   np.testing.assert_allclose(m.predict_proba(X),m2.predict_proba(X),atol=1e-6)
 def test_temporal_reject_clears(self):
  t=TemporalConsensus(5)
  for _ in range(4):t.update("a",.9)
  self.assertIsNotNone(t.result(3,.7));t.reject();self.assertIsNone(t.result(3,.7))
 def test_all_languages_have_all_objects(self):
  for lang in LANGUAGES:
   for label in ["steel_glass","steel_water_bottle","bottle_gourd"]:
    self.assertTrue(object_name(label,lang))
if __name__=="__main__":unittest.main()
