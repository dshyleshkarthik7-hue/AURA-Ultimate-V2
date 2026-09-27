import unittest
from aura.auto_pipeline import EvaluationGate,EvidenceGate,Observation
class Tests(unittest.TestCase):
 def test_evidence_gate(self):
  g=EvidenceGate(required_observations=2,minimum_quality=.6);self.assertFalse(g.add(Observation(0,.5,"dim","busy")));self.assertFalse(g.add(Observation(1,.8,"daylight","clear")));self.assertTrue(g.add(Observation(2,.9,"daylight","clear")));self.assertAlmostEqual(g.mean_quality,.85)
 def test_gate(self):
  g=EvaluationGate(min_macro_f1=.85,min_unknown_rejection=.9,max_regression=.02);self.assertTrue(g.accepts(.9,.95,previous_macro_f1=.89));self.assertFalse(g.accepts(.84,.99));self.assertFalse(g.accepts(.9,.89));self.assertFalse(g.accepts(.86,.95,previous_macro_f1=.90))
if __name__=="__main__":unittest.main()
