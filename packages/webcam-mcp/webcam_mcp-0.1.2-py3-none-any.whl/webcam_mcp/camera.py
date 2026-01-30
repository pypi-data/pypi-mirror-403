"""Webcam capture utilities for photo and video frame capture."""

import logging
import platform
import time

import cv2

logger = logging.getLogger("webcam_mcp")


class WebcamError(Exception):
    """Exception raised for webcam-related errors."""

    pass


class WebcamCapture:
    """Webcam capture utility. NOT a context manager itself.

    Each capture method (capture_photo, capture_video_frames) manages
    its own cv2.VideoCapture lifecycle internally.
    """

    def __init__(self, camera_index: int = 0):
        """Initialize webcam capture with camera index.

        Args:
            camera_index: Camera device index (default: 0 for primary camera)
        """
        self.camera_index = camera_index

    def _open_camera(self) -> cv2.VideoCapture:
        """Open camera with cross-platform backend fallback.

        Uses self.camera_index set in __init__.

        Returns:
            Opened cv2.VideoCapture instance

        Raises:
            WebcamError: If camera cannot be opened
        """
        # Try default backend first
        cap = cv2.VideoCapture(self.camera_index)
        if cap.isOpened():
            return cap

        # Platform-specific fallbacks
        system = platform.system()
        backends = {
            "Darwin": cv2.CAP_AVFOUNDATION,  # macOS
            "Windows": cv2.CAP_DSHOW,  # Windows DirectShow
            "Linux": cv2.CAP_V4L2,  # Linux Video4Linux2
        }

        if system in backends:
            cap = cv2.VideoCapture(self.camera_index, backends[system])
            if cap.isOpened():
                return cap

        raise WebcamError(
            f"Camera {self.camera_index} unavailable. Check:\n"
            "- Camera permissions in System Settings\n"
            "- No other app is using the camera\n"
            "- Camera index is correct (try --camera-index 1)"
        )

    def _set_resolution(self, cap: cv2.VideoCapture, width: int, height: int) -> tuple[int, int]:
        """Set resolution and return actual resolution achieved.

        Args:
            cap: Opened VideoCapture instance
            width: Desired width in pixels
            height: Desired height in pixels

        Returns:
            Tuple of (actual_width, actual_height) achieved
        """
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        if (actual_w, actual_h) != (width, height):
            logger.warning(
                f"Requested resolution {width}x{height}, but camera provided {actual_w}x{actual_h}"
            )
        return actual_w, actual_h

    def _encode_jpeg(self, frame, quality: int) -> bytes:
        """Encode frame as JPEG with specified quality (0-100).

        Args:
            frame: OpenCV frame (numpy array)
            quality: JPEG quality (0-100, higher is better)

        Returns:
            JPEG-encoded bytes

        Raises:
            WebcamError: If encoding fails
        """
        success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if not success:
            raise WebcamError("Failed to encode JPEG")
        return buffer.tobytes()

    def capture_photo(self, width: int = 1920, height: int = 1080, quality: int = 75) -> bytes:
        """Capture a single photo. All params have defaults.

        Args:
            width: Photo width in pixels (default: 1920)
            height: Photo height in pixels (default: 1080)
            quality: JPEG quality 0-100 (default: 75)

        Returns:
            JPEG-encoded photo as bytes

        Raises:
            WebcamError: If capture fails
        """
        cap = self._open_camera()
        try:
            self._set_resolution(cap, width, height)
            # Warm-up for photo (5 frames - less than video)
            for _ in range(5):
                cap.read()
            ret, frame = cap.read()
            if not ret:
                raise WebcamError("Failed to capture frame")
            return self._encode_jpeg(frame, quality)
        finally:
            cap.release()  # Always release camera

    def capture_video_frames(
        self,
        duration_seconds: float,
        width: int = 640,
        height: int = 480,
        max_frames: int = 50,
        quality: int = 75,
    ) -> list[bytes]:
        """Capture video frames over specified duration.

        Frames are sampled evenly over the duration. Warm-up frames are
        discarded BEFORE timing starts, so duration is actual capture time.

        Args:
            duration_seconds: Capture duration in seconds (1.0 to 60.0)
            width: Frame width in pixels (default: 640)
            height: Frame height in pixels (default: 480)
            max_frames: Maximum frames to capture (default: 50)
            quality: JPEG quality 0-100 (default: 75)

        Returns:
            List of JPEG-encoded frames as bytes

        Raises:
            WebcamError: If duration is invalid or capture fails
        """
        # Validate duration first
        if duration_seconds < 1.0:
            raise WebcamError(f"Duration must be >= 1.0 seconds, got {duration_seconds}")
        if duration_seconds > 60.0:
            raise WebcamError(f"Duration must be <= 60.0 seconds, got {duration_seconds}")

        cap = self._open_camera()  # Uses self.camera_index
        try:
            self._set_resolution(cap, width, height)

            # Warm-up: discard 10 frames BEFORE starting the timer
            for _ in range(10):
                cap.read()

            # NOW start timing - warm-up doesn't count toward duration
            start_time = time.time()
            frames = []
            interval = duration_seconds / max_frames
            next_capture = start_time

            while (time.time() - start_time) < duration_seconds and len(frames) < max_frames:
                if time.time() >= next_capture:
                    ret, frame = cap.read()
                    if ret:
                        frames.append(self._encode_jpeg(frame, quality))
                        next_capture += interval
                else:
                    time.sleep(0.01)  # Avoid busy-waiting

            return frames
        finally:
            cap.release()
