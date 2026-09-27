#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml


REQUIRED_WEB_MARKERS = (
    "featureFromCanvas",
    "sceneMask",
    "captureView",
    "excludePerson",
    "unknown_threshold",
)


def main() -> None:
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    web_config = json.loads((ROOT / "web/model_config.json").read_text(encoding="utf-8"))
    model = json.loads((ROOT / "web/model.json").read_text(encoding="utf-8"))
    app = (ROOT / "web/app.js").read_text(encoding="utf-8")

    labels = list(config["labels"])
    assert web_config["image_size"] == config["model"]["image_size"]
    assert web_config["roi"] == config["roi"]
    assert web_config["labels"] == labels
    assert web_config["feature_length"] == 329

    feature_length = int(model["feature_length"])
    classes = int(model["classes"])
    assert feature_length == 329
    assert len(model["labels"]) == classes == len(labels)
    assert len(model["W"]) == feature_length
    assert all(len(row) == classes for row in model["W"])
    assert len(model["b"]) == classes
    assert len(model["mean"]) == feature_length
    assert len(model["std"]) == feature_length
    assert all(float(value) > 0 for value in model["std"])
    assert float(model["temperature"]) > 0
    threshold = float(model["unknown_threshold"])
    assert 0 < threshold < 1
    assert model["labels"] == labels

    missing = [marker for marker in REQUIRED_WEB_MARKERS if marker not in app]
    assert not missing, f"web perception stages missing: {missing}"
    print("web contract OK: model + config + perception stages")


if __name__ == "__main__":
    main()
