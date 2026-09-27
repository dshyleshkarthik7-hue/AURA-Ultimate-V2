import cv2
import platform
import time


class Camera:
    """
    Cross-platform camera wrapper with safer open/read/reconnect handling.
    """

    def __init__(
        self,
        source=0,
        width=1280,
        height=720,
        fps=30,
    ):
        self.source = self._parse_source(source)
        self.width = int(width)
        self.height = int(height)
        self.fps = int(fps)

        self.cap = None
        self.backend_name = "DEFAULT"

    @staticmethod
    def _parse_source(source):
        try:
            return int(source)
        except (TypeError, ValueError):
            return str(source)

    def _backend_candidates(self):
        """
        Use platform-appropriate backends.
        """
        system = platform.system().lower()

        if not isinstance(self.source, int):
            return [(cv2.CAP_ANY, "DEFAULT")]

        if system == "windows":
            return [
                (cv2.CAP_DSHOW, "DIRECTSHOW"),
                (cv2.CAP_MSMF, "MSMF"),
                (cv2.CAP_ANY, "DEFAULT"),
            ]

        if system == "linux":
            return [
                (cv2.CAP_V4L2, "V4L2"),
                (cv2.CAP_ANY, "DEFAULT"),
            ]

        if system == "darwin":
            return [
                (cv2.CAP_AVFOUNDATION, "AVFOUNDATION"),
                (cv2.CAP_ANY, "DEFAULT"),
            ]

        return [(cv2.CAP_ANY, "DEFAULT")]

    def open(self):
        self.release()

        for backend, backend_name in self._backend_candidates():

            try:
                cap = cv2.VideoCapture(
                    self.source,
                    backend,
                )

                if not cap.isOpened():
                    cap.release()
                    continue

                cap.set(
                    cv2.CAP_PROP_FRAME_WIDTH,
                    self.width,
                )

                cap.set(
                    cv2.CAP_PROP_FRAME_HEIGHT,
                    self.height,
                )

                cap.set(
                    cv2.CAP_PROP_FPS,
                    self.fps,
                )

                # Try to reduce camera buffering.
                cap.set(
                    cv2.CAP_PROP_BUFFERSIZE,
                    1,
                )

                # Give camera a moment to initialize.
                time.sleep(0.3)

                self.cap = cap
                self.backend_name = backend_name

                return True

            except Exception:
                try:
                    cap.release()
                except Exception:
                    pass

        self.cap = None
        return False

    def is_open(self):
        return (
            self.cap is not None
            and self.cap.isOpened()
        )

    def read(self):
        """
        Returns:
            (True, frame)  on success
            (False, None)  on failure

        Never intentionally loops forever.
        """

        if not self.is_open():
            return False, None

        try:
            ok, frame = self.cap.read()

            if not ok or frame is None:
                return False, None

            return True, frame

        except KeyboardInterrupt:
            # Allow Ctrl+C to cleanly exit.
            raise

        except Exception:
            return False, None

    def reconnect(self, delay=1.0):
        self.release()
        time.sleep(delay)
        return self.open()

    def release(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass

            self.cap = None