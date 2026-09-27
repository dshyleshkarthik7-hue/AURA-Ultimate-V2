import unittest
import numpy as np
from aura.calibration import evaluate,promotion_gate
from aura.model import AuraSoftmax
class CalibrationTests(unittest.TestCase):
 def test_unknown_is_required_for_promotion(self):
  m=AuraSoftmax();X=np.eye(3,dtype=np.float32);m.fit(X,[0,1,2],['a','b','c'],epochs=3);metrics=evaluate(m,X,np.array([0,1,2]));self.assertIsNone(metrics['unknown_rejection']);self.assertFalse(promotion_gate(metrics))
 def test_unknown_rejection_is_measured(self):
  m=AuraSoftmax();X=np.eye(3,dtype=np.float32);m.fit(X,[0,1,2],['a','b','c'],epochs=3);u=np.ones((2,3),np.float32)*.1;self.assertIsNotNone(evaluate(m,X,np.array([0,1,2]),u)['unknown_rejection'])
if __name__=="__main__":unittest.main()
