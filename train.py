#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import cv2,numpy as np
from aura.config import load_config
from aura.data import validate_dataset
from aura.features import FeatureExtractor
from aura.model import AuraSoftmax
from aura.augmentation import augment
from aura.calibration import fit_temperature

def split_indices(y,k,val_frac,test_frac,rng):
 tr=[];va=[];te=[]
 for c in range(k):
  a=np.where(y==c)[0];rng.shuffle(a);n=len(a)
  nt=max(1,int(round(n*test_frac)));nv=max(1,int(round(n*val_frac)))
  if nt+nv>=n:raise ValueError(f"Class {c} has too few images for train/validation/test")
  te+=a[:nt].tolist();va+=a[nt:nt+nv].tolist();tr+=a[nt+nv:].tolist()
 rng.shuffle(tr);rng.shuffle(va);rng.shuffle(te)
 return tuple(np.asarray(z,dtype=np.int64) for z in (tr,va,te))

def write_manifest(root,labels,files_by):
 (root/"MANIFEST.csv").write_text("label,original_files\n"+"\n".join(f"{l},{len(files_by[l])}" for l in labels)+"\n",encoding="utf-8")

def main():
 p=argparse.ArgumentParser();p.add_argument("--config",default="config.yaml");a=p.parse_args();cfg=load_config(a.config)
 root=Path(cfg["dataset"]["root"]);labels=list(cfg["labels"]);files_by=validate_dataset(root,labels,cfg["training"]["min_images_per_class"]);write_manifest(root,labels,files_by)
 fx=FeatureExtractor(cfg["model"]["image_size"],cfg.get("roi"));X=[];y=[];paths=[];failures=[]
 for ci,label in enumerate(labels):
  for f in files_by[label]:
   im=cv2.imread(str(f))
   if im is None:failures.append(str(f));continue
   try:X.append(fx.extract(im));y.append(ci);paths.append(str(f))
   except Exception as e:failures.append(f"{f}: {e}")
 if failures:Path("feature_failures.log").write_text("\n".join(failures),encoding="utf-8")
 if failures and len(failures)>max(5,int(.02*(len(paths)+len(failures)))):raise SystemExit("Too many feature failures")
 X=np.asarray(X,np.float32);y=np.asarray(y,np.int64);rng=np.random.default_rng(cfg["training"]["seed"])
 tr,va,te=split_indices(y,len(labels),cfg["training"]["validation_fraction"],cfg["training"]["test_fraction"],rng)
 Xtr=X[tr];ytr=y[tr];extra=[];extra_y=[];arng=np.random.default_rng(cfg["training"]["seed"]+1)
 for i in tr:
  im=cv2.imread(paths[i])
  if im is not None:
   try:extra.append(fx.extract(augment(im,arng)));extra_y.append(y[i])
   except Exception:pass
 if extra:Xtr=np.vstack([Xtr,np.asarray(extra,np.float32)]);ytr=np.concatenate([ytr,np.asarray(extra_y,np.int64)])
 model=AuraSoftmax();model.fit(Xtr,ytr,labels,epochs=cfg["training"]["epochs"],lr=cfg["training"]["learning_rate"],l2=cfg["training"]["l2"],batch_size=cfg["training"]["batch_size"],seed=cfg["training"]["seed"],class_weight=cfg["training"].get("class_balance","balanced"))
 if cfg["training"].get("calibration_temperature",True):fit_temperature(model,X[va],y[va])
 model.save(cfg["model"]["path"])
 Path("splits.json").write_text(json.dumps({"train":[paths[i] for i in tr],"validation":[paths[i] for i in va],"test":[paths[i] for i in te]},indent=2),encoding="utf-8")
 print("saved",cfg["model"]["path"],"temperature",model.temperature,"train/val/test",len(tr),len(va),len(te))
if __name__=="__main__":main()
