#!/usr/bin/env python3
from pathlib import Path
import cv2
from aura.config import load_config

EXTENSIONS = {".jpg", ".jpeg", ".png"}

def main():
    config = load_config()
    root = Path("dataset")
    minimum = config["training"].get("min_images_per_class", 20)

    total = 0
    ready = True

    for label in config["labels"]:
        directory = root / label
        files = []
        unreadable = 0

        if directory.exists():
            for path in directory.iterdir():
                if path.is_file() and path.suffix.lower() in EXTENSIONS:
                    if cv2.imread(str(path)) is None:
                        unreadable += 1
                    else:
                        files.append(path)

        count = len(files)
        total += count
        status = "OK" if count >= minimum else "NEEDS_IMAGES"
        if status != "OK":
            ready = False

        print(
            f"{label:18} usable={count:4} unreadable={unreadable:3} "
            f"minimum={minimum:3} {status}"
        )

    print(f"Total usable images: {total}")
    print("TRAINING_READY" if ready else "NOT_TRAINING_READY")

if __name__ == "__main__":
    main()
