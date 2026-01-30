"""Direct Python API for SVG generation.

This module provides simple functions for generating SVG diagrams from YAML
specifications, without requiring the MCP server. Use this when you want to
call the SVG generation code directly from another Python program.

Example usage:
    from mcp_svg_animator.api import yaml_to_svg, yaml_to_svg_file

    # Generate SVG content from YAML string
    yaml_spec = '''
    width: 400
    height: 300
    elements:
      - type: circle
        cx: 200
        cy: 150
        r: 50
        fill: blue
    '''
    svg_content = yaml_to_svg(yaml_spec)

    # Or save directly to file
    yaml_to_svg_file(yaml_spec, "output.svg")

    # Load YAML from file and generate SVG
    from mcp_svg_animator.api import yaml_file_to_svg, yaml_file_to_svg_file

    svg_content = yaml_file_to_svg("diagram.yaml")
    yaml_file_to_svg_file("diagram.yaml", "output.svg")
"""

from pathlib import Path
from typing import Union

from .generators.yaml_loader import create_diagram_from_yaml
from .generators.animations import create_animated_diagram


def yaml_to_svg(yaml_spec: str) -> str:
    """Generate SVG content from a YAML specification string.

    Args:
        yaml_spec: YAML string containing the diagram specification.
            Should include:
            - width: Canvas width (default 400)
            - height: Canvas height (default 300)
            - definitions: Optional dict of reusable element definitions
            - libraries: Optional list of library file paths to import
            - elements: List of shape specifications

    Returns:
        SVG content as a string.

    Raises:
        ValueError: If the YAML contains invalid element specifications.
        yaml.YAMLError: If the YAML is malformed.

    Example:
        >>> svg = yaml_to_svg('''
        ... width: 200
        ... height: 200
        ... elements:
        ...   - type: circle
        ...     cx: 100
        ...     cy: 100
        ...     r: 50
        ...     fill: red
        ... ''')
    """
    return create_diagram_from_yaml(yaml_spec)


def yaml_to_svg_file(
    yaml_spec: str,
    output_path: Union[str, Path],
) -> Path:
    """Generate SVG from YAML and save to a file.

    Args:
        yaml_spec: YAML string containing the diagram specification.
        output_path: Path where the SVG file will be written.

    Returns:
        Path object pointing to the created SVG file.

    Raises:
        ValueError: If the YAML contains invalid element specifications.
        yaml.YAMLError: If the YAML is malformed.
        OSError: If the file cannot be written.

    Example:
        >>> path = yaml_to_svg_file('''
        ... width: 200
        ... height: 200
        ... elements:
        ...   - type: circle
        ...     cx: 100
        ...     cy: 100
        ...     r: 50
        ...     fill: blue
        ... ''', "circle.svg")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    svg_content = create_diagram_from_yaml(yaml_spec)
    output_path.write_text(svg_content)
    return output_path


def yaml_file_to_svg(yaml_path: Union[str, Path]) -> str:
    """Load a YAML file and generate SVG content.

    Args:
        yaml_path: Path to the YAML specification file.

    Returns:
        SVG content as a string.

    Raises:
        FileNotFoundError: If the YAML file doesn't exist.
        ValueError: If the YAML contains invalid element specifications.
        yaml.YAMLError: If the YAML is malformed.

    Example:
        >>> svg = yaml_file_to_svg("diagram.yaml")
    """
    yaml_path = Path(yaml_path)
    yaml_content = yaml_path.read_text()
    return create_diagram_from_yaml(yaml_content)


def yaml_file_to_svg_file(
    yaml_path: Union[str, Path],
    output_path: Union[str, Path],
) -> Path:
    """Load a YAML file and save the generated SVG to a file.

    Args:
        yaml_path: Path to the YAML specification file.
        output_path: Path where the SVG file will be written.

    Returns:
        Path object pointing to the created SVG file.

    Raises:
        FileNotFoundError: If the YAML file doesn't exist.
        ValueError: If the YAML contains invalid element specifications.
        yaml.YAMLError: If the YAML is malformed.
        OSError: If the file cannot be written.

    Example:
        >>> path = yaml_file_to_svg_file("diagram.yaml", "output.svg")
    """
    yaml_path = Path(yaml_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_content = yaml_path.read_text()
    svg_content = create_diagram_from_yaml(yaml_content)
    output_path.write_text(svg_content)
    return output_path


def dict_to_svg(spec: dict) -> str:
    """Generate SVG content from a Python dictionary specification.

    This is useful when you want to build the specification programmatically
    rather than from a YAML string.

    Args:
        spec: Dictionary containing the diagram specification.
            Should include:
            - width: Canvas width (default 400)
            - height: Canvas height (default 300)
            - elements: List of shape specifications

    Returns:
        SVG content as a string.

    Example:
        >>> svg = dict_to_svg({
        ...     "width": 200,
        ...     "height": 200,
        ...     "elements": [
        ...         {"type": "circle", "cx": 100, "cy": 100, "r": 50, "fill": "green"}
        ...     ]
        ... })
    """
    return create_animated_diagram(spec)


def dict_to_svg_file(
    spec: dict,
    output_path: Union[str, Path],
) -> Path:
    """Generate SVG from a dictionary and save to a file.

    Args:
        spec: Dictionary containing the diagram specification.
        output_path: Path where the SVG file will be written.

    Returns:
        Path object pointing to the created SVG file.

    Example:
        >>> path = dict_to_svg_file({
        ...     "width": 200,
        ...     "height": 200,
        ...     "elements": [
        ...         {"type": "circle", "cx": 100, "cy": 100, "r": 50, "fill": "purple"}
        ...     ]
        ... }, "circle.svg")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    svg_content = create_animated_diagram(spec)
    output_path.write_text(svg_content)
    return output_path


