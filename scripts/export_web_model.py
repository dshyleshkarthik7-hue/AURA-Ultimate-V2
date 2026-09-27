#!/usr/bin/env python3
import base64,json,tempfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from aura.model import AuraSoftmax
from aura.config import load_config
def main():
 cfg=load_config(ROOT/"config.yaml");model=AuraSoftmax.load(ROOT/cfg["model"]["path"])
 with tempfile.NamedTemporaryFile(suffix=".npz",delete=False) as f: tmp=Path(f.name)
 try:model.save(tmp);artifact=base64.b64encode(tmp.read_bytes()).decode("ascii")
 finally:tmp.unlink(missing_ok=True)
 (ROOT/"web/model.b64").write_text(artifact+"\n",encoding="utf-8")
 (ROOT/"web/model_export.json").write_text(json.dumps({"version":2,"artifact_format":"npz-base64","feature_contract":"opencv-v1-329","feature_length":int(model.W.shape[0]),"labels":model.labels,"model_version":int(model.model_version),"temperature":float(model.temperature),"unknown_threshold":float(model.unknown_threshold)},indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
