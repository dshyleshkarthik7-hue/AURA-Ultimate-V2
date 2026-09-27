# AURA Perception V2 Deployment Status

Configured production labels are exactly: `steel_glass`, `steel_water_bottle`, and `bottle_gourd`. Legacy labels were removed. The bundled dataset contains originals plus deterministic offline augmentations to approximately 180 files per class. Augmented files are not independent photographs and must not be presented as independent data for accuracy claims. Run `python train.py` and then `python evaluate.py` locally to measure the actual result.
