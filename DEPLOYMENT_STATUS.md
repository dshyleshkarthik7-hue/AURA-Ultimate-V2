# AURA Perception V2 — Deployment Status

## Current status: research prototype, not production validated

Configured classes are `steel_glass`, `steel_water_bottle`, and `bottle_gourd`. The committed dataset is small, imbalanced, and contains temporally adjacent frames. Random image-level splits can leak near-duplicate frames across training and evaluation; any score from such a split must not be described as independent-session accuracy.

- **No production accuracy claim is approved.** Report metrics only alongside the exact split strategy, per-class support, confusion matrix, and dataset revision.
- **Independent capture sessions are required.** Collect at least three separate sessions per class with different backgrounds, lighting, camera positions, and days before claiming generalization. Keep all frames from a burst/session in one split.
- **Unknown-object rejection is unvalidated** unless an independently collected and labelled unknown set is used.
- **Web artifacts must match the source model and config.** CI regenerates both artifacts and fails if the generated files differ from the committed versions.
- **Browser, Docker, Netlify, and desktop performance still require real environment testing.** Passing unit tests does not establish those deployment properties.
- Augmented images are synthetic derivatives, not additional independent observations. The augmentation folder is not evidence of additional capture sessions.

Before deployment, run the full CI workflow, inspect per-class evaluation results on session-held-out data, and verify the web demo in a real browser. Do not enable live payments; the checkout integration remains demo-only.
