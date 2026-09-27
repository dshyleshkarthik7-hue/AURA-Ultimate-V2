
from pathlib import Path
import numpy as np
class AuraSoftmax:
    """AURA custom NumPy classifier: no pretrained model and no cloud inference."""
    def __init__(self): self.W=self.b=self.mean=self.std=self.labels=None
    @staticmethod
    def _softmax(z):
        z=z-z.max(axis=1,keepdims=True); e=np.exp(z); return e/(e.sum(axis=1,keepdims=True)+1e-12)
    def validate(self):
        if any(x is None for x in [self.W,self.b,self.mean,self.std,self.labels]): raise ValueError("Incomplete model")
        d,k=self.W.shape
        if self.b.shape!=(k,) or self.mean.shape!=(d,) or self.std.shape!=(d,) or len(self.labels)!=k: raise ValueError("Invalid model shapes")
        if not all(np.isfinite(x).all() for x in [self.W,self.b,self.mean,self.std]): raise ValueError("Non-finite model")
    def fit(self,X,y,labels,epochs=600,lr=.08,l2=5e-4,batch_size=32,seed=42):
        X=np.asarray(X,np.float32);y=np.asarray(y,np.int64); n,d=X.shape;k=len(labels)
        if n==0 or k<2: raise ValueError("Need samples from at least two classes")
        self.labels=list(labels);self.mean=X.mean(0);self.std=np.maximum(X.std(0),1e-6);X=(X-self.mean)/self.std
        self.W=np.zeros((d,k),np.float32);self.b=np.zeros(k,np.float32);rng=np.random.default_rng(seed)
        for _ in range(int(epochs)):
            for start in range(0,n,max(1,min(int(batch_size),n))):
                # shuffled each epoch
                if start==0: idx=rng.permutation(n)
                bi=idx[start:start+max(1,min(int(batch_size),n))]; xb=X[bi]; yb=y[bi]
                Y=np.eye(k,dtype=np.float32)[yb];p=self._softmax(xb@self.W+self.b);g=(p-Y)/len(bi)
                self.W-=lr*(xb.T@g+l2*self.W);self.b-=lr*g.sum(0)
        self.validate()
    def predict_proba(self,X):
        self.validate();X=np.asarray(X,np.float32)
        if X.ndim==1:X=X[None,:]
        if X.shape[1]!=self.W.shape[0]:raise ValueError("Feature dimension mismatch")
        return self._softmax(((X-self.mean)/self.std)@self.W+self.b)
    def save(self,path):
        self.validate();Path(path).parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(path,W=self.W,b=self.b,mean=self.mean,std=self.std,labels=np.asarray(self.labels,dtype=str),model_version=np.asarray(2,dtype=np.int32))
    @classmethod
    def load(cls,path):
        with np.load(path,allow_pickle=False) as d:
            m=cls();m.W=d["W"];m.b=d["b"];m.mean=d["mean"];m.std=d["std"];m.labels=d["labels"].astype(str).tolist()
        m.validate();return m
