#!/usr/bin/env python3
import argparse, json
from pathlib import Path
import cv2, numpy as np
from aura.config import load_config
from aura.data import validate_dataset
from aura.features import FeatureExtractor
from aura.model import AuraSoftmax
from aura.augmentation import augment

def split_indices(y,k,val_frac,test_frac,rng):
    tr=[]; va=[]; te=[]
    for c in range(k):
        a=np.where(y==c)[0]; rng.shuffle(a); n=len(a)
        nt=max(1,int(round(n*test_frac))); nv=max(1,int(round(n*val_frac)))
        if nt+nv>=n: nt=nv=1
        te+=a[:nt].tolist(); va+=a[nt:nt+nv].tolist(); tr+=a[nt+nv:].tolist()
    rng.shuffle(tr); rng.shuffle(va); rng.shuffle(te); return map(lambda z:np.asarray(z,dtype=np.int64),(tr,va,te))

def main():
 p=argparse.ArgumentParser(); p.add_argument('--config',default='config.yaml'); a=p.parse_args(); cfg=load_config(a.config)
 root=Path(cfg['dataset']['root']); labels=list(cfg['labels']); files_by=validate_dataset(root,labels,cfg['training']['min_images_per_class'])
 fx=FeatureExtractor(cfg['model']['image_size'],cfg.get('roi')); X=[]; y=[]; paths=[]; failures=[]
 for ci,label in enumerate(labels):
  for f in files_by[label]:
   im=cv2.imread(str(f))
   if im is None: failures.append(str(f)); continue
   try: X.append(fx.extract(im)); y.append(ci); paths.append(str(f))
   except Exception as e: failures.append(f'{f}: {e}')
 if failures: Path('feature_failures.log').write_text('\n'.join(failures));
 if failures and len(failures)>max(5,int(.02*(len(paths)+len(failures)))): raise SystemExit('Too many unreadable/feature failures; see feature_failures.log')
 X=np.asarray(X,np.float32); y=np.asarray(y,np.int64); rng=np.random.default_rng(cfg['training']['seed'])
 tr,va,te=split_indices(y,len(labels),cfg['training']['validation_fraction'],cfg['training']['test_fraction'],rng)
 # Augment only the training partition to avoid train/test augmentation leakage.
 Xtr=X[tr]; ytr=y[tr]
 aug_rng=np.random.default_rng(cfg['training']['seed']+1)
 extra=[]; extra_y=[]
 for original_index in tr:
  im=cv2.imread(paths[original_index])
  if im is not None:
   try:
    extra.append(fx.extract(augment(im,aug_rng))); extra_y.append(y[original_index])
   except Exception: pass
 if extra:
  Xtr=np.vstack([Xtr,np.asarray(extra,np.float32)]); ytr=np.concatenate([ytr,np.asarray(extra_y,np.int64)])
 model=AuraSoftmax(); model.fit(Xtr,ytr,labels,epochs=cfg['training']['epochs'],lr=cfg['training']['learning_rate'],l2=cfg['training']['l2'],batch_size=cfg['training']['batch_size'],seed=cfg['training']['seed'])
 mp=Path(cfg['model']['path']); mp.parent.mkdir(parents=True,exist_ok=True); model.save(mp)
 for name,idx in [('validation',va),('test',te)]:
  pred=model.predict_proba(X[idx]).argmax(1); print(name,'accuracy',float((pred==y[idx]).mean()),'n=',len(idx))
 Path('splits.json').write_text(json.dumps({'train':[paths[i] for i in tr],'validation':[paths[i] for i in va],'test':[paths[i] for i in te]},indent=2))
 print('Saved',mp)
if __name__=='__main__': main()
