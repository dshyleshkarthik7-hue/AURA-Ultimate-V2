#!/usr/bin/env python3
"""Interactive dataset collector: capture labeled images from a camera."""
import argparse
import time
from pathlib import Path
from datetime import datetime

import cv2

from aura.config import load_config
from aura.camera import Camera


def count_images(label_dir):
    return len(list(label_dir.glob('*.jpg')) + list(label_dir.glob('*.jpeg')) + list(label_dir.glob('*.png')))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--config', default='config.yaml')
    parser.add_argument('--source', default='0', help='Camera index or device path')
    args = parser.parse_args()
    cfg = load_config(args.config)

    if args.label not in cfg['labels']:
        raise SystemExit('Label not in config.yaml labels.')

    label_root = Path(cfg['dataset']['root']) / args.label
    session_name = datetime.now().strftime('%Y%m%d_%H%M%S') + f'_{time.time_ns() % 1000000:06d}'
    label_dir = label_root / session_name
    label_dir.mkdir(parents=True, exist_ok=False)

    camera = Camera(args.source, cfg['camera']['width'], cfg['camera']['height'], cfg['camera']['fps'])
    if not camera.open():
        raise SystemExit('Camera open failed')

    count = count_images(label_root)
    print(f'Session: {label_dir}. SPACE saves one image, A saves a 30-frame burst, Q quits.')
    print('Use a new collector session for each different background, lighting setup, camera position, and day.')

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                continue

            cv2.putText(frame, f'{args.label} | {count} images', (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow('AURA Collector', frame)
            key = cv2.waitKey(1) & 255

            if key == ord('q'):
                break
            if key in (32, ord('a')):
                burst = 30 if key == ord('a') else 1
                for _ in range(burst):
                    ok, img = camera.read()
                    if ok:
                        cv2.imwrite(str(label_dir / f'{args.label}_{time.time_ns()}.jpg'), img)
                        count += 1
                    time.sleep(0.08)
    finally:
        camera.release()
        cv2.destroyAllWindows()

    print('Saved', count)


if __name__ == '__main__':
    main()
