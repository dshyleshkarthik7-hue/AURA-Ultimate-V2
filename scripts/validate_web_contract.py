#!/usr/bin/env python3
import base64,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import yaml
def main():
 c=yaml.safe_load((ROOT/"config.yaml").read_text());w=json.loads((ROOT/"web/model_config.json").read_text());a=(ROOT/"web/model.b64").read_text().strip();app=(ROOT/"web/app.js").read_text();idx=(ROOT/"web/index.html").read_text()
 assert w["artifact"]=="model.b64" and w["artifact_format"]=="npz-base64" and w["feature_contract"]=="opencv-v1-329" and w["feature_length"]==329
 assert w["labels"]==list(c["labels"]) and w["image_size"]==c["model"]["image_size"] and w["roi"]==c["roi"] and len(base64.b64decode(a))>1000
 for n in ("featureFromCanvas","loadNpz","sceneMask","grabCutBox","viewEvidence","excludePerson","progress","captureView"): assert re.search(r"function\s+"+n+r"\s*\(",app),n
 assert "opencv.js" in idx and "fflate" in idx and "model.b64" in app
 for n in ("cv.cvtColor","cv.calcHist","cv.Sobel","cv.cartToPolar","cv.resize","cv.INTER_AREA"): assert n in app,n
 assert "window.AURA_TEST" in app and "width_ratio" in app and "height_ratio" in app
 print("web contract OK: artifact, dependencies, ROI, OpenCV feature stages, perception stages")
if __name__=="__main__":main()
