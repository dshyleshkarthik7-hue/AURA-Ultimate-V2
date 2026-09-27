
"""Atomic local model promotion with rollback and validation metadata."""
from pathlib import Path
import json,os,shutil,tempfile,time
class ModelRegistry:
    def __init__(self,root="models/registry"):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.manifest=self.root/"manifest.json"
    def _read(self):
        if not self.manifest.exists(): return {"active":None,"history":[]}
        m=json.loads(self.manifest.read_text(encoding="utf-8"))
        if not isinstance(m,dict) or not isinstance(m.get("history"),list): raise ValueError("Invalid registry manifest")
        return m
    def _write(self,m):
        fd,tmp=tempfile.mkstemp(prefix=".manifest-",dir=self.root)
        try:
            with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(m,f,indent=2);f.flush();os.fsync(f.fileno())
            os.replace(tmp,self.manifest)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    def promote(self,candidate,metrics):
        from .model import AuraSoftmax
        candidate=Path(candidate)
        if not candidate.exists():raise FileNotFoundError(candidate)
        model=AuraSoftmax.load(candidate)
        m=self._read();stamp=time.strftime("%Y%m%d-%H%M%S");target=self.root/f"aura_{stamp}_{time.time_ns()%1000000:06d}.npz"
        shutil.copy2(candidate,target)
        previous=m.get("active")
        m["history"].append({"path":str(target),"metrics":metrics,"model_version":model.model_version,"previous":previous,"time":stamp})
        m["active"]=str(target);self._write(m);return target
    def rollback(self):
        m=self._read()
        if len(m["history"])<2:return None
        m["history"].pop();m["active"]=m["history"][-1]["path"];self._write(m);return m["active"]
    def active_path(self):
        p=self._read().get("active");return Path(p) if p else None