def yaml_to_png(
    yaml_spec: str,
    output_path: Union[str, Path],
    width: int | None = None,
    height: int | None = None,
) -> Path:
    """Generate a PNG image from a YAML specification.

    Uses Playwright to render the SVG in a headless browser.
    Requires Playwright to be installed.

    Args:
        yaml_spec: YAML string containing the diagram specification.
        output_path: Path where the PNG file will be written.
        width: Image width (defaults to SVG width or 800).
        height: Image height (defaults to SVG height or 600).

    Returns:
        Path object pointing to the created PNG file.

    Example:
        >>> path = yaml_to_png('''
        ... width: 200
        ... height: 200
        ... elements:
        ...   - type: circle
        ...     cx: 100
        ...     cy: 100
        ...     r: 50
        ...     fill: red
        ... ''', "circle.png")
    """
    from .generators.png_generator import create_png_from_svg

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    svg_content = create_diagram_from_yaml(yaml_spec)
    create_png_from_svg(svg_content, str(output_path), width=width, height=height)
    return output_path


def yaml_to_video(
    yaml_spec: str,
    output_path: Union[str, Path],
    duration_ms: int = 3000,
) -> Path:
    """Generate a video from an animated YAML specification.

    Uses Playwright to render the SVG animation and record it.
    Requires Playwright to be installed.

    Args:
        yaml_spec: YAML string containing the animated diagram specification.
        output_path: Path where the .webm video will be written.
        duration_ms: Duration of the video in milliseconds (default 3000).

    Returns:
        Path object pointing to the created video file.

    Example:
        >>> path = yaml_to_video('''
        ... width: 200
        ... height: 200
        ... elements:
        ...   - type: circle
        ...     cx: 100
        ...     cy: 100
        ...     r: 50
        ...     fill: red
        ...     animations:
        ...       - attribute: r
        ...         values: "50;30;50"
        ...         dur: 1s
        ...         repeatCount: indefinite
        ... ''', "animation.webm")
    """
    from .generators.video_generator import create_video_from_svg

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    svg_content = create_diagram_from_yaml(yaml_spec)
    create_video_from_svg(svg_content, str(output_path), duration_ms=duration_ms)
    return output_path
