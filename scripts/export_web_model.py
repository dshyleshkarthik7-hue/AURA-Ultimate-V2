#!/usr/bin/env python3
import json
from pathlib import Path
import numpy as np
from aura.model import AuraSoftmax
from aura.config import load_config
cfg=load_config();m=AuraSoftmax.load(cfg["model"]["path"])
out={"W":m.W.tolist(),"b":m.b.tolist(),"mean":m.mean.tolist(),"std":m.std.tolist(),"labels":m.labels,"temperature":m.temperature,"unknown_threshold":m.unknown_threshold,"model_version":m.model_version}
Path("web/model.json").write_text(json.dumps(out,separators=(",",":")),encoding="utf-8")
print("wrote web/model.json")
