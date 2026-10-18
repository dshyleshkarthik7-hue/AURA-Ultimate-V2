import unittest
from aura.context_intelligence import ContextGraph, ObjectTwin, Relation, build_graph, reason_about_scene

class ContextIntelligenceTests(unittest.TestCase):
    def test_unknown_skipped_and_confidence_clamped(self):
        graph = build_graph([{"label": "unknown", "confidence": 1}, {"label": "Laptop", "confidence": 1.7}])
        self.assertEqual(len(graph.objects), 1)
        self.assertEqual(graph.objects[0].confidence, 1.0)
    def test_relation_requires_existing_endpoints(self):
        graph = ContextGraph(objects=[ObjectTwin("a", "Laptop"), ObjectTwin("b", "Monitor")])
        graph.add_relation(Relation("a", "may_connect_to", "b", .5, "demo"))
        with self.assertRaises(ValueError):
            graph.add_relation(Relation("a", "fits", "missing", .5, "demo"))
    def test_compatibility_is_caveated(self):
        result = reason_about_scene([{"label": "Laptop", "confidence": .95}, {"label": "Monitor", "confidence": .9}], "Can I connect this monitor?")
        self.assertEqual(result["intent"], "compatibility")
        self.assertTrue(result["missing_information"])
        self.assertTrue(result["limitations"])
    def test_empty_scene_asks_for_identity(self):
        result = reason_about_scene([], "What is this?")
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("object identity", result["missing_information"])
    def test_prices_marked_illustrative(self):
        result = reason_about_scene([{"label": "Monitor", "confidence": .8}], "Should I buy this?")
        self.assertEqual(result["intent"], "commerce")
        self.assertTrue(result["recommendations"][0]["requires_verification"])

if __name__ == "__main__":
    unittest.main()
