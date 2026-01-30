from dataclasses import dataclass


@dataclass
class ServerConfig:
    """Configuration passed from CLI to server to camera."""

    camera_index: int = 0
    photo_width: int = 1920
    photo_height: int = 1080
    video_width: int = 640
    video_height: int = 480
    jpeg_quality: int = 90
    host: str = "0.0.0.0"
    port: int = 8000
