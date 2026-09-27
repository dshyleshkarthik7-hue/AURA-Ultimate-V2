#!/usr/bin/env python3
import json
from pathlib import Path
import yaml
c=yaml.safe_load(Path("config.yaml").read_text());m=c["model"]
Path("web/model_config.json").write_text(json.dumps({"image_size":m["image_size"],"roi":c["roi"],"labels":c["labels"],"confidence_threshold":m["confidence_threshold"],"margin_threshold":m["margin_threshold"],"feature_length":329},indent=2)+"\n")
