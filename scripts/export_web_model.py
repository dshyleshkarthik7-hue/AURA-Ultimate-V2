#!/usr/bin/env python3
import json
from pathlib import Path
from aura.model import AuraSoftmax
from aura.config import load_config
cfg=load_config();m=AuraSoftmax.load(cfg["model"]["path"])
out={"version":1,"feature_length":int(m.W.shape[0]),"classes":len(m.labels),"W":m.W.tolist(),"b":m.b.tolist(),"mean":m.mean.tolist(),"std":m.std.tolist(),"labels":m.labels,"temperature":float(m.temperature),"unknown_threshold":float(m.unknown_threshold),"model_version":int(m.model_version)}
Path("web/model.json").write_text(json.dumps(out,separators=(",",":")),encoding="utf-8")
print("wrote web/model.json")
