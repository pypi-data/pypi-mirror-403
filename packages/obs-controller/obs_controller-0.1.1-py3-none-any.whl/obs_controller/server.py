"""FastMCP server for OBS Controller."""

from fastmcp import FastMCP

from .tools import (
    filters,
    general,
    inputs,
    media,
    outputs,
    recording,
    scene_items,
    scenes,
    sources,
    streaming,
    transitions,
    ui,
)

mcp = FastMCP(
    "OBS Controller",
    instructions="MCP server for controlling OBS Studio via WebSocket API",
)

# Register all tools
general.register_tools(mcp)
scenes.register_tools(mcp)
inputs.register_tools(mcp)
streaming.register_tools(mcp)
recording.register_tools(mcp)
transitions.register_tools(mcp)
filters.register_tools(mcp)
scene_items.register_tools(mcp)
outputs.register_tools(mcp)
media.register_tools(mcp)
ui.register_tools(mcp)
sources.register_tools(mcp)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
