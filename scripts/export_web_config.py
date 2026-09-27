#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml


def main():
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    model = config["model"]
    payload = {
        "version": 2,
        "artifact": "model.b64",
        "artifact_format": "npz-base64",
        "image_size": model["image_size"],
        "roi": config["roi"],
        "labels": config["labels"],
        "confidence_threshold": model["confidence_threshold"],
        "margin_threshold": model["margin_threshold"],
        "feature_length": 329,
        "feature_contract": "opencv-v1-329",
    }
    target = ROOT / "web/model_config.json"
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("web config exported:", target)


if __name__ == "__main__":
    main()
