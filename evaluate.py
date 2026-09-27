#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import cv2, numpy as np
from aura.config import load_config
from aura.features import FeatureExtractor
from aura.model import AuraSoftmax
from aura.data import image_files

def main():
 p=argparse.ArgumentParser(); p.add_argument('--config',default='config.yaml'); p.add_argument('--dataset',default=None); a=p.parse_args(); cfg=load_config(a.config)
 model=AuraSoftmax.load(cfg['model']['path']); fx=FeatureExtractor(cfg['model']['image_size'],cfg.get('roi')); labels=model.labels
 root=Path(a.dataset) if a.dataset else None
 if root is None: splits=json.loads(Path('splits.json').read_text()); items=[(Path(x),i) for i,l in enumerate(labels) for x in splits['test'] if Path(x).parent.name==l]
 else: items=[(f,i) for i,l in enumerate(labels) for f in image_files(root/l)]
 cm=np.zeros((len(labels),len(labels)),int); conf=[]
 for f,true in items:
  im=cv2.imread(str(f));
  if im is None: continue
  pr=model.predict_proba(fx.extract(im))[0]; pred=int(pr.argmax()); cm[true,pred]+=1; conf.append(float(pr[pred]))
 print('labels:',labels); print('confusion_matrix:'); print(cm); print('accuracy:',np.trace(cm)/max(1,cm.sum())); print('confidence mean/min/max:',float(np.mean(conf)),float(np.min(conf)),float(np.max(conf)))
 for i,l in enumerate(labels):
  tp=cm[i,i]; fp=cm[:,i].sum()-tp; fn=cm[i,:].sum()-tp; prec=tp/max(1,tp+fp); rec=tp/max(1,tp+fn); f1=2*prec*rec/max(1e-9,prec+rec); print(l,{'precision':prec,'recall':rec,'f1':f1})
if __name__=='__main__': main()
