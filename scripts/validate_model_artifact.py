from pathlib import Path
import numpy as np
from aura.model import AuraSoftmax
from aura.config import load_config
cfg=load_config();p=Path(cfg["model"]["path"]);m=AuraSoftmax.load(p)
assert m.W.shape[0]==329 and m.W.shape[1]==len(cfg["labels"])
assert m.labels==list(cfg["labels"])
print("model artifact OK",p,"version",m.model_version,"temperature",m.temperature)
