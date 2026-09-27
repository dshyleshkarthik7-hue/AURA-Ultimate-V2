import cv2
import numpy as np


class FeatureExtractor:
    """AURA's original handcrafted descriptor: color, gradients and texture."""

    def __init__(self, size=128, roi=None):
        self.size = int(size)
        roi = roi or {}
        self.mode = roi.get("mode", "center")
        self.width_ratio = float(roi.get("width_ratio", 1.0))
        self.height_ratio = float(roi.get("height_ratio", 1.0))

    def _roi(self, frame):
        if self.mode != "center":
            return frame

        h, w = frame.shape[:2]
        rw = max(1, min(w, int(w * self.width_ratio)))
        rh = max(1, min(h, int(h * self.height_ratio)))
        x = (w - rw) // 2
        y = (h - rh) // 2
        return frame[y:y + rh, x:x + rw]

    def extract(self, frame):
        roi = self._roi(frame)
        img = cv2.resize(
            roi, (self.size, self.size), interpolation=cv2.INTER_AREA
        )

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist(
            [hsv], [0, 1, 2], None,
            [12, 6, 4],
            [0, 180, 0, 256, 0, 256],
        ).astype(np.float32).ravel()
        hist /= hist.sum() + 1e-8

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        magnitude, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)

        gradient_hist, _ = np.histogram(
            angle, bins=9, range=(0, 360), weights=magnitude
        )
        gradient_hist = gradient_hist.astype(np.float32)
        gradient_hist /= gradient_hist.sum() + 1e-8

        small = cv2.resize(
            gray, (32, 32), interpolation=cv2.INTER_AREA
        ).astype(np.float32) / 255.0

        texture = []
        for yy in range(0, 32, 8):
            for xx in range(0, 32, 8):
                patch = small[yy:yy + 8, xx:xx + 8]
                texture.extend([patch.mean(), patch.std()])

        return np.concatenate(
            [hist, gradient_hist, np.asarray(texture, dtype=np.float32)]
        ).astype(np.float32)
