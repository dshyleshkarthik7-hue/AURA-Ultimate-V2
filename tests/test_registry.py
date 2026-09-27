import tempfile,unittest
from pathlib import Path
from aura.model_registry import ModelRegistry
class RegistryTests(unittest.TestCase):
 def test_promote_and_rollback(self):
  with tempfile.TemporaryDirectory() as d:
   r=ModelRegistry(Path(d)/'registry');a=Path(d)/'a';a.write_bytes(b'a');b=Path(d)/'b';b.write_bytes(b'b');r.promote(a,{'macro_f1':.9});r.promote(b,{'macro_f1':.91});self.assertTrue(r.active_path().exists());old=r.rollback();self.assertIsNotNone(old);self.assertEqual(Path(old).read_bytes(),b'a')
if __name__=="__main__":unittest.main()
