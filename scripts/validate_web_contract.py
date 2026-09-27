#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import yaml
def main():
 c=yaml.safe_load((ROOT/"config.yaml").read_text());w=json.loads((ROOT/"web/model_config.json").read_text());a=(ROOT/"web/model.b64").read_text().strip();app=(ROOT/"web/app.js").read_text();idx=(ROOT/"web/index.html").read_text()
 assert w["artifact"]=="model.b64" and w["artifact_format"]=="npz-base64" and w["feature_contract"]=="opencv-v1-329" and w["feature_length"]==329
 assert w["labels"]==list(c["labels"]) and w["image_size"]==c["model"]["image_size"] and w["roi"]==c["roi"] and a.startswith("UEsDB")
 for n in ("featureFromCanvas","loadNpz","sceneMask","grabCutBox","viewEvidence","excludePerson","progress","captureView"): assert re.search(r"function\s+"+n+r"\s*\(",app),n
 assert "opencv.js" in idx and "fflate" in idx and "model.b64" in app
 for n in ("cv.calcHist","cv.Sobel","cv.cartToPolar","cv.resize"): assert n in app,n
 print("web contract OK")
if __name__=="__main__":main()
