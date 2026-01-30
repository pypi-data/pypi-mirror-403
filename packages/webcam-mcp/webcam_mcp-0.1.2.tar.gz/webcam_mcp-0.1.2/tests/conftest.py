"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def mock_camera_frame():
    """Provide a mock camera frame (480x640 RGB)."""
    import numpy as np

    return np.zeros((480, 640, 3), dtype=np.uint8)
