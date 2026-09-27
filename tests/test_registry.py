import tempfile,unittest
from pathlib import Path
import numpy as np
from aura.model import AuraSoftmax
from aura.model_registry import ModelRegistry
class RegistryTests(unittest.TestCase):
 def _model(self,path,version):
  m=AuraSoftmax();X=np.vstack([np.zeros((8,3)),np.ones((8,3)),np.full((8,3),2)]).astype(np.float32);y=np.repeat([0,1,2],8)
  m.fit(X,y,["a","b","c"],epochs=4);m.model_version=version;m.save(path)
 def test_promote_and_rollback(self):
  with tempfile.TemporaryDirectory() as d:
   r=ModelRegistry(Path(d)/"registry");a=Path(d)/"a.npz";b=Path(d)/"b.npz";self._model(a,1);self._model(b,2)
   r.promote(a,{"macro_f1":.9});r.promote(b,{"macro_f1":.91})
   self.assertTrue(r.active_path().exists());old=r.rollback();self.assertIsNotNone(old);self.assertEqual(Path(old).read_bytes(),a.read_bytes())
 def test_invalid_artifact_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   r=ModelRegistry(Path(d)/"registry");p=Path(d)/"bad";p.write_bytes(b"not a model")
   with self.assertRaises((ValueError,OSError,KeyError)):r.promote(p,{})
if __name__=="__main__":unittest.main()
