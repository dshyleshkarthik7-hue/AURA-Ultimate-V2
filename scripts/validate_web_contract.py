#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml

REQUIRED_WEB_MARKERS = (
    "featureFromCanvas", "cvReady", "loadNpz", "sceneMask",
    "grabCutBox", "viewEvidence", "excludePerson",
)


def main() -> None:
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    web_config = json.loads((ROOT / "web/model_config.json").read_text(encoding="utf-8"))
    artifact = ROOT / "web/model.b64"
    app = (ROOT / "web/app.js").read_text(encoding="utf-8")
    index = (ROOT / "web/index.html").read_text(encoding="utf-8")

    labels = list(config["labels"])
    assert web_config["image_size"] == config["model"]["image_size"]
    assert web_config["roi"] == config["roi"]
    assert web_config["labels"] == labels
    assert web_config["feature_length"] == 329
    assert web_config["feature_contract"] == "opencv-v1-329"
    assert artifact.exists() and artifact.stat().st_size > 100
    assert artifact.read_text(encoding="utf-8").lstrip().startswith("UEsDB")

    missing = [marker for marker in REQUIRED_WEB_MARKERS if marker not in app]
    assert not missing, f"web perception stages missing: {missing}"
    assert "opencv.js" in index and "fflate" in index
    assert "model.b64" in app
    print("web contract OK: OpenCV feature contract + shipped NPZ artifact + perception stages")


if __name__ == "__main__":
    main()
