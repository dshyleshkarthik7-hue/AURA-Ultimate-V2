#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import yaml
c=yaml.safe_load((ROOT/"config.yaml").read_text(encoding="utf-8"));m=c["model"]
(ROOT/"web/model_config.json").write_text(json.dumps({"version":2,"artifact":"model.b64","artifact_format":"npz-base64","image_size":m["image_size"],"roi":c["roi"],"labels":c["labels"],"confidence_threshold":m["confidence_threshold"],"margin_threshold":m["margin_threshold"],"feature_length":329,"feature_contract":"opencv-v1-329"},indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
