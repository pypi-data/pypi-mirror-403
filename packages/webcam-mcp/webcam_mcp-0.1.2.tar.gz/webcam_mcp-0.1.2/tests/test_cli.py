"""Tests for CLI argument parsing."""

import pytest

from webcam_mcp.cli import parse_args


def test_cli_defaults():
    args = parse_args([])

    assert args.host == "0.0.0.0"
    assert args.port == 8000
    assert args.camera_index == 0
    assert args.photo_width == 1920
    assert args.photo_height == 1080
    assert args.video_width == 640
    assert args.video_height == 480


def test_cli_custom_host_port():
    args = parse_args(["--host", "127.0.0.1", "--port", "9000"])

    assert args.host == "127.0.0.1"
    assert args.port == 9000


def test_cli_custom_camera():
    args = parse_args(["--camera-index", "1"])

    assert args.camera_index == 1


def test_cli_custom_photo_resolution():
    args = parse_args(["--photo-width", "1280", "--photo-height", "720"])

    assert args.photo_width == 1280
    assert args.photo_height == 720


def test_cli_custom_video_resolution():
    args = parse_args(["--video-width", "1280", "--video-height", "720"])

    assert args.video_width == 1280
    assert args.video_height == 720


def test_cli_version():
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--version"])

    assert exc_info.value.code == 0


def test_cli_help():
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--help"])

    assert exc_info.value.code == 0
