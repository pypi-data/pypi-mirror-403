"""Tests for MCP server tool registration and functionality."""

import pytest

from webcam_mcp.config import ServerConfig
from webcam_mcp.server import create_server


@pytest.mark.asyncio
async def test_tool_registration():
    config = ServerConfig()
    server = create_server(config)

    tools = await server.list_tools()
    tool_names = [tool.name for tool in tools]

    assert "take_photo" in tool_names
    assert "record_video" in tool_names


@pytest.mark.asyncio
async def test_tool_metadata():
    config = ServerConfig()
    server = create_server(config)

    tools = await server.list_tools()
    tool_dict = {tool.name: tool for tool in tools}

    assert "take_photo" in tool_dict
    take_photo_tool = tool_dict["take_photo"]
    assert take_photo_tool.description is not None
    assert "photo" in take_photo_tool.description.lower()

    assert "record_video" in tool_dict
    record_video_tool = tool_dict["record_video"]
    assert record_video_tool.description is not None
    assert "video" in record_video_tool.description.lower()


def test_server_config_applied():
    config = ServerConfig(
        host="127.0.0.1", port=9000, camera_index=1, photo_width=1280, photo_height=720
    )
    server = create_server(config)

    assert server.settings.host == "127.0.0.1"
    assert server.settings.port == 9000
