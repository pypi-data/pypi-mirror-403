"""Generated MCP tools from asset_functions_schema.json"""

import logging
from typing import Annotated, Optional, Any, Dict, Literal
from pydantic import Field
from fastmcp import FastMCP
from ..unity_client import UnityRpcClient

logger = logging.getLogger(__name__)

# Global references to be set by register_tools
_mcp: Optional[FastMCP] = None
_unity_client: Optional[UnityRpcClient] = None


async def list_all_prefabs_with_bounding_boxes(
    path: Annotated[
        str | None,
        Field(
            description="""Optional. Subdirectory under Assets to search for prefabs. Defaults to 'Assets' (searches all prefabs in the project)."""
        ),
    ] = None,
    limit: Annotated[
        int | None,
        Field(
            description="""Optional. Maximum number of prefabs to return. Defaults to 200."""
        ),
    ] = None,
) -> Any:
    """Lists all prefab files under the Assets folder with their bounding box sizes. Returns a plain text list with each line containing the prefab path followed by its AABB size coordinates."""
    try:
        logger.debug(f"Executing list_all_prefabs_with_bounding_boxes with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if path is not None:
            params['path'] = str(path)
        if limit is not None:
            params['limit'] = str(limit)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('list_all_prefabs_with_bounding_boxes', params)
        logger.debug(f"list_all_prefabs_with_bounding_boxes completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute list_all_prefabs_with_bounding_boxes: {e}")
        raise RuntimeError(f"Tool execution failed for list_all_prefabs_with_bounding_boxes: {e}")


async def place_asset_in_scene(
    asset_path: Annotated[
        str,
        Field(
            description="""Path to the asset within the Assets folder (e.g., 'Models/Chair.fbx' or 'Prefabs/Player.prefab')."""
        ),
    ],
    on_top_of: Annotated[
        str,
        Field(
            description="""Hierarchy path to the game object on top of which the new asset should be placed. e.g. 'root/environment/terrain'"""
        ),
    ],
    instance_name: Annotated[
        str | None,
        Field(
            description="""Optional name for the instantiated object in the scene. If not provided, uses the asset's name."""
        ),
    ] = None,
    position: Annotated[
        str | None,
        Field(
            description="""Optional comma-separated position coordinates (e.g., 'x,z'). Defaults to '0,0'. The y coordinate is determined by the height of the asset on top of which it is placed."""
        ),
    ] = None,
) -> Any:
    """Adds an existing asset from the Assets folder into the current scene."""
    try:
        logger.debug(f"Executing place_asset_in_scene with parameters: {locals()}")

        # Prepare parameters for Unity RPC call
        params = {}
        if asset_path is not None:
            params['asset_path'] = str(asset_path)
        if on_top_of is not None:
            params['on_top_of'] = str(on_top_of)
        if instance_name is not None:
            params['instance_name'] = str(instance_name)
        if position is not None:
            params['position'] = str(position)

        # Execute Unity RPC call
        result = await _unity_client.execute_request('place_asset_in_scene', params)
        logger.debug(f"place_asset_in_scene completed successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to execute place_asset_in_scene: {e}")
        raise RuntimeError(f"Tool execution failed for place_asset_in_scene: {e}")


def register_tools(mcp: FastMCP, unity_client: UnityRpcClient) -> None:
    """Register all tools from asset_functions_schema with the MCP server."""
    global _mcp, _unity_client
    _mcp = mcp
    _unity_client = unity_client

    # Register list_all_prefabs_with_bounding_boxes
    mcp.tool()(list_all_prefabs_with_bounding_boxes)
    # Register place_asset_in_scene
    mcp.tool()(place_asset_in_scene)
