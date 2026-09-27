import json,yaml
from pathlib import Path
c=yaml.safe_load(Path("config.yaml").read_text());w=json.loads(Path("web/model_config.json").read_text());m=json.loads(Path("web/model.json").read_text())
assert w["image_size"]==c["model"]["image_size"] and w["roi"]==c["roi"] and w["labels"]==c["labels"] and w["feature_length"]==m["feature_length"]
assert len(m["labels"])==m["classes"] and len(m["W"])==m["feature_length"] and len(m["W"][0])==m["classes"] and len(m["mean"])==m["feature_length"] and len(m["std"])==m["feature_length"]
assert m["temperature"]>0 and 0<m["unknown_threshold"]<1
print("web contract OK")
