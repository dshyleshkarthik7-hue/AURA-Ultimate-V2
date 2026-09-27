"""Calibration and conservative promotion gates."""
import numpy as np

def fit_temperature(model,X,y):
 if len(y)==0:return 1.0,float("inf")
 base=model.predict_proba(X);logits=np.log(np.clip(base,1e-8,1.0));best=(1.0,float("inf"))
 for t in np.linspace(.5,3.0,51):
  z=logits/t;z-=z.max(1,keepdims=True);p=np.exp(z);p/=p.sum(1,keepdims=True)
  loss=-float(np.mean(np.log(np.clip(p[np.arange(len(y)),y],1e-8,1.0))))
  if loss<best[1]:best=(float(t),loss)
 model.temperature=best[0];return best

def fit_unknown_threshold(model,known_X,unknown_X,min_known_acceptance=.95):
 if unknown_X is None or len(unknown_X)==0:return model.unknown_threshold
 known=model.predict_proba(known_X).max(1);unknown=model.predict_proba(unknown_X).max(1)
 candidates=np.unique(np.concatenate([known,unknown,[.5,.55,.6,.65,.7,.75,.8,.85,.9,.95]]))
 best=model.unknown_threshold;best_rej=-1.
 for t in candidates:
  acceptance=float((known>=t).mean())
  rejection=float((unknown<t).mean())
  if acceptance>=min_known_acceptance and rejection>best_rej:
   best=float(t);best_rej=rejection
 model.unknown_threshold=best
 return best

def evaluate(model,X,y,unknown_X=None):
 p=model.predict_proba(X);pred=p.argmax(1);f1=[];per_class=[]
 for c in range(len(model.labels)):
  tp=int(((pred==c)&(y==c)).sum());fp=int(((pred==c)&(y!=c)).sum());fn=int(((pred!=c)&(y==c)).sum())
  pr=tp/max(1,tp+fp);re=tp/max(1,tp+fn);f=2*pr*re/max(1e-9,pr+re);f1.append(f)
  per_class.append({"precision":pr,"recall":re,"f1":f})
 out={"accuracy":float((pred==y).mean()) if len(y) else 0.0,"macro_f1":float(np.mean(f1)) if f1 else 0.0,"per_class":per_class}
 out["unknown_rejection"]=None if unknown_X is None or len(unknown_X)==0 else float((model.predict_proba(unknown_X).max(1)<model.unknown_threshold).mean())
 return out

def promotion_gate(metrics,previous=None):
 if metrics.get("unknown_rejection") is None:return False
 if metrics.get("macro_f1",0)<.85 or metrics["unknown_rejection"]<.90:return False
 if previous and metrics["macro_f1"]<previous.get("macro_f1",0)-.02:return False
 return True
