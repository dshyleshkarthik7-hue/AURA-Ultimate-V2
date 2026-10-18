import unittest
from aura.context_adapter import reason_from_perception

class ContextAdapterTests(unittest.TestCase):
    def test_unstable_detection_is_not_promoted_to_object(self):
        result = reason_from_perception({"label": "steel_glass", "confidence": .9, "stable": False, "reason": "collecting_evidence"}, "What is this?")
        self.assertIn("not verified", result["summary"])
        self.assertIn("a stable, verified object label", result["missing_information"])
        self.assertEqual(result["graph"]["objects"], [])
    def test_stable_detection_is_carried_into_graph(self):
        result = reason_from_perception({"label": "steel_glass", "mean_confidence": .88, "stable": True, "colour": "silver"}, "Describe this")
        self.assertEqual(result["graph"]["objects"][0]["label"], "steel_glass")
        self.assertEqual(result["perception"]["stable"], True)

if __name__ == "__main__":
    unittest.main()
