from pathlib import Path
import os,tempfile
import numpy as np

class AuraSoftmax:
    def __init__(self):
        self.W=self.b=self.mean=self.std=self.labels=None
        self.temperature=1.0;self.unknown_threshold=.55;self.model_version=6
    @staticmethod
    def _softmax(z):
        z=z-z.max(axis=1,keepdims=True);e=np.exp(z);return e/(e.sum(axis=1,keepdims=True)+1e-12)
    def validate(self):
        if any(x is None for x in [self.W,self.b,self.mean,self.std,self.labels]): raise ValueError("Incomplete model")
        if not isinstance(self.labels,list) or len(self.labels)<2 or len(set(self.labels))!=len(self.labels): raise ValueError("Invalid labels")
        d,k=self.W.shape
        if self.b.shape!=(k,) or self.mean.shape!=(d,) or self.std.shape!=(d,) or len(self.labels)!=k: raise ValueError("Invalid model shapes")
        if not all(np.isfinite(x).all() for x in [self.W,self.b,self.mean,self.std]): raise ValueError("Non-finite model")
        if np.any(self.std<=0) or not np.isfinite(self.temperature) or self.temperature<=0 or not 0<self.unknown_threshold<1: raise ValueError("Invalid calibration")
    def fit(self,X,y,labels,epochs=600,lr=.08,l2=5e-4,batch_size=32,seed=42,class_weight="balanced",validation_data=None,patience=40):
        X=np.asarray(X,np.float32);y=np.asarray(y,np.int64);n,d=X.shape;k=len(labels)
        if X.ndim!=2 or n==0 or len(y)!=n or k<2 or np.any(y<0)|np.any(y>=k) or not np.isfinite(X).all(): raise ValueError("Invalid training data")
        self.labels=list(labels);self.mean=X.mean(0);self.std=np.maximum(X.std(0),1e-6);X=(X-self.mean)/self.std
        if class_weight=="balanced":
            c=np.bincount(y,minlength=k).astype(np.float32)
            if np.any(c==0): raise ValueError("Every class needs samples")
            weights=n/(k*c)
        elif class_weight in (None,"none"): weights=np.ones(k,np.float32)
        else: raise ValueError("Unsupported class_weight")
        val=None
        if validation_data is not None:
            VX,Vy=validation_data;VX=np.asarray(VX,np.float32);Vy=np.asarray(Vy,np.int64)
            if VX.ndim!=2 or VX.shape[1]!=d or len(Vy)!=len(VX) or len(Vy)==0 or not np.isfinite(VX).all(): raise ValueError("Invalid validation data")
            val=((VX-self.mean)/self.std,Vy)
        self.W=np.zeros((d,k),np.float32);self.b=np.zeros(k,np.float32);rng=np.random.default_rng(seed);bs=max(1,min(int(batch_size),n))
        best=None;best_loss=float("inf");stale=0;limit=max(1,int(patience))
        for _ in range(int(epochs)):
            for bi in [rng.permutation(n)[st:st+bs] for st in range(0,n,bs)]:
                Y=np.eye(k,dtype=np.float32)[y[bi]];p=self._softmax(X[bi]@self.W+self.b);sw=weights[y[bi]]
                g=((p-Y)*sw[:,None])/max(float(sw.sum()),1e-8);self.W-=lr*(X[bi].T@g+l2*self.W);self.b-=lr*g.sum(0)
            if val is not None:
                vp=self._softmax(val[0]@self.W+self.b);Vy=val[1]
                loss=-float(np.mean(np.log(np.clip(vp[np.arange(len(Vy)),Vy],1e-8,1.0))))
                if loss+1e-7<best_loss:
                    best_loss=loss;best=(self.W.copy(),self.b.copy());stale=0
                else:
                    stale+=1
                    if stale>=limit: break
        if best is not None:self.W,self.b=best
        self.validate()
    def predict_proba(self,X):
        self.validate();X=np.asarray(X,np.float32)
        if X.ndim==1:X=X[None,:]
        if X.ndim!=2 or X.shape[1]!=self.W.shape[0] or not np.isfinite(X).all(): raise ValueError("Invalid feature matrix")
        if len(X)==0:return np.empty((0,len(self.labels)),np.float32)
        return self._softmax((((X-self.mean)/self.std)@self.W+self.b)/max(self.temperature,1e-3))
    def save(self,path):
        self.validate();path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix=".model-",suffix=".npz",dir=path.parent)
        os.close(fd)
        try:
            np.savez_compressed(tmp,W=self.W,b=self.b,mean=self.mean,std=self.std,labels=np.asarray(self.labels,dtype=str),model_version=np.asarray(self.model_version,dtype=np.int32),temperature=np.asarray(self.temperature,dtype=np.float32),unknown_threshold=np.asarray(self.unknown_threshold,dtype=np.float32))
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    @classmethod
    def load(cls,path):
        with np.load(path,allow_pickle=False) as d:
            m=cls();m.W=d["W"].astype(np.float32);m.b=d["b"].astype(np.float32);m.mean=d["mean"].astype(np.float32);m.std=d["std"].astype(np.float32);m.labels=d["labels"].astype(str).tolist();m.model_version=int(d["model_version"]) if "model_version" in d else 1;m.temperature=float(d["temperature"]) if "temperature" in d else 1.;m.unknown_threshold=float(d["unknown_threshold"]) if "unknown_threshold" in d else .55
        m.validate();return m
