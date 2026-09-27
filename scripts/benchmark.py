#!/usr/bin/env python3
"""Measure local feature/model latency for deployment decisions."""
import argparse,time
from pathlib import Path
import cv2,numpy as np
from aura.config import load_config
from aura.features import FeatureExtractor
from aura.model import AuraSoftmax
from aura.data import image_files


def percentile(values,p):
    return float(np.percentile(np.asarray(values,dtype=np.float64),p))


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",default="config.yaml");ap.add_argument("--iterations",type=int,default=100)
    args=ap.parse_args();cfg=load_config(args.config)
    fx=FeatureExtractor(cfg["model"]["image_size"],cfg.get("roi"));model=AuraSoftmax.load(cfg["model"]["path"])
    files=[]
    for label in cfg["labels"]: files.extend(image_files(Path(cfg["dataset"]["root"])/label))
    if not files: raise SystemExit("No benchmark images found")
    frame=cv2.imread(str(files[0]))
    if frame is None: raise SystemExit("Benchmark image unreadable")
    for _ in range(10): model.predict_proba(fx.extract(frame)[None,:])
    feature=[];inference=[]
    for _ in range(args.iterations):
        t=time.perf_counter();x=fx.extract(frame);feature.append((time.perf_counter()-t)*1000)
        t=time.perf_counter();model.predict_proba(x[None,:]);inference.append((time.perf_counter()-t)*1000)
    out={"iterations":args.iterations,"feature_ms":{"p50":percentile(feature,50),"p95":percentile(feature,95)},"inference_ms":{"p50":percentile(inference,50),"p95":percentile(inference,95)},"model_version":model.model_version,"feature_contract":fx.CONTRACT}
    print(out)


if __name__=="__main__":main()
