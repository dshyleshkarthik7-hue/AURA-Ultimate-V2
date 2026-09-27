from pathlib import Path
import numpy as np
class AuraSoftmax:
 def __init__(self): self.W=self.b=self.mean=self.std=self.labels=None;self.temperature=1.;self.unknown_threshold=.55;self.model_version=4
 @staticmethod
 def _softmax(z):
  z=z-z.max(axis=1,keepdims=True);e=np.exp(z);return e/(e.sum(axis=1,keepdims=True)+1e-12)
 def validate(self):
  if any(x is None for x in [self.W,self.b,self.mean,self.std,self.labels]):raise ValueError("Incomplete model")
  d,k=self.W.shape
  if self.b.shape!=(k,) or self.mean.shape!=(d,) or self.std.shape!=(d,) or len(self.labels)!=k:raise ValueError("Invalid model shapes")
  if not all(np.isfinite(x).all() for x in [self.W,self.b,self.mean,self.std]):raise ValueError("Non-finite model")
  if self.temperature<=0 or not 0<self.unknown_threshold<1:raise ValueError("Invalid calibration")
 def fit(self,X,y,labels,epochs=600,lr=.08,l2=5e-4,batch_size=32,seed=42,class_weight="balanced"):
  X=np.asarray(X,np.float32);y=np.asarray(y,np.int64);n,d=X.shape;k=len(labels);self.labels=list(labels);self.mean=X.mean(0);self.std=np.maximum(X.std(0),1e-6);X=(X-self.mean)/self.std
  if class_weight=="balanced":
   c=np.bincount(y,minlength=k).astype(np.float32)
   if np.any(c==0):raise ValueError("Every class needs samples")
   w=n/(k*c)
  else:w=np.ones(k,np.float32)
  self.W=np.zeros((d,k),np.float32);self.b=np.zeros(k,np.float32);rng=np.random.default_rng(seed);bs=max(1,min(int(batch_size),n))
  for _ in range(int(epochs)):
   idx=rng.permutation(n)
   for st in range(0,n,bs):
    bi=idx[st:st+bs];Y=np.eye(k,dtype=np.float32)[y[bi]];p=self._softmax(X[bi]@self.W+self.b);sw=w[y[bi]];g=((p-Y)*sw[:,None])/max(float(sw.sum()),1e-8);self.W-=lr*(X[bi].T@g+l2*self.W);self.b-=lr*g.sum(0)
  self.validate()
 def predict_proba(self,X):
  self.validate();X=np.asarray(X,np.float32)
  if X.ndim==1:X=X[None,:]
  z=((X-self.mean)/self.std)@self.W+self.b;return self._softmax(z/max(self.temperature,1e-3))
 def save(self,path):
  self.validate();Path(path).parent.mkdir(parents=True,exist_ok=True);np.savez_compressed(path,W=self.W,b=self.b,mean=self.mean,std=self.std,labels=np.asarray(self.labels,dtype=str),model_version=np.asarray(self.model_version,dtype=np.int32),temperature=np.asarray(self.temperature,dtype=np.float32),unknown_threshold=np.asarray(self.unknown_threshold,dtype=np.float32))
 @classmethod
 def load(cls,path):
  with np.load(path,allow_pickle=False) as d:
   m=cls();m.W=d["W"];m.b=d["b"];m.mean=d["mean"];m.std=d["std"];m.labels=d["labels"].astype(str).tolist();m.model_version=int(d["model_version"]) if "model_version" in d else 1;m.temperature=float(d["temperature"]) if "temperature" in d else 1.;m.unknown_threshold=float(d["unknown_threshold"]) if "unknown_threshold" in d else .55
  m.validate();return m
