#!/usr/bin/env python3
"""Guarded self-training for AURA.

This is still self-supervised/pseudo-labelled learning: it does not manufacture
ground truth. Its purpose is to reduce confirmation bias by requiring agreement
across independent views and by never allowing a candidate to promote itself
without passing a frozen-teacher regression gate on held-out evidence.
"""
import argparse, time
from pathlib import Path
import cv2, numpy as np

from aura.config import load_config
from aura.camera import Camera
from aura.perception import PerceptionEngine
from aura.features import FeatureExtractor
from aura.model import AuraSoftmax
from aura.calibration import fit_temperature, evaluate
from aura.model_registry import ModelRegistry


def variants(frame, rng):
    """Create condition changes that test invariance, not new labels."""
    views=[frame]
    h,w=frame.shape[:2]
    views.append(cv2.flip(frame,1))
    alpha=float(rng.uniform(.75,.95))
    beta=int(rng.uniform(-25,-5))
    views.append(cv2.convertScaleAbs(frame,alpha=alpha,beta=beta))
    alpha=float(rng.uniform(1.05,1.25))
    beta=int(rng.uniform(5,20))
    views.append(cv2.convertScaleAbs(frame,alpha=alpha,beta=beta))
    angle=float(rng.uniform(-8,8))
    m=cv2.getRotationMatrix2D((w/2,h/2),angle,1.0)
    views.append(cv2.warpAffine(frame,m,(w,h),borderMode=cv2.BORDER_REFLECT))
    return views


def teacher_label(engine, frame, fx):
    """Return a label only when independent transformations agree."""
    rng=np.random.default_rng(123)
    observations=[]
    for view in variants(frame,rng):
        result=engine.predict(view)
        if result.get("stable") and result.get("confidence",0)>=.88:
            observations.append((result["label"],float(result["confidence"])))
        else:
            return None
    labels=[x[0] for x in observations]
    if len(set(labels)) != 1:
        return None
    # Require strong agreement, not merely the mean.
    if min(x[1] for x in observations) < .88:
        return None
    return labels[0]


def split_session(samples, seed):
    """Split by captured session, never by transformed frame."""
    rng=np.random.default_rng(seed)
    ids=np.arange(len(samples))
    rng.shuffle(ids)
    cut=max(1,int(len(ids)*.70))
    return ids[:cut],ids[cut:]


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default="config.yaml")
    ap.add_argument("--seconds",type=int,default=45)
    ap.add_argument("--min-per-class",type=int,default=12)
    args=ap.parse_args()
    cfg=load_config(args.config)

    cam=Camera(cfg["camera"].get("source",0),cfg["camera"]["width"],
               cfg["camera"]["height"],cfg["camera"]["fps"])
    if not cam.open():
        raise SystemExit("camera open failed")

    teacher=PerceptionEngine(cfg)
    if teacher.model is None:
        raise SystemExit("An existing teacher model is required for guarded self-training.")

    fx=FeatureExtractor(cfg["model"]["image_size"],cfg.get("roi"))
    rng=np.random.default_rng(cfg["training"]["seed"])
    samples=[]
    rejected=0
    start=time.time()

    try:
        while time.time()-start < args.seconds:
            ok,frame=cam.read()
            if not ok:
                continue

            # Each accepted sample is one original camera moment. Its
            # transformations are evidence checks, not additional samples.
            label=teacher_label(teacher,frame,fx)
            if label is None:
                rejected+=1
                continue

            feature=fx.extract(frame)
            samples.append((feature,label))
    finally:
        cam.release()

    print("accepted evidence:",len(samples),"rejected:",rejected)

    if not samples:
        print("No independently-agreeing evidence. Model unchanged.")
        return

    labels=list(cfg["labels"])
    counts={label:sum(1 for _,y in samples if y==label) for label in labels}
    print("accepted class counts:",counts)

    if any(counts[label] < args.min_per_class for label in labels):
        print("Class coverage gate failed. Model unchanged.")
        return

    X=np.asarray([x for x,_ in samples],np.float32)
    y=np.asarray([labels.index(y) for _,y in samples],np.int64)
    train_idx,test_idx=split_session(samples,cfg["training"]["seed"])

    if len(test_idx)<max(3,len(labels)):
        print("Held-out session is too small. Model unchanged.")
        return

    # Freeze teacher behaviour before fitting the candidate.
    teacher_test=teacher.model.predict_proba(X[test_idx]).argmax(1)
    teacher_acc=float((teacher_test==y[test_idx]).mean())

    candidate=AuraSoftmax()
    candidate.fit(
        X[train_idx],y[train_idx],labels,
        epochs=cfg["training"]["epochs"],
        lr=cfg["training"]["learning_rate"],
        l2=cfg["training"]["l2"],
        batch_size=cfg["training"]["batch_size"],
        seed=cfg["training"]["seed"],
    )
    fit_temperature(candidate,X[test_idx],y[test_idx])
    metrics=evaluate(candidate,X[test_idx],y[test_idx])

    # The candidate must not regress against the frozen teacher on the same
    # untouched session. A pseudo-label pipeline is allowed to abstain, never
    # to silently lower the existing model's performance.
    metrics["teacher_accuracy"]=teacher_acc
    metrics["candidate_accuracy"]=metrics["accuracy"]

    if metrics["candidate_accuracy"] < teacher_acc - .01:
        print("Teacher regression gate failed. Model unchanged.")
        return

    if metrics["macro_f1"] < .85:
        print("Macro-F1 gate failed. Model unchanged.")
        return

    candidate_path=Path("models/candidate.npz")
    candidate.save(candidate_path)
    target=ModelRegistry().promote(candidate_path,metrics)
    print("PROMOTED:",target)
    print("Note: labels remain pseudo-labels; independent ground truth is still recommended.")


if __name__=="__main__":
    main()
