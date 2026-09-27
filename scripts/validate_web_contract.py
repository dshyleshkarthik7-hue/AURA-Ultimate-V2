#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml


def main() -> None:
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    web_config = json.loads((ROOT / "web/model_config.json").read_text(encoding="utf-8"))
    model = json.loads((ROOT / "web/model.json").read_text(encoding="utf-8"))

    labels = list(config["labels"])
    assert web_config["image_size"] == config["model"]["image_size"]
    assert web_config["roi"] == config["roi"]
    assert web_config["labels"] == labels

    feature_length = int(model["feature_length"])
    classes = int(model["classes"])
    assert web_config["feature_length"] == feature_length == 329
    assert len(model["labels"]) == classes == len(labels)

    weights = model["W"]
    assert len(weights) == feature_length
    assert all(len(row) == classes for row in weights)

    assert len(model["b"]) == classes
    assert len(model["mean"]) == feature_length
    assert len(model["std"]) == feature_length
    assert all(float(value) > 0 for value in model["std"])

    assert float(model["temperature"]) > 0
    threshold = float(model["unknown_threshold"])
    assert 0 < threshold < 1
    assert model["labels"] == labels

    print("web contract OK")


if __name__ == "__main__":
    main()
