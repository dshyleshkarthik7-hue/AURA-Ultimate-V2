
from pathlib import Path
import numpy as np
from .features import FeatureExtractor
from .model import AuraSoftmax
from .quality import assess
from .temporal import TemporalConsensus

class PerceptionEngine:
    def __init__(self,cfg):
        self.cfg=cfg
        self.fx=FeatureExtractor(cfg["model"]["image_size"],cfg.get("roi"))
        p=Path(cfg["model"]["path"]); self.model=AuraSoftmax.load(p) if p.exists() else None
        if self.model is not None and self.model.W.shape[0] != len(self.fx.extract(np.zeros((32,32,3),np.uint8))):
            raise ValueError("Model and feature extractor are incompatible. Retrain the model.")
        self.temporal=TemporalConsensus(cfg["stability"]["window"])
    def _unknown(self,reason,q,confidence=0.0):
        return {"label":"unknown","raw_label":None,"confidence":float(confidence),"stable":False,"reason":reason,"quality":q}
    def predict(self,frame):
        q=assess(frame,self.cfg)
        if not q["ok"]: self.temporal.reject(); return self._unknown(q["reason"],q)
        if self.model is None: self.temporal.reject(); return self._unknown("model_not_trained",q)
        f=self.fx.extract(frame); probs=self.model.predict_proba(f[None,:])[0]
        order=np.argsort(probs)[::-1]
        if len(order)<2:return self._unknown("invalid_model",q)
        top,second=map(int,order[:2]); conf=float(probs[top]); margin=float(probs[top]-probs[second])
        if conf<self.cfg["model"]["confidence_threshold"] or margin<self.cfg["model"]["margin_threshold"]:
            self.temporal.reject(); return self._unknown("uncertain",q,conf)
        raw=self.model.labels[top]; self.temporal.update(raw,conf)
        stable=self.temporal.result(self.cfg["stability"]["min_votes"],self.cfg["stability"]["min_mean_confidence"])
        if stable is None:return {"label":"unknown","raw_label":raw,"confidence":conf,"stable":False,"reason":"collecting_evidence","quality":q}
        label,mean,votes=stable
        return {"label":label,"raw_label":raw,"confidence":conf,"stable":True,"reason":"verified","quality":q,"votes":votes,"mean_confidence":mean}
