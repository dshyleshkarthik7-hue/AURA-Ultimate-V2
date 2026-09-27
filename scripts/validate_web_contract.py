import json,yaml
from pathlib import Path
c=yaml.safe_load(Path("config.yaml").read_text());w=json.loads(Path("web/model_config.json").read_text())
assert w["image_size"]==c["model"]["image_size"] and w["roi"]==c["roi"] and w["labels"]==c["labels"] and w["confidence_threshold"]==c["model"]["confidence_threshold"] and w["margin_threshold"]==c["model"]["margin_threshold"] and w["feature_length"]==329
print("web contract OK")
