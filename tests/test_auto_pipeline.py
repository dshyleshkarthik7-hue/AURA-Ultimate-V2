from aura.auto_pipeline import EvaluationGate, EvidenceGate, Observation


def test_evidence_gate_waits_for_quality_observations():
    gate = EvidenceGate(required_observations=2, minimum_quality=0.6)
    assert not gate.add(Observation(0, 0.5, "dim", "busy"))
    assert not gate.ready
    assert gate.add(Observation(1, 0.8, "daylight", "clear"))
    assert not gate.ready
    assert gate.add(Observation(2, 0.9, "daylight", "clear"))
    assert gate.ready
    assert gate.mean_quality == 0.85


def test_evaluation_gate_rejects_regression_and_weak_unknown_rejection():
    gate = EvaluationGate(min_macro_f1=0.85, min_unknown_rejection=0.9, max_regression=0.02)
    assert gate.accepts(0.9, 0.95, previous_macro_f1=0.89)
    assert not gate.accepts(0.84, 0.99)
    assert not gate.accepts(0.9, 0.89)
    assert not gate.accepts(0.86, 0.95, previous_macro_f1=0.90)
