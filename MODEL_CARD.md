# AURA Perception V2 — Model Card

## Intended use
A small educational prototype for recognizing three object classes: steel glass, steel water bottle, and bottle gourd. It is not a safety-critical recognizer and should not be used to make consequential decisions.

## Model and features
- Classifier: custom softmax classifier implemented in this repository.
- Features: OpenCV v1, 329-element descriptor.
- Input processing: configured center ROI, resize, HSV histogram, gradient-orientation histogram, and grayscale texture statistics.
- Calibration: temperature is fitted on the validation partition when enabled.
- Unknown rejection: a threshold is fitted only when a sufficiently large unknown set is available; its validity depends on that set being independent and representative.

## Data and evaluation caveats
The bundled dataset is small, imbalanced, and contains temporally adjacent frames from short capture bursts. A random image-level split can leak highly similar frames across partitions and substantially overstate generalization. Do not quote a single accuracy figure without identifying the split method, dataset revision, per-class support, and confusion matrix.

For a defensible evaluation, split by independent capture session or burst before fitting any preprocessing/calibration parameters. Collect multiple sessions per class across backgrounds, lighting, distances, and camera positions. Keep augmented versions in the same partition as their source image. Evaluate unknown objects separately using independently labelled examples.

## Limitations
- Generalization to new environments has not been established.
- Class imbalance and limited independent sessions can cause weak per-class recall.
- Browser/Python feature parity must be tested against a reproducible generated fixture.
- Temporal agreement is not equivalent to independent observations or a calibrated probability of correctness.
- The optional context and payment demo are not part of the classifier's validated capability.

## Reproducibility
Run `python train.py`, `python evaluate.py`, and `python scripts/generate_model_card.py`. Review the generated metrics and the data split before publishing results. CI checks the committed web artifacts against regenerated artifacts; it does not prove that the dataset is representative.
