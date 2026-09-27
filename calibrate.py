#!/usr/bin/env python3
"""Intrinsic calibration using user-captured chessboard images.

Calibration is optional and not required for classification.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np

from aura.camera import Camera


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cols', type=int, default=9)
    parser.add_argument('--rows', type=int, default=6)
    parser.add_argument('--source', default='0', help='Camera index or device path')
    parser.add_argument('--outdir', default='calibration')
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(exist_ok=True)

    camera = Camera(args.source)
    if not camera.open():
        raise SystemExit('Camera failed')

    object_points = np.zeros((args.rows * args.cols, 3), np.float32)
    object_points[:, :2] = np.mgrid[0:args.cols, 0:args.rows].T.reshape(-1, 2)
    obj_points_list, img_points_list = [], []

    print('Show chessboard. SPACE capture valid frame; C calibrate; Q quit.')

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            found, corners = cv2.findChessboardCorners(gray, (args.cols, args.rows))
            display = frame.copy()
            if found:
                cv2.drawChessboardCorners(display, (args.cols, args.rows), corners, found)
            cv2.imshow('AURA Calibration', display)

            key = cv2.waitKey(1) & 255
            if key == ord('q'):
                break
            if key == 32 and found:
                corners = cv2.cornerSubPix(
                    gray, corners, (11, 11), (-1, -1),
                    (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                obj_points_list.append(object_points)
                img_points_list.append(corners)
                print('captured', len(obj_points_list))
            if key == ord('c') and len(obj_points_list) >= 8:
                _, K, dist, _, _ = cv2.calibrateCamera(
                    obj_points_list, img_points_list, gray.shape[::-1], None, None)
                np.savez(outdir / 'camera_intrinsics.npz', K=K, dist=dist)
                print('saved calibration')
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
