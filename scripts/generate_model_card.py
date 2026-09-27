#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];e=json.loads((ROOT/"evaluation.json").read_text()) if (ROOT/"evaluation.json").exists() else {}
lines=["# AURA Model Card","","## Scope","Three-class offline object-recognition prototype.","","## Evaluation",""]
for k in ["samples","accuracy","accuracy_ci95","macro_f1","mean_confidence","unknown_samples","unknown_rejection","model_version","temperature","unknown_threshold"]:lines.append(f"- **{k}:** {e.get(k,'not measured')}")
lines+=["","## Per-class metrics"]
for label,m in zip(e.get("labels",[]),e.get("per_class",[])):lines.append(f"- **{label}:** precision {m['precision']:.3f}, recall {m['recall']:.3f}, F1 {m['f1']:.3f}")
lines+=["","## Limitations","Training data are imbalanced and automatic retraining uses guarded pseudo-labels. Unknown rejection requires an independently collected unknown-object set.","","## Intended use","Offline prototype research and controlled evaluation; not a sole safety-critical decision maker."]
(ROOT/"MODEL_CARD.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
