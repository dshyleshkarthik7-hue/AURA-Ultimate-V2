"""Real-time scene analysis, foreground segmentation and guidance helpers."""
from __future__ import annotations
import cv2
import numpy as np

LIGHTING = ("daylight", "warm_indoor", "cool_indoor", "low_light",
            "backlit", "overexposed", "underexposed", "mixed_light", "balanced")

def analyse_scene(frame):
    if frame is None or frame.size == 0:
        return {"ok": False, "lighting": "unknown"}
    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    gray=hsv[:,:,2].astype(np.float32)
    mean=float(gray.mean()); p5,p95=np.percentile(gray,[5,95])
    clipped=float((gray>=250).mean()); dark=float((gray<=20).mean())
    sat=float(hsv[:,:,1].mean())
    if mean<55 or dark>.30: lighting="low_light"
    elif clipped>.18 or mean>220: lighting="overexposed"
    elif p5<20 and p95>220: lighting="mixed_light"
    elif dark>.20 and mean>100: lighting="backlit"
    else: lighting="balanced"
    edges=cv2.Canny(frame,80,160)
    sharp=float(cv2.Laplacian(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY),cv2.CV_64F).var())
    return {"ok": True, "lighting": lighting, "brightness": mean,
            "contrast": float(p95-p5), "clipped_fraction": clipped,
            "dark_fraction": dark, "saturation": sat, "sharpness": sharp}

def foreground_mask(frame, background=None):
    """Foreground segmentation using GrabCut when no reference exists and
    background differencing when a reference frame is available."""
    h,w=frame.shape[:2]
    if background is not None and background.shape==frame.shape:
        a=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        b=cv2.cvtColor(background,cv2.COLOR_BGR2GRAY)
        diff=cv2.GaussianBlur(cv2.absdiff(a,b),(5,5),0)
        _,mask=cv2.threshold(diff,18,255,cv2.THRESH_BINARY)
        kernel=np.ones((5,5),np.uint8)
        mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel)
        mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel)
        return mask
    mask=np.zeros((h,w),np.uint8)
    rect=(max(1,int(.08*w)),max(1,int(.08*h)),max(1,int(.84*w)),max(1,int(.84*h)))
    try:
        bgd=np.zeros((1,65),np.float64); fgd=np.zeros((1,65),np.float64)
        cv2.grabCut(frame,mask,rect,bgd,fgd,3,cv2.GC_INIT_WITH_RECT)
        return np.where((mask==2)|(mask==0),0,255).astype(np.uint8)
    except cv2.error:
        return np.full((h,w),255,np.uint8)

def crop_from_mask(frame,mask):
    ys,xs=np.where(mask>0)
    if len(xs)<max(100,int(frame.shape[0]*frame.shape[1]*.01)):
        return frame
    pad=12; x1=max(0,int(xs.min())-pad); x2=min(frame.shape[1],int(xs.max())+pad)
    y1=max(0,int(ys.min())-pad); y2=min(frame.shape[0],int(ys.max())+pad)
    return frame[y1:y2,x1:x2]

def dominant_colour(frame,mask=None):
    hsv=cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    pixels=hsv.reshape(-1,3) if mask is None else hsv[mask>0]
    if len(pixels)==0: return {"name":"unknown","confidence":0.0}
    h,s,v=np.median(pixels,axis=0)
    if v<55: name="black"
    elif s<35 and v>190: name="white"
    elif s<55: name="silver/grey"
    elif s>90 and 35<=h<85: name="green"
    elif s>90 and (h<12 or h>=165): name="red"
    elif s>80 and 12<=h<35: name="orange/yellow"
    elif s>65 and 35<=h<85: name="green"
    elif s>55 and 85<=h<135: name="blue"
    else: name="neutral"
    return {"name":name,"confidence":float(min(1.0,abs(float(v)-128)/128+.35))}

def environment(frame,scene):
    """Visual environmental cues only; not a claim of meteorological sensing."""
    b=scene.get("brightness",128); s=scene.get("saturation",0)
    if scene.get("lighting")=="low_light": env="indoor/night-like"
    elif s>100 and b>130: env="bright/outdoor-like"
    elif scene.get("contrast",0)<35: env="diffuse/overcast-like"
    else: env="indeterminate"
    return {"visual_environment":env,"confidence":.55 if env!="indeterminate" else .25}

def guidance(mask, frame_shape):
    h,w=frame_shape[:2]
    if mask is None: return {"action":"hold","text":"Keep the object inside the guide."}
    ys,xs=np.where(mask>0)
    if len(xs)<100: return {"action":"move_closer","text":"Move the object into view."}
    cx=float(xs.mean())/w; cy=float(ys.mean())/h
    area=len(xs)/(w*h)
    if area<.08: return {"action":"move_closer","text":"Move a little closer."}
    if area>.65: return {"action":"move_back","text":"Move a little farther away."}
    if cx<.35: return {"action":"turn_right","text":"Turn slightly right."}
    if cx>.65: return {"action":"turn_left","text":"Turn slightly left."}
    if cy<.30: return {"action":"lower_camera","text":"Lower the camera slightly."}
    if cy>.72: return {"action":"raise_camera","text":"Raise the camera slightly."}
    return {"action":"capture","text":"Good view. Collecting evidence."}
