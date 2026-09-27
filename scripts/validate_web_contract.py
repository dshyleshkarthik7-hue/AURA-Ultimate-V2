#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import json,yaml
c=yaml.safe_load((ROOT/"config.yaml").read_text(encoding="utf-8"));w=json.loads((ROOT/"web/model_config.json").read_text());m=json.loads((ROOT/"web/model.json").read_text())
assert w["image_size"]==c["model"]["image_size"] and w["roi"]==c["roi"] and w["labels"]==c["labels"]
assert w["feature_length"]==m["feature_length"]==329
assert len(m["labels"])==m["classes"]==len(c["labels"]);assert len(m["W"])==m["feature_length"] and all(len(row)==m["classes"] for row in m["W"]);assert len(m["b"])==m["classes"] and len(m["mean"])==m["feature_length"] and len(m["std"])==m["feature_length"]);assert all(x>0 for x in m["std"]) and m["temperature"]>0 and 0<m["unknown_threshold"]<1;assert m["labels"]==c["labels"];print("web contract OK")
