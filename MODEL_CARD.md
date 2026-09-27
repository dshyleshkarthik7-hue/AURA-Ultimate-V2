# AURA Model Card

Run python train.py, python evaluate.py, then python scripts/generate_model_card.py to refresh this file.

The model is a three-class offline prototype. Temperature calibration is fitted on the validation partition during training. Unknown-object rejection is only meaningful when an independently collected unknown-object evaluation set is supplied.
