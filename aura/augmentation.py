import cv2, numpy as np

def augment(img, rng):
    h,w=img.shape[:2]; angle=float(rng.uniform(-10,10)); scale=float(rng.uniform(.92,1.08))
    M=cv2.getRotationMatrix2D((w/2,h/2),angle,scale); M[:,2]+=rng.uniform(-.03*w,.03*w,2)
    x=cv2.warpAffine(img,M,(w,h),borderMode=cv2.BORDER_REFLECT_101)
    x=cv2.convertScaleAbs(x,alpha=float(rng.uniform(.9,1.1)),beta=float(rng.uniform(-15,15)))
    if rng.random()<.25: x=cv2.GaussianBlur(x,(3,3),0)
    return x
