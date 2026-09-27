# AURA V2 — Adaptive Perception Simulation

This web experience is an active-perception simulation rather than a claim of perfect computer vision.

Runtime: camera -> scene quality -> lighting/exposure estimation -> evidence capture -> conceptual human/object separation -> background suppression -> colour normalization -> multi-view evidence -> temporal fusion -> conversational response.

The five language experience uses browser speech synthesis with graceful fallback. Actual voice availability and quality depend on the browser/device.

The existing Python classifier remains the offline training prototype. A production ML path should use session-level splits, unknown-object evaluation, calibration, regression gates, and model promotion/rollback rather than treating synthetic augmentation as independent evidence.
