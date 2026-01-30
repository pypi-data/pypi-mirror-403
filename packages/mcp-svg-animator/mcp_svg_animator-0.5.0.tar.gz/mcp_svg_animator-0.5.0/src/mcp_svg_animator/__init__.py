"""Mcp Svg Animator - A Python project following TDD principles."""

__version__ = "0.5.0"

# Direct Python API for SVG generation (no MCP server required)
from .api import (
    yaml_to_svg,
    yaml_to_svg_file,
    yaml_file_to_svg,
    yaml_file_to_svg_file,
    dict_to_svg,
    dict_to_svg_file,
    yaml_to_png,
    yaml_to_video,
)

__all__ = [
    "yaml_to_svg",
    "yaml_to_svg_file",
    "yaml_file_to_svg",
    "yaml_file_to_svg_file",
    "dict_to_svg",
    "dict_to_svg_file",
    "yaml_to_png",
    "yaml_to_video",
]