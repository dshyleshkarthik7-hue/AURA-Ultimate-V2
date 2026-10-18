# AURA Model Card

## Scope
Three-class offline object-recognition prototype.

## Evaluation

- **samples:** 68
- **accuracy:** 0.9852941176470589
- **accuracy_ci95:** [0.9558823529411765, 1.0]
- **macro_f1:** 0.9771559109080524
- **mean_confidence:** 0.9938309788703918
- **unknown_samples:** 0
- **unknown_rejection:** None
- **model_version:** 6
- **temperature:** 0.6499999761581421
- **unknown_threshold:** 0.550000011920929

## Per-class metrics
- **steel_glass:** precision 0.889, recall 1.000, F1 0.941
- **steel_water_bottle:** precision 1.000, recall 0.981, F1 0.990
- **bottle_gourd:** precision 1.000, recall 1.000, F1 1.000

## Limitations
Training data are imbalanced and automatic retraining uses guarded pseudo-labels. Unknown rejection requires an independently collected unknown-object set.

## Intended use
Offline prototype research and controlled evaluation; not a sole safety-critical decision maker.
