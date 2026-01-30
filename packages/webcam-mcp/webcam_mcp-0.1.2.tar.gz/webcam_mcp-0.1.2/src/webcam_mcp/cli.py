"""Command-line interface for Webcam MCP server."""

import argparse

from webcam_mcp import __version__
from webcam_mcp.config import ServerConfig
from webcam_mcp.server import create_server


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of arguments to parse (defaults to sys.argv[1:])

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        prog="webcam-mcp",
        description="MCP server for webcam access",
    )

    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port (default: 8000)",
    )

    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Webcam index (default: 0)",
    )

    parser.add_argument(
        "--photo-width",
        type=int,
        default=1920,
        help="Default photo width (default: 1920)",
    )

    parser.add_argument(
        "--photo-height",
        type=int,
        default=1080,
        help="Default photo height (default: 1080)",
    )

    parser.add_argument(
        "--video-width",
        type=int,
        default=640,
        help="Default video width (default: 640)",
    )

    parser.add_argument(
        "--video-height",
        type=int,
        default=480,
        help="Default video height (default: 480)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"webcam-mcp {__version__}",
    )

    return parser.parse_args(args)


def main(args: list[str] | None = None) -> None:
    """Main entry point for the CLI.

    Parses arguments, creates server configuration, and runs the server.

    Args:
        args: List of arguments to parse (defaults to sys.argv[1:])
    """
    parsed_args = parse_args(args)

    config = ServerConfig(
        camera_index=parsed_args.camera_index,
        photo_width=parsed_args.photo_width,
        photo_height=parsed_args.photo_height,
        video_width=parsed_args.video_width,
        video_height=parsed_args.video_height,
        host=parsed_args.host,
        port=parsed_args.port,
    )

    server = create_server(config)
    server.run(transport="sse")


if __name__ == "__main__":
    main()
