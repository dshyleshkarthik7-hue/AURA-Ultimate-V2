#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import cv2,numpy as np
from aura.config import load_config
from aura.features import FeatureExtractor
from aura.model import AuraSoftmax
from aura.data import image_files
from aura.calibration import evaluate as evaluate_metrics

def bootstrap(y,p,seed,n=2000):
    if len(y)<2:return [None,None]
    rng=np.random.default_rng(seed);v=[]
    for _ in range(n):
        i=rng.integers(0,len(y),len(y));v.append(float((p[i]==y[i]).mean()))
    return [float(np.quantile(v,.025)),float(np.quantile(v,.975))]

def main():
    p=argparse.ArgumentParser();p.add_argument("--config",default="config.yaml");p.add_argument("--dataset");p.add_argument("--unknown",default="dataset/unknown");a=p.parse_args();cfg=load_config(a.config);m=AuraSoftmax.load(cfg["model"]["path"]);fx=FeatureExtractor(cfg["model"]["image_size"],cfg.get("roi"));labels=m.labels
    if a.dataset:items=[(f,i) for i,l in enumerate(labels) for f in image_files(Path(a.dataset)/l)]
    else:
        sp=json.loads(Path("splits.json").read_text(encoding="utf-8"));sets={k:set(v) for k,v in sp.items()}
        if sets["train"]&sets["validation"] or sets["train"]&sets["test"] or sets["validation"]&sets["test"]:raise SystemExit("Split integrity failure: overlapping paths")
        items=[(Path(x),i) for i,l in enumerate(labels) for x in sp["test"] if Path(x).parent.name==l]
    X=[];y=[];conf=[]
    for f,t in items:
        im=cv2.imread(str(f))
        if im is None:continue
        X.append(fx.extract(im));y.append(t)
    if not y:raise SystemExit("No readable evaluation samples")
    y=np.asarray(y,np.int64);X=np.asarray(X,np.float32);probs=m.predict_proba(X);pred=probs.argmax(1);conf=probs.max(1)
    unknown_files=image_files(Path(a.unknown)) if Path(a.unknown).exists() else [];unknown_X=[]
    for f in unknown_files:
        im=cv2.imread(str(f))
        if im is not None:unknown_X.append(fx.extract(im))
    unknown_X=np.asarray(unknown_X,np.float32) if unknown_X else None
    metrics=evaluate_metrics(m,X,y,unknown_X);cm=np.zeros((len(labels),len(labels)),int)
    for t,pred_i in zip(y,pred):cm[t,pred_i]+=1
    out={**metrics,"labels":labels,"samples":len(y),"confusion_matrix":cm.tolist(),"accuracy_ci95":bootstrap(y,pred,cfg["training"]["seed"]),"mean_confidence":float(conf.mean()),"unknown_samples":len(unknown_files),"model_version":m.model_version,"temperature":m.temperature,"unknown_threshold":m.unknown_threshold}
    Path("evaluation.json").write_text(json.dumps(out,indent=2),encoding="utf-8");print(json.dumps(out,indent=2))
if __name__=="__main__":main()
