"""MCP server for SVG diagram generation."""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("mcp-svg-animator")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available SVG generation tools."""
    return [
        Tool(
            name="create_svg_from_yaml",
            description="""Create an animated SVG diagram from a YAML specification.

Supports shapes: circle, rectangle, line, text, path, group
Supports animations: attribute animations and transform animations (rotate, translate, scale)
Supports reusable definitions and library imports.

Example YAML:
```yaml
width: 400
height: 300
definitions:
  my_circle:
    type: circle
    r: 25
    fill: red
elements:
  - use: my_circle
    cx: 100
    cy: 150
  - type: group
    transform: translate(200, 150)
    transform_animations:
      - type: rotate
        values: "0;360"
        dur: 2s
        repeatCount: indefinite
    elements:
      - type: rectangle
        x: -25
        y: -25
        width: 50
        height: 50
        fill: blue
```""",
            inputSchema={
                "type": "object",
                "properties": {
                    "yaml_spec": {
                        "type": "string",
                        "description": "YAML specification for the SVG diagram",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional path to write the SVG file. If provided, writes to file and returns confirmation instead of SVG content.",
                    },
                    "png_path": {
                        "type": "string",
                        "description": "Optional path to write a PNG render of the SVG. Useful for previewing static images.",
                    },
                },
                "required": ["yaml_spec"],
            },
        ),
        Tool(
            name="create_animation_video",
            description="""Create a video file from an SVG animation.

Takes an SVG with SMIL animations and records it to a .webm video file.
The SVG can be created using create_svg_from_yaml first.

Example usage:
1. First create an SVG with animations using create_svg_from_yaml
2. Then pass the SVG content to this tool to create a video""",
            inputSchema={
                "type": "object",
                "properties": {
                    "svg_content": {
                        "type": "string",
                        "description": "SVG content with animations",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path where the .webm video will be saved",
                    },
                    "duration_ms": {
                        "type": "number",
                        "description": "Duration of the video in milliseconds (default: 3000)",
                        "default": 3000,
                    },
                },
                "required": ["svg_content", "output_path"],
            },
        ),
    ]


def _check_write_permission(file_path: str, file_type: str) -> None:
    """Check if writing to a path is allowed, raise PermissionError if not."""
    from .config import is_path_allowed

    if not is_path_allowed(file_path, file_type):
        raise PermissionError(
            f"Writing {file_type} to {file_path} is not allowed. "
            f"Configure allowed paths in ~/.config/mcp-svg-animator/config.yaml"
        )


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls for SVG generation."""
    if name == "create_svg_from_yaml":
        from pathlib import Path

        from .generators.yaml_loader import create_diagram_from_yaml

        yaml_spec = arguments.get("yaml_spec", "")
        output_path = arguments.get("output_path")
        png_path = arguments.get("png_path")

        # Check permissions before generating content
        if output_path:
            _check_write_permission(output_path, "svg")
        if png_path:
            _check_write_permission(png_path, "png")

        svg_content = create_diagram_from_yaml(yaml_spec)

        messages = []

        if output_path:
            Path(output_path).write_text(svg_content)
            messages.append(f"SVG written to {output_path}")

        if png_path:
            import asyncio

            from .generators.png_generator import create_png_from_svg

            # Run sync Playwright code in a separate thread to avoid async conflict
            await asyncio.to_thread(create_png_from_svg, svg_content, png_path)
            messages.append(f"PNG written to {png_path}")

        if messages:
            return [TextContent(type="text", text="\n".join(messages))]

        return [TextContent(type="text", text=svg_content)]

    if name == "create_animation_video":
        import asyncio

        from .generators.video_generator import create_video_from_svg

        svg_content = arguments.get("svg_content", "")
        output_path = arguments.get("output_path", "animation.webm")
        duration_ms = int(arguments.get("duration_ms", 3000))

        _check_write_permission(output_path, "webm")

        # Run sync Playwright code in a separate thread to avoid async conflict
        await asyncio.to_thread(
            create_video_from_svg, svg_content, output_path, duration_ms=duration_ms
        )
        return [TextContent(type="text", text=f"Video saved to {output_path}")]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
