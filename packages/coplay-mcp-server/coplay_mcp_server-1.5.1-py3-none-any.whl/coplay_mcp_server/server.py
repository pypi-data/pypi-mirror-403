"""Main entry point for Coplay MCP Server using FastMCP."""

import logging
import os
import sys
import importlib
from pathlib import Path

from typing import Any, Optional, Annotated

from pydantic import Field
from coplay_mcp_server.process_discovery import discover_unity_project_roots
from fastmcp import FastMCP

from coplay_mcp_server.unity_client import UnityRpcClient

# Set binary mode for stdin/stdout/stderr on Windows
# This is necessary for proper MCP protocol communication on Windows
if sys.platform == 'win32':
    import msvcrt
    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stderr.fileno(), os.O_BINARY)


def setup_logging() -> None:
    """Set up logging configuration with support for file logging and configurable log level via environment variables.
    
    Environment variables:
    - COPLAY_LOG_FILE: Path to log file (if set, logs will be written to this file)
    - COPLAY_LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Defaults to WARNING.
    """
    
    # Get log level from environment variable, default to WARNING
    log_level_str = os.getenv("COPLAY_LOG_LEVEL", "WARNING").upper()
    log_level = getattr(logging, log_level_str, logging.WARNING)
    
    # Get log file path from environment variable
    log_file = os.getenv("COPLAY_LOG_FILE")
    
    # Create handlers list
    handlers = [
        # Log to stderr (visible to MCP client)
        logging.StreamHandler(sys.stderr),
    ]
    
    # Add file handler if log file is specified
    if log_file:
        try:
            # Create directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            )
            handlers.append(file_handler)
            
            # Log to stderr that file logging is enabled
            sys.stderr.write(f"File logging enabled: {log_file}\n")
        except Exception as e:
            sys.stderr.write(f"Failed to set up file logging to {log_file}: {e}\n")
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    # Set specific log levels for noisy libraries
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


setup_logging()


# Initialize FastMCP server
mcp = FastMCP(name="coplay-mcp-server")

# Global Unity client instance
unity_client = UnityRpcClient()

logger = logging.getLogger(__name__)


def load_tool_modules() -> list:
    """Dynamically discover and load all tool modules from generated_tools directory.
    
    Returns:
        List of loaded tool modules that have a register_tools function.
    """
    generated_tools_dir = Path(__file__).parent / "generated_tools"
    tool_modules = []
    
    # Find all *_tools.py files in the generated_tools directory
    for tool_file in generated_tools_dir.glob("*_tools.py"):
        module_name = tool_file.stem  # Get filename without extension
        try:
            # Dynamically import the module
            module = importlib.import_module(f"coplay_mcp_server.generated_tools.{module_name}")
            
            # Verify the module has a register_tools function
            if hasattr(module, "register_tools"):
                tool_modules.append(module)
                logger.debug(f"Loaded tool module: {module_name}")
            else:
                logger.warning(f"Module {module_name} does not have a register_tools function, skipping")
        except Exception as e:
            logger.error(f"Failed to load tool module {module_name}: {e}")
            # Continue loading other modules even if one fails
            continue
    
    logger.info(f"Discovered {len(tool_modules)} tool modules")
    return tool_modules


@mcp.tool()
async def set_unity_project_root(
    unity_project_root: str
) -> str:
    """Set the Unity project root path for the MCP server instance. This tool should be called before using any other Unity tools."""
    try:
        logger.info(f"Setting Unity project root to: {unity_project_root}")

        if not unity_project_root or not unity_project_root.strip():
            raise ValueError("Unity project root cannot be empty")

        # Set the Unity project root in the RPC client
        unity_client.set_unity_project_root(unity_project_root)

        result = f"Unity project root set to: {unity_project_root}"
        logger.info("Unity project root set successfully")
        return result

    except Exception as e:
        logger.error(f"Failed to set Unity project root: {e}")
        raise


@mcp.tool()
async def list_unity_project_roots() -> Any:
    """List all project roots of currently open Unity instances. This tool discovers all running Unity Editor instances and returns their project root directories."""
    try:
        logger.info("Discovering Unity project roots...")

        project_roots = discover_unity_project_roots()
        return {
            "count": len(project_roots),
            "projectRoots": [
                {
                    "projectRoot": root,
                    "projectName": Path(root).name,
                }
                for root in project_roots
            ],
        }
    except Exception as e:
        logger.error(f"Failed to list Unity project roots: {e}")
        raise


@mcp.tool()
async def create_coplay_task(
    prompt: Annotated[
        str,
        Field(description="The task prompt to submit"),
    ],
    file_paths: Annotated[
        Optional[str],
        Field(description="Optional comma-separated file paths to attach as context"),
    ] = None,
    model: Annotated[
        Optional[str],
        Field(description="Optional AI model to use for this task"),
    ] = None,
) -> Any:
    """Creates a new task in the Unity Editor with the specified prompt and optional file attachments.

    Args:
        prompt: The task prompt to submit
        file_paths: Optional comma-separated file paths to attach as context
        model: Optional AI model to use for this task
    """
    try:
        logger.info(f"Creating task with prompt: {prompt[:10000]}...")

        params = {"prompt": prompt}
        if file_paths:
            params["file_paths"] = file_paths
        if model:
            params["model"] = model

        # Always wait for completion
        params["wait_for_completion"] = "true"

        # Use a longer timeout (610 seconds) to accommodate Unity's default 600-second timeout
        result = await unity_client.execute_request(
            "create_task", params, timeout=610.0
        )
        return result
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise


def main():
    """Initialize MCP server with generated tools and start serving."""
    try:
        logger.info("Initializing Coplay MCP Server...")

        # Dynamically load all tool modules
        tool_modules = load_tool_modules()

        # Register all discovered tool modules
        total_tools = 0
        for module in tool_modules:
            try:
                module.register_tools(mcp, unity_client)
                # Count tools by checking for functions with @mcp.tool decorator
                module_tools = [
                    name
                    for name in dir(module)
                    if not name.startswith("_") and name != "register_tools"
                ]
                total_tools += len(module_tools)
                logger.info(f"Registered tools from {module.__name__}")
            except Exception as e:
                logger.error(f"Failed to register tools from {module.__name__}: {e}")
                # Continue registering other modules even if one fails
                continue

        logger.info(f"Total generated tools registered: {total_tools}")
        logger.info("Coplay MCP Server initialized successfully")

        # Start the MCP server
        mcp.run()

    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {e}")
        raise


if __name__ == "__main__":
    main()
