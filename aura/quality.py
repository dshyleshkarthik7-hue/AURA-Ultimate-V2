
import cv2, numpy as np
def assess(frame,cfg):
    if frame is None:return {"ok":False,"sharpness":0.,"brightness":0.,"reason":"missing_frame"}
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    sharp=float(cv2.Laplacian(gray,cv2.CV_64F).var()); bright=float(gray.mean())
    q=cfg["quality"]; problems=[]
    if sharp<q["min_sharpness"]:problems.append("blurred")
    if bright<q["min_brightness"] or bright>q["max_brightness"]:problems.append("lighting")
    max_clip=q.get("max_clipped_fraction",.25)
    if float((gray<=5).mean())>max_clip:problems.append("underexposed")
    if float((gray>=250).mean())>max_clip:problems.append("overexposed")
    return {"ok":not problems,"sharpness":sharp,"brightness":bright,"reason":"ok" if not problems else "+".join(problems)}
