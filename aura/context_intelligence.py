"""AURA Context Intelligence: transparent, conservative scene reasoning."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Optional
import re

@dataclass(frozen=True)
class ObjectTwin:
    id: str
    label: str
    confidence: float = 1.0
    attributes: dict[str, Any] = field(default_factory=dict)
    source: str = "perception"

@dataclass(frozen=True)
class Relation:
    subject: str
    predicate: str
    object: str
    confidence: float
    evidence: str
    status: str = "inferred"

@dataclass
class ContextGraph:
    objects: list[ObjectTwin] = field(default_factory=list)
    relations: list[Relation] = field(default_factory=list)
    def add_object(self, obj: ObjectTwin) -> None:
        if not any(item.id == obj.id for item in self.objects):
            self.objects.append(obj)
    def add_relation(self, relation: Relation) -> None:
        known = {item.id for item in self.objects}
        if relation.subject not in known or relation.object not in known:
            raise ValueError("Relation endpoints must exist in the graph")
        if relation.subject == relation.object:
            raise ValueError("A relation cannot connect an object to itself")
        if not 0 <= relation.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self.relations.append(relation)
    def to_dict(self) -> dict[str, Any]:
        return {"objects": [asdict(x) for x in self.objects], "relations": [asdict(x) for x in self.relations]}

CATALOG = {
    "monitor": {"ports": ["HDMI", "DisplayPort"], "price_usd": 119.00},
    "laptop": {"ports": ["USB-C", "HDMI"], "price_usd": 499.00},
    "usb-c hub": {"ports": ["USB-C", "HDMI", "USB-A"], "price_usd": 24.00},
    "hdmi cable": {"ports": ["HDMI"], "price_usd": 9.00},
    "desk": {"dimensions_cm": {"width": 120, "depth": 60}, "price_usd": 89.00},
    "curtain": {"price_usd": 25.00},
}
def normalize_label(label: str) -> str:
    return re.sub(r"\s+", " ", label.strip().lower().replace("_", " "))

def build_graph(detections: Iterable[dict[str, Any]]) -> ContextGraph:
    """Accept perception-like dictionaries; never store image data."""
    graph = ContextGraph()
    for index, detection in enumerate(detections):
        label = str(detection.get("label", "")).strip()
        if not label or normalize_label(label) == "unknown":
            continue
        confidence = min(1.0, max(0.0, float(detection.get("confidence", 0.0))))
        graph.add_object(ObjectTwin(str(detection.get("id") or f"object-{index + 1}"), label,
                                    confidence, dict(detection.get("attributes") or {}),
                                    str(detection.get("source") or "perception")))
    return graph

def reason_about_scene(detections: Iterable[dict[str, Any]], question: str = "",
                       constraints: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Build a small context graph and conservative recommendations."""
    constraints = dict(constraints or {})
    graph = build_graph(detections)
    labels = [normalize_label(x.label) for x in graph.objects]
    q = normalize_label(question)
    observations, missing, recommendations = [], [], []
    intent = "understand_scene"
    if not graph.objects:
        return {"intent": intent, "summary": "I couldn't identify a usable object label yet. Try a clearer view or enter the object name.",
                "graph": graph.to_dict(), "observations": [], "missing_information": ["object identity"],
                "recommendations": [], "confidence": 0.0,
                "limitations": ["No reliable object labels were supplied to the context engine."]}
    if any(word in q for word in ("connect", "plug", "port", "monitor", "display")):
        intent = "compatibility"
        laptop = next((x for x in graph.objects if normalize_label(x.label) == "laptop"), None)
        monitor = next((x for x in graph.objects if normalize_label(x.label) == "monitor"), None)
        if laptop and monitor:
            a, b = CATALOG.get("laptop"), CATALOG.get("monitor")
            shared = sorted(set(a["ports"]) & set(b["ports"]))
            observations.append("The demo catalogue lists a shared connection type: " + ", ".join(shared) + ".")
            graph.add_relation(Relation(laptop.id, "may_connect_to", monitor.id, 0.65,
                                        "Generic demo catalogue; verify the actual device models."))
            missing.append("Exact laptop and monitor model numbers and available ports")
        else:
            observations.append("I can't confirm compatibility from the current object labels alone.")
            missing.append("A labelled laptop and monitor plus exact model/port specifications")
        if "usb-c hub" in labels:
            recommendations.append({"item": "USB-C hub", "reason": "May bridge port differences if the laptop supports video output over USB-C.", "requires_verification": True})
    elif any(word in q for word in ("fit", "room", "width", "measure", "curtain", "desk", "space")):
        intent = "fit_and_space"
        if constraints.get("measurements_cm"):
            observations.append("User-provided measurements are available; compare them with verified product dimensions.")
        else:
            observations.append("A camera view alone cannot reliably establish exact physical dimensions.")
            missing.append("Room/opening measurements and the candidate product's verified dimensions")
        if "curtain" in labels:
            recommendations.append({"item": "Measure window width and drop", "reason": "Sizing depends on mounting style and desired fullness.", "requires_verification": True})
        if "desk" in labels:
            recommendations.append({"item": "Measure available floor area", "reason": "Check width, depth, clearance, and access.", "requires_verification": True})
    elif any(word in q for word in ("buy", "purchase", "price", "order", "shop")):
        intent = "commerce"
        observations.append("Consider purchase only after the item and requirements are confirmed.")
        missing.append("Confirmed item, budget, currency, and explicit approval before checkout")
        for obj in graph.objects:
            item = CATALOG.get(normalize_label(obj.label))
            if item and "price_usd" in item:
                recommendations.append({"item": obj.label, "price_usd": item["price_usd"],
                                         "reason": "Illustrative demo price, not a live offer.", "requires_verification": True})
    else:
        observations.append("I found " + ", ".join(x.label for x in graph.objects) + ".")
        uncertain = [x.label for x in graph.objects if x.confidence < .65]
        if uncertain:
            observations.append("Please verify uncertain labels: " + ", ".join(uncertain) + ".")
    confidence = sum(x.confidence for x in graph.objects) / len(graph.objects)
    return {"intent": intent, "summary": " ".join(observations), "graph": graph.to_dict(),
            "observations": observations, "missing_information": missing, "recommendations": recommendations,
            "confidence": round(confidence, 3),
            "limitations": ["Relations are hypotheses, not physical measurements or safety certifications.",
                            "Demo catalogue data is illustrative; verify exact product specifications."]}
