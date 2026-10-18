from pathlib import Path
import numpy as np
from .features import FeatureExtractor
from .model import AuraSoftmax
from .quality import assess
from .temporal import TemporalConsensus
from .scene import analyse_scene, dominant_colour, environment
class PerceptionEngine:
    def __init__(self,cfg):
        self.cfg=cfg;self.fx=FeatureExtractor(cfg["model"]["image_size"],cfg.get("roi"))
        from .model_registry import ModelRegistry
        active=ModelRegistry().active_path()
        path=active if active is not None and active.exists() else Path(cfg["model"]["path"])
        self.model=AuraSoftmax.load(path) if path.exists() else None
        self.temporal=TemporalConsensus(cfg["stability"]["window"]);self.background=None
    def _unknown(self,reason,q,confidence=0.0,scene=None):
        return {"label":"unknown","raw_label":None,"confidence":float(confidence),"stable":False,"reason":reason,"quality":q,"scene":scene}
    def predict(self,frame):
        q=assess(frame,self.cfg);scene=analyse_scene(frame)
        if not q["ok"]:
            self.temporal.reject();return self._unknown(q["reason"],q,scene=scene)
        # Training uses the full frame plus the configured center ROI. Do not crop to a
        # GrabCut foreground at inference: that is both expensive and a feature mismatch.
        colour=dominant_colour(frame);env=environment(frame,scene)
        guide={"action":"capture","text":"Keep the object centered and well lit."}
        if self.model is None:
            self.temporal.reject();return self._unknown("model_not_trained",q,0.0,scene)
        f=self.fx.extract(frame);probs=self.model.predict_proba(f[None,:])[0];order=np.argsort(probs)[::-1]
        if len(order)<2:return self._unknown("invalid_model",q,0.0,scene)
        top,second=map(int,order[:2]);conf=float(probs[top]);margin=float(probs[top]-probs[second])
        threshold=max(float(self.cfg["model"]["confidence_threshold"]),float(getattr(self.model,"unknown_threshold",.55)))
        if conf<threshold or margin<float(self.cfg["model"]["margin_threshold"]):
            self.temporal.reject();return self._unknown("uncertain",q,conf,scene)
        raw=self.model.labels[top];self.temporal.update(raw,conf)
        stable=self.temporal.result(self.cfg["stability"]["min_votes"],self.cfg["stability"]["min_mean_confidence"])
        base={"label":"unknown","raw_label":raw,"confidence":conf,"stable":False,"reason":"collecting_evidence","quality":q,"scene":scene,"colour":colour,"environment":env,"guidance":guide}
        if stable is None:return base
        label,mean,votes=stable;base.update(label=label,stable=True,reason="verified",votes=votes,mean_confidence=mean);return base
