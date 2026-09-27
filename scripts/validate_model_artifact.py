#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aura.model import AuraSoftmax
from aura.config import load_config
cfg=load_config(ROOT/"config.yaml");p=ROOT/cfg["model"]["path"];m=AuraSoftmax.load(p)
assert m.W.shape[0]==329 and m.W.shape[1]==len(cfg["labels"]);assert m.labels==list(cfg["labels"]);print("model artifact OK",p,"version",m.model_version,"temperature",m.temperature)
