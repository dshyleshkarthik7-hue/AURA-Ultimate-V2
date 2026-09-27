"""Automated evidence and model-quality orchestration for AURA.

This module provides the deterministic orchestration layer around the existing
offline classifier. It deliberately separates evidence collection, evaluation,
and model promotion so a higher training score cannot silently replace a
previous model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import time
from typing import Iterable


@dataclass
class Observation:
    timestamp: float
    quality: float
    lighting: str
    scene: str
    label: str | None = None
    confidence: float = 0.0


@dataclass
class EvidenceGate:
    required_observations: int = 7
    minimum_quality: float = 0.55
    observations: list[Observation] = field(default_factory=list)

    def add(self, observation: Observation) -> bool:
        if observation.quality >= self.minimum_quality:
            self.observations.append(observation)
        return self.ready

    @property
    def ready(self) -> bool:
        return len(self.observations) >= self.required_observations

    @property
    def mean_quality(self) -> float:
        if not self.observations:
            return 0.0
        return sum(x.quality for x in self.observations) / len(self.observations)

    def summary(self) -> dict:
        return {
            "ready": self.ready,
            "observations": len(self.observations),
            "mean_quality": round(self.mean_quality, 4),
            "lighting": sorted({x.lighting for x in self.observations}),
            "scenes": sorted({x.scene for x in self.observations}),
        }


@dataclass
class EvaluationGate:
    """Conservative promotion gate for automatically trained models."""

    min_macro_f1: float = 0.85
    min_unknown_rejection: float = 0.90
    max_regression: float = 0.02

    def accepts(
        self,
        macro_f1: float,
        unknown_rejection: float,
        previous_macro_f1: float | None = None,
    ) -> bool:
        if macro_f1 < self.min_macro_f1:
            return False
        if unknown_rejection < self.min_unknown_rejection:
            return False
        if previous_macro_f1 is not None and macro_f1 < previous_macro_f1 - self.max_regression:
            return False
        return True


class SessionRecorder:
    """Persist session metadata without treating frames as independent sessions."""

    def __init__(self, root: str | Path = "runs") -> None:
        self.root = Path(root)

    def save(self, session_id: str, gate: EvidenceGate) -> Path:
        destination = self.root / session_id
        destination.mkdir(parents=True, exist_ok=True)
        output = destination / "evidence.json"
        output.write_text(
            json.dumps(
                {
                    "session_id": session_id,
                    "created_at": time.time(),
                    "summary": gate.summary(),
                    "observations": [o.__dict__ for o in gate.observations],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return output


def build_session(
    observations: Iterable[Observation],
    required_observations: int = 7,
) -> EvidenceGate:
    gate = EvidenceGate(required_observations=required_observations)
    for observation in observations:
        gate.add(observation)
    return gate
