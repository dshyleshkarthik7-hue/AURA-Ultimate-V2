"""Canonical 329-value feature contract shared by Python training and the browser.

The implementation intentionally mirrors the browser's arithmetic instead of
depending on OpenCV-specific histogram/gradient semantics. This keeps training
and browser inference on the same feature definition.
"""
import cv2
import numpy as np


class FeatureExtractor:
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

    @staticmethod
    def _browser_hsv_hist(img):
        # Explicit RGB->HSV arithmetic matching web/app.js. OpenCV is BGR.
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        mx = np.maximum(np.maximum(r, g), b)
        mn = np.minimum(np.minimum(r, g), b)
        delta = mx - mn
        h = np.zeros_like(mx)
        nz = delta > 0
        mask = nz & (mx == r)
        h[mask] = ((g[mask] - b[mask]) / delta[mask]) % 6.0
        mask = nz & (mx == g)
        h[mask] = (b[mask] - r[mask]) / delta[mask] + 2.0
        mask = nz & (mx == b)
        h[mask] = (r[mask] - g[mask]) / delta[mask] + 4.0
        h *= 30.0
        h[h < 0] += 180.0
        s = np.where(mx > 0, delta / mx * 255.0, 0.0)
        v = mx
        hi = np.minimum(11, np.floor(h / 15.0).astype(np.int32))
        si = np.minimum(5, np.floor(s / 256.0 * 6.0).astype(np.int32))
        vi = np.minimum(3, np.floor(v / 256.0 * 4.0).astype(np.int32))
        bins = hi * 24 + si * 4 + vi
        hist = np.bincount(bins.ravel(), minlength=288).astype(np.float32)
        return hist / (hist.sum() + 1e-8)

    @staticmethod
    def _browser_gray(img):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32)
        return 0.114 * rgb[..., 2] + 0.587 * rgb[..., 1] + 0.299 * rgb[..., 0]

    @staticmethod
    def _browser_gradient_hist(gray):
        # Exact 3x3 Sobel kernels used by the browser implementation.
        kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], np.float32)
        ky = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], np.float32)
        gx = np.zeros_like(gray)
        gy = np.zeros_like(gray)
        gx[1:-1, 1:-1] = (
            gray[:-2, :-2] * kx[0, 0] + gray[:-2, 1:-1] * kx[0, 1] +
            gray[:-2, 2:] * kx[0, 2] + gray[1:-1, :-2] * kx[1, 0] +
            gray[1:-1, 1:-1] * kx[1, 1] + gray[1:-1, 2:] * kx[1, 2] +
            gray[2:, :-2] * kx[2, 0] + gray[2:, 1:-1] * kx[2, 1] +
            gray[2:, 2:] * kx[2, 2]
        )
        gy[1:-1, 1:-1] = (
            gray[:-2, :-2] * ky[0, 0] + gray[:-2, 1:-1] * ky[0, 1] +
            gray[:-2, 2:] * ky[0, 2] + gray[1:-1, :-2] * ky[1, 0] +
            gray[1:-1, 1:-1] * ky[1, 1] + gray[1:-1, 2:] * ky[1, 2] +
            gray[2:, :-2] * ky[2, 0] + gray[2:, 1:-1] * ky[2, 1] +
            gray[2:, 2:] * ky[2, 2]
        )
        mag = np.hypot(gx, gy)
        angle = np.degrees(np.arctan2(gy, gx))
        angle[angle < 0] += 360.0
        bins = np.minimum(8, np.floor(angle / 40.0).astype(np.int32))
        hist = np.bincount(bins.ravel(), weights=mag.ravel(), minlength=9).astype(np.float32)
        return hist / (hist.sum() + 1e-8)

    def extract(self, frame):
        roi = self._roi(frame)
        img = cv2.resize(roi, (self.size, self.size), interpolation=cv2.INTER_LINEAR)
        hist = self._browser_hsv_hist(img)
        gray = self._browser_gray(img)
        gradient = self._browser_gradient_hist(gray)
        small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_LINEAR) / 255.0
        texture = []
        for yy in range(0, 32, 8):
            for xx in range(0, 32, 8):
                patch = small[yy:yy + 8, xx:xx + 8]
                texture.extend([float(patch.mean()), float(patch.std())])
        out = np.concatenate([hist, gradient, np.asarray(texture, dtype=np.float32)]).astype(np.float32)
        if out.shape != (329,) or not np.isfinite(out).all():
            raise ValueError("Invalid 329-feature contract")
        return out
