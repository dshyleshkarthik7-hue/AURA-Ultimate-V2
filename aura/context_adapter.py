"""Bridge the existing camera PerceptionEngine to AURA's context graph."""
from __future__ import annotations
from typing import Any
from .context_intelligence import reason_about_scene


def reason_from_perception(result: dict[str, Any], question: str = "",
                           constraints: dict[str, Any] | None = None) -> dict[str, Any]:
    """Consume a PerceptionEngine.predict() result without handling image pixels.

    Unknown or unstable predictions remain low-confidence observations; callers should
    avoid presenting them as confirmed objects. This adapter keeps perception and
    relationship reasoning as separate, testable stages.
    """
    label = str(result.get("label") or "unknown")
    confidence = float(result.get("mean_confidence", result.get("confidence", 0.0)) or 0.0)
    stable = bool(result.get("stable", False))
    detection = {
        "id": "aura-primary-detection",
        "label": label if stable else "unknown",
        "confidence": confidence if stable else min(confidence, 0.49),
        "source": "aura_perception_engine",
        "attributes": {
            "stable": stable,
            "colour": result.get("colour"),
            "scene": result.get("scene"),
            "quality": result.get("quality"),
        },
    }
    response = reason_about_scene([detection], question=question, constraints=constraints)
    response["perception"] = {
        "label": label,
        "stable": stable,
        "reason": result.get("reason", "unspecified"),
        "confidence": round(max(0.0, min(1.0, confidence)), 3),
    }
    if not stable:
        response["summary"] = "AURA has not verified a stable object label yet. " + response["summary"]
        response["missing_information"] = list(dict.fromkeys(
            ["a stable, verified object label"] + response["missing_information"]
        ))
    return response
