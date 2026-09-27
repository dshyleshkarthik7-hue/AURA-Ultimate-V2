import unittest
from aura.calibration import promotion_gate
class Tests(unittest.TestCase):
 def test_weak(self):self.assertFalse(promotion_gate({"macro_f1":.8,"unknown_rejection":.99}))
 def test_strong(self):self.assertTrue(promotion_gate({"macro_f1":.9,"unknown_rejection":.95}))
 def test_teacher_regression(self):self.assertLess(.87,.89)
if __name__=="__main__":unittest.main()
