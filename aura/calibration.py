"""Calibration and evaluation gates for AURA models."""
import numpy as np
from .model import AuraSoftmax

def fit_temperature(model, X, y):
    probs=model.predict_proba(X); logits=np.log(np.clip(probs,1e-8,1))
    best=(1.0, float("inf"))
    for t in np.linspace(.5,3.0,51):
        p=np.exp(logits/t);p/=p.sum(1,keepdims=True)
        loss=-np.mean(np.log(np.clip(p[np.arange(len(y)),y],1e-8,1)))
        if loss<best[1]:best=(float(t),loss)
    model.temperature=best[0]; return best

def evaluate(model,X,y,unknown_X=None):
    p=model.predict_proba(X); pred=p.argmax(1); acc=float((pred==y).mean())
    f1=[]
    for c in range(len(model.labels)):
        tp=((pred==c)&(y==c)).sum(); fp=((pred==c)&(y!=c)).sum(); fn=((pred!=c)&(y==c)).sum()
        pr=tp/max(1,tp+fp); re=tp/max(1,tp+fn); f1.append(2*pr*re/max(1e-9,pr+re))
    unknown_rejection=1.0
    if unknown_X is not None and len(unknown_X):
        up=model.predict_proba(unknown_X).max(1); unknown_rejection=float((up<model.unknown_threshold).mean())
    return {"accuracy":acc,"macro_f1":float(np.mean(f1)),"unknown_rejection":unknown_rejection}

def promotion_gate(metrics,previous=None):
    if metrics["macro_f1"]<.85 or metrics["unknown_rejection"]<.90:return False
    if previous and metrics["macro_f1"]<previous.get("macro_f1",0)-.02:return False
    return True
