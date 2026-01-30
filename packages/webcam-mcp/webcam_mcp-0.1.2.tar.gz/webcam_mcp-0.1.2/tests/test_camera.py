"""Tests for webcam capture functionality."""

import numpy as np
import pytest

from webcam_mcp.camera import WebcamCapture, WebcamError


def test_camera_init():
    cam = WebcamCapture(camera_index=0)
    assert cam.camera_index == 0

    cam = WebcamCapture(camera_index=1)
    assert cam.camera_index == 1


def test_duration_validation():
    cam = WebcamCapture(0)

    with pytest.raises(WebcamError, match="Duration must be >= 1.0 seconds"):
        cam.capture_video_frames(0.5)

    with pytest.raises(WebcamError, match="Duration must be <= 60.0 seconds"):
        cam.capture_video_frames(61.0)


def test_frame_distribution(mocker):
    mock_cap = mocker.MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mocker.patch("cv2.VideoCapture", return_value=mock_cap)

    fake_time = [0.0]

    def mock_time():
        return fake_time[0]

    def mock_sleep(seconds):
        fake_time[0] += seconds

    mocker.patch("time.time", side_effect=mock_time)
    mocker.patch("time.sleep", side_effect=mock_sleep)

    def read_with_time_advance():
        fake_time[0] += 0.033
        return (True, np.zeros((480, 640, 3), dtype=np.uint8))

    mock_cap.read.side_effect = read_with_time_advance

    cam = WebcamCapture(0)
    frames = cam.capture_video_frames(5.0)
    assert len(frames) == 50


def test_photo_capture_mocked(mocker):
    mock_cap = mocker.MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((1080, 1920, 3), dtype=np.uint8))
    mocker.patch("cv2.VideoCapture", return_value=mock_cap)

    mocker.patch("cv2.imencode", return_value=(True, np.array([0xFF, 0xD8, 0xFF])))

    cam = WebcamCapture(0)
    jpeg_bytes = cam.capture_photo(width=1920, height=1080, quality=75)

    assert isinstance(jpeg_bytes, bytes)
    assert len(jpeg_bytes) > 0


def test_camera_open_failure(mocker):
    mock_cap = mocker.MagicMock()
    mock_cap.isOpened.return_value = False
    mocker.patch("cv2.VideoCapture", return_value=mock_cap)

    cam = WebcamCapture(0)

    with pytest.raises(WebcamError, match="Camera 0 unavailable"):
        cam.capture_photo()


def test_jpeg_encoding_failure(mocker):
    mock_cap = mocker.MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mocker.patch("cv2.VideoCapture", return_value=mock_cap)

    mocker.patch("cv2.imencode", return_value=(False, None))

    cam = WebcamCapture(0)

    with pytest.raises(WebcamError, match="Failed to encode JPEG"):
        cam.capture_photo()
