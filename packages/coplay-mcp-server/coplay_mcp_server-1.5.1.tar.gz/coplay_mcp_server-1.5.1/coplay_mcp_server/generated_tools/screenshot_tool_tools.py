"""Generated MCP tools from screenshot_tool_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def capture_ui_canvas(
    canvasPath: Annotated[
        str | None,
        Field(
            description="""Optional path to the canvas in the scene hierarchy. If provided, the specified Canvas will be captured. If empty or null, the first Canvas found in the scene will be captured."""
        ),
    ] = None,
) -> Any:
    """Captures a screenshot of a UI Canvas. Use this tool to capture and analyze Unity UI Canvases in the Scene hierarchy after generating UI for validation."""
    try:
        logger.debug(f"Executing capture_ui_canvas with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if canvasPath is not None:
            params['canvasPath'] = str(canvasPath)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('capture_ui_canvas', params)
        logger.debug(f"capture_ui_canvas completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute capture_ui_canvas: {e}")
        raise RuntimeError(f"Tool execution failed for capture_ui_canvas: {e}")


async def capture_scene_object(
    gameObjectPath: Annotated[
        str | None,
        Field(
            description="""Optional path to a GameObject in the scene hierarchy to frame (e.g., '/Root/Character/Weapon'). If provided, the camera will be positioned to frame this object. If empty or null, captures from the current SceneView camera position."""
        ),
    ] = None,
) -> Any:
    """Captures a screenshot of the scene object. If gameObjectPath is provided, frames the specified GameObject and its children. Otherwise, uses the current SceneView camera position, rotation, and field of view. Use this tool to inspect or analyze the visual appearance of objects after making visual changes to a scene or prefab."""
    try:
        logger.debug(f"Executing capture_scene_object with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if gameObjectPath is not None:
            params['gameObjectPath'] = str(gameObjectPath)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('capture_scene_object', params)
        logger.debug(f"capture_scene_object completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute capture_scene_object: {e}")
        raise RuntimeError(f"Tool execution failed for capture_scene_object: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from screenshot_tool_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register capture_ui_canvas
    mcp.tool()(capture_ui_canvas)
    # Register capture_scene_object
    mcp.tool()(capture_scene_object)
