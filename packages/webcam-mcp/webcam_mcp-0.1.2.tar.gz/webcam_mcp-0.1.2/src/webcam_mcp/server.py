"""FastMCP server for webcam capture operations.

This module provides the MCP server implementation with tools for:
- take_photo(): Capture a single high-resolution photo
- record_video(duration_seconds): Record video frames as JPEG images

The server is created dynamically via create_server() to allow runtime
configuration of host/port and camera settings.
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image

from webcam_mcp.camera import WebcamCapture
from webcam_mcp.config import ServerConfig

# Module-level config (set by create_server before tools are called)
_config: ServerConfig | None = None

# FastMCP instance created dynamically in create_server() to allow host/port config
_mcp: FastMCP | None = None


def create_server(config: ServerConfig) -> FastMCP:
    """Create and configure the MCP server with given config.

    Args:
        config: Server configuration including host, port, and camera settings

    Returns:
        Configured FastMCP server instance ready to run

    Example:
        >>> from webcam_mcp.config import ServerConfig
        >>> from webcam_mcp.server import create_server
        >>> config = ServerConfig(host='0.0.0.0', port=8000)
        >>> server = create_server(config)
        >>> server.run(transport='sse')
    """
    global _config, _mcp
    _config = config

    # Create FastMCP with host/port from config (CRITICAL: set in constructor)
    _mcp = FastMCP("Webcam MCP Server", host=config.host, port=config.port)

    # Register tools on the new instance
    @_mcp.tool()
    def take_photo() -> Image:
        """Capture a high-resolution photo from the webcam.

        Uses server configuration for resolution and quality settings.
        Returns JPEG image data that can be displayed or processed by LLMs.

        Returns:
            Image object containing JPEG data

        Raises:
            WebcamError: If camera access fails or capture errors occur
        """
        assert _config is not None
        cam = WebcamCapture(_config.camera_index)
        jpeg_bytes = cam.capture_photo(
            width=_config.photo_width, height=_config.photo_height, quality=_config.jpeg_quality
        )
        return Image(data=jpeg_bytes, format="jpeg")

    @_mcp.tool()
    def record_video(duration_seconds: float = 5.0):
        """Record video from webcam. Returns up to 50 frames as JPEG images.

        Captures video frames at the camera's native framerate, then samples
        up to 50 frames evenly distributed across the duration.

        Args:
            duration_seconds: How long to record (default: 5.0 seconds)

        Returns:
            List of Image objects, each containing a JPEG frame

        Raises:
            WebcamError: If camera access fails or capture errors occur
        """
        assert _config is not None
        cam = WebcamCapture(_config.camera_index)
        frames = cam.capture_video_frames(
            duration_seconds=duration_seconds,
            width=_config.video_width,
            height=_config.video_height,
            quality=_config.jpeg_quality,
        )
        return [Image(data=frame, format="jpeg") for frame in frames]

    return _mcp
