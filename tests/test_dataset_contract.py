import tempfile, unittest
from pathlib import Path
from aura.data import validate_dataset
class T(unittest.TestCase):
 def test_contract_rejects_unexpected(self):
  with tempfile.TemporaryDirectory() as x:
   r=Path(x); (r/'a').mkdir(); (r/'b').mkdir(); (r/'old').mkdir();
   for d in ['a','b']:
    for i in range(2): (r/d/f'{i}.jpg').write_bytes(b'x')
   with self.assertRaises(ValueError): validate_dataset(r,['a','b'],2)
if __name__=='__main__': unittest.main()
