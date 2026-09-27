"""Atomic local model promotion with rollback and validation metadata."""
from pathlib import Path
import json,shutil,time
class ModelRegistry:
 def __init__(self,root="models/registry"):
  self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.manifest=self.root/"manifest.json"
 def _read(self):
  return json.loads(self.manifest.read_text()) if self.manifest.exists() else {"active":None,"history":[]}
 def promote(self,candidate,metrics):
  m=self._read();candidate=Path(candidate)
  if not candidate.exists():raise FileNotFoundError(candidate)
  stamp=time.strftime("%Y%m%d-%H%M%S");target=self.root/f"aura_{stamp}_{time.time_ns()%1000000:06d}.npz";shutil.copy2(candidate,target)
  previous=m.get("active");m["history"].append({"path":str(target),"metrics":metrics,"previous":previous,"time":stamp});m["active"]=str(target);self.manifest.write_text(json.dumps(m,indent=2));return target
 def rollback(self):
  m=self._read()
  if len(m["history"])<2:return None
  m["history"].pop();m["active"]=m["history"][-1]["path"];self.manifest.write_text(json.dumps(m,indent=2));return m["active"]
 def active_path(self):
  m=self._read();p=m.get("active");return Path(p) if p else None
