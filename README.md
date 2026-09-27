# AURA Perception V2

Offline-first, privacy-preserving Indian multilingual object recognition prototype.

## Objects
- Steel Glass
- Steel Water Bottle
- Bottle Gourd

## Languages
English, Hindi, Telugu, Tamil, Gujarati.

## Important
No cloud inference, agents, pretrained AI model, or internet connection is required during operation. Accuracy is measured locally; no 100% claim is made.

## Quick start
1. Install Python 3.10–3.13.
2. `python -m venv .venv`
3. Activate it.
4. `pip install -r requirements.txt`
5. `python -m unittest discover -s tests -p "test*.py"`
6. `python train.py`
7. `python evaluate.py`
8. `python app.py`

## Dataset note
The production dataset contains your original camera images. A separate `dataset_augmented/` folder contains approximately 180 files per class for inspection/demo purposes; these are generated transformations and are deliberately excluded from held-out evaluation. Training performs augmentation only on the training partition to avoid augmentation leakage. For credible grants and deployment, collect additional independent real camera sessions and evaluate on sessions never used for training.
