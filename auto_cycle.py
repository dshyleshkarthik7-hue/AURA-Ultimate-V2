#!/usr/bin/env python3
"""Guarded pseudo-label self-training with isolated train/calibration/test gates."""
import argparse,time
from pathlib import Path
import cv2,numpy as np
from aura.config import load_config
from aura.camera import Camera
from aura.perception import PerceptionEngine
from aura.features import FeatureExtractor
from aura.model import AuraSoftmax
from aura.calibration import fit_temperature,fit_unknown_threshold,evaluate,promotion_gate
from aura.model_registry import ModelRegistry
from aura.data import image_files

def variants(frame,rng):
    h,w=frame.shape[:2]
    views=[frame,cv2.flip(frame,1)]
    for alpha,beta in [(float(rng.uniform(.75,.95)),int(rng.uniform(-25,-5))),
                       (float(rng.uniform(1.05,1.25)),int(rng.uniform(5,20)))]:
        views.append(cv2.convertScaleAbs(frame,alpha=alpha,beta=beta))
    m=cv2.getRotationMatrix2D((w/2,h/2),float(rng.uniform(-8,8)),1.0)
    views.append(cv2.warpAffine(frame,m,(w,h),borderMode=cv2.BORDER_REFLECT))
    return views

def teacher_label(engine,frame):
    obs=[]
    for view in variants(frame,np.random.default_rng(123)):
        r=engine.predict(view)
        if not r.get("stable") or r.get("confidence",0)<.88:return None
        obs.append((r["label"],float(r["confidence"])))
    return obs[0][0] if obs and len({x[0] for x in obs})==1 else None

def stratified_three_way(y,rng):
    train=[];cal=[];test=[]
    for c in np.unique(y):
        idx=np.where(y==c)[0];rng.shuffle(idx);n=len(idx)
        nt=max(1,int(round(n*.20)));nc=max(1,int(round(n*.20)))
        if nt+nc>=n: raise ValueError("Not enough pseudo-labelled samples per class for isolated train/calibration/test")
        test.extend(idx[:nt]);cal.extend(idx[nt:nt+nc]);train.extend(idx[nt+nc:])
    return np.asarray(train),np.asarray(cal),np.asarray(test)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default="config.yaml");ap.add_argument("--seconds",type=int,default=45)
    ap.add_argument("--min-per-class",type=int,default=12);args=ap.parse_args()
    cfg=load_config(args.config);unknown=image_files(Path(cfg["dataset"]["root"])/"unknown")
    if len(unknown)<int(cfg["training"].get("unknown_min_samples",10)):
        raise SystemExit("Independent unknown-object set is required before promotion.")
    cam=Camera(cfg["camera"].get("source",0),cfg["camera"]["width"],cfg["camera"]["height"],cfg["camera"]["fps"])
    if not cam.open():raise SystemExit("camera open failed")
    teacher=PerceptionEngine(cfg)
    if teacher.model is None:raise SystemExit("existing teacher model required")
    fx=FeatureExtractor(cfg["model"]["image_size"],cfg.get("roi"));samples=[];start=time.time()
    try:
        while time.time()-start<args.seconds:
            ok,frame=cam.read()
            if not ok:continue
            label=teacher_label(teacher,frame)
            if label is not None:samples.append((fx.extract(frame),label))
    finally:cam.release()
    labels=list(cfg["labels"]);counts={l:sum(1 for _,y in samples if y==l) for l in labels}
    if not samples or any(counts[l]<args.min_per_class for l in labels):
        print("coverage gate failed; model unchanged");return
    X=np.asarray([x for x,_ in samples],np.float32)
    y=np.asarray([labels.index(y) for _,y in samples],np.int64)
    rng=np.random.default_rng(cfg["training"]["seed"]);tr,cal,te=stratified_three_way(y,rng)
    fxu=FeatureExtractor(cfg["model"]["image_size"],cfg.get("roi"));ux=[]
    for f in unknown:
        im=cv2.imread(str(f))
        if im is not None:ux.append(fxu.extract(im))
    ux=np.asarray(ux,np.float32)
    candidate=AuraSoftmax()
    candidate.fit(X[tr],y[tr],labels,epochs=cfg["training"]["epochs"],lr=cfg["training"]["learning_rate"],
                  l2=cfg["training"]["l2"],batch_size=cfg["training"]["batch_size"],seed=cfg["training"]["seed"],
                  class_weight=cfg["training"].get("class_balance","balanced"))
    fit_temperature(candidate,X[cal],y[cal])
    fit_unknown_threshold(candidate,X[cal],ux)
    metrics=evaluate(candidate,X[te],y[te],ux)
    teacher_pred=teacher.model.predict_proba(X[te]).argmax(1)
    metrics["teacher_accuracy"]=float((teacher_pred==y[te]).mean())
    if metrics["accuracy"]<metrics["teacher_accuracy"]-.01 or not promotion_gate(metrics):
        print("promotion gate failed; model unchanged");return
    candidate.model_version=max(int(getattr(teacher.model,"model_version",0))+1,6)
    candidate_path=Path("models/candidate.npz");candidate.save(candidate_path)
    print("PROMOTED:",ModelRegistry().promote(candidate_path,metrics))
if __name__=="__main__":main()
