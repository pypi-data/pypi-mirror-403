"""Resolve relative position references in element specifications."""

import re
from copy import deepcopy

# Pattern to match expressions like "box1.x", "box1.x + 70", "box1.cx - 30"
EXPR_PATTERN = re.compile(
    r"^(?P<element_id>\w+)\.(?P<attr>\w+)(?:\s*(?P<op>[+-])\s*(?P<offset>\d+(?:\.\d+)?))?$"
)

# Pattern to extract coordinates from SVG path commands
# Matches command letter followed by coordinate pairs
PATH_COORD_PATTERN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?\d*\.?\d+")

# Attributes that can be referenced for position calculations
POSITION_ATTRS = {"x", "y", "cx", "cy", "x1", "y1", "x2", "y2", "width", "height", "r", "rx", "ry"}


def get_element_center(element: dict) -> tuple[float, float]:
    """Calculate the center point of an element.

    Args:
        element: Element specification dict with a 'type' key.

    Returns:
        Tuple of (center_x, center_y).

    Raises:
        ValueError: If the element type doesn't support center calculation,
                    or if a path is open (not closed).
    """
    element_type = element.get("type")

    if element_type in ("circle", "ellipse"):
        return (float(element["cx"]), float(element["cy"]))
    elif element_type == "rectangle":
        x = float(element["x"])
        y = float(element["y"])
        width = float(element["width"])
        height = float(element["height"])
        return (x + width / 2, y + height / 2)
    elif element_type == "text":
        return (float(element["x"]), float(element["y"]))
    elif element_type == "path":
        return _get_path_center(element)
    else:
        raise ValueError(f"Cannot calculate center for element type: {element_type}")


def _get_path_center(element: dict) -> tuple[float, float]:
    """Calculate the centroid of a closed path.

    Args:
        element: Path element dict with either 'd' (raw path data) or 'segments'.

    Returns:
        Tuple of (center_x, center_y) - the centroid of the path vertices.

    Raises:
        ValueError: If the path is open (not closed with Z or close segment).
    """
    segments = element.get("segments")
    d = element.get("d")

    if segments:
        return _get_path_center_from_segments(segments)
    elif d:
        return _get_path_center_from_d(d)
    else:
        raise ValueError("Path element requires either 'd' or 'segments'")


def _get_path_center_from_segments(segments: list[dict]) -> tuple[float, float]:
    """Calculate centroid from segment-based path definition."""
    # Check if path is closed
    is_closed = any(seg.get("type") == "close" for seg in segments)
    if not is_closed:
        raise ValueError("Cannot calculate center for open path")

    # Extract coordinates from segments
    coords: list[tuple[float, float]] = []
    for seg in segments:
        seg_type = seg.get("type")
        if seg_type in ("move_to", "line_to"):
            coords.append((float(seg["x"]), float(seg["y"])))
        elif seg_type == "cubic_bezier":
            # Use end point only (control points are not vertices)
            coords.append((float(seg["x"]), float(seg["y"])))
        elif seg_type == "quadratic_bezier":
            coords.append((float(seg["x"]), float(seg["y"])))
        elif seg_type == "arc":
            coords.append((float(seg["x"]), float(seg["y"])))
        # close segment has no coordinates

    if not coords:
        raise ValueError("Path has no coordinates")

    # Calculate centroid (average of all coordinates)
    cx = sum(x for x, _ in coords) / len(coords)
    cy = sum(y for _, y in coords) / len(coords)
    return (cx, cy)


def _get_path_center_from_d(d: str) -> tuple[float, float]:
    """Calculate centroid from raw SVG path data."""
    # Check if path is closed
    if not d.rstrip().endswith(("Z", "z")):
        raise ValueError("Cannot calculate center for open path")

    # Parse the path data to extract coordinates
    tokens = PATH_COORD_PATTERN.findall(d)
    coords: list[tuple[float, float]] = []
    current_command = None
    numbers: list[float] = []

    for token in tokens:
        if token in "MmLlHhVvCcSsQqTtAaZz":
            # Process previous command's numbers
            if current_command and numbers:
                coords.extend(_extract_coords_from_command(current_command, numbers))
            current_command = token
            numbers = []
        else:
            # It's a number
            try:
                numbers.append(float(token))
            except ValueError:
                pass

    # Process last command
    if current_command and numbers:
        coords.extend(_extract_coords_from_command(current_command, numbers))

    if not coords:
        raise ValueError("Path has no coordinates")

    # Calculate centroid
    cx = sum(x for x, _ in coords) / len(coords)
    cy = sum(y for _, y in coords) / len(coords)
    return (cx, cy)


def _extract_coords_from_command(command: str, numbers: list[float]) -> list[tuple[float, float]]:
    """Extract endpoint coordinates from a path command."""
    coords: list[tuple[float, float]] = []

    if command in "Mm":
        # Move to: pairs of x,y
        for i in range(0, len(numbers) - 1, 2):
            coords.append((numbers[i], numbers[i + 1]))
    elif command in "Ll":
        # Line to: pairs of x,y
        for i in range(0, len(numbers) - 1, 2):
            coords.append((numbers[i], numbers[i + 1]))
    elif command in "Hh":
        # Horizontal line: x values only (we'll skip these for centroid)
        pass
    elif command in "Vv":
        # Vertical line: y values only (we'll skip these for centroid)
        pass
    elif command in "Cc":
        # Cubic bezier: x1,y1,x2,y2,x,y - take only endpoint
        for i in range(0, len(numbers) - 5, 6):
            coords.append((numbers[i + 4], numbers[i + 5]))
    elif command in "Ss":
        # Smooth cubic: x2,y2,x,y - take only endpoint
        for i in range(0, len(numbers) - 3, 4):
            coords.append((numbers[i + 2], numbers[i + 3]))
    elif command in "Qq":
        # Quadratic bezier: x1,y1,x,y - take only endpoint
        for i in range(0, len(numbers) - 3, 4):
            coords.append((numbers[i + 2], numbers[i + 3]))
    elif command in "Tt":
        # Smooth quadratic: x,y
        for i in range(0, len(numbers) - 1, 2):
            coords.append((numbers[i], numbers[i + 1]))
    elif command in "Aa":
        # Arc: rx,ry,rotation,large-arc,sweep,x,y - take only endpoint
        for i in range(0, len(numbers) - 6, 7):
            coords.append((numbers[i + 5], numbers[i + 6]))

    return coords


def resolve_positions(elements: list[dict]) -> list[dict]:
    """Resolve relative position references in element specifications.

    Uses two-phase processing:
    1. Process all non-connection elements, building a registry of positions
    2. Resolve connections using the full registry, prepend to element list

    Args:
        elements: List of element specification dicts. String values in
            position attributes can reference other elements using syntax
            like "element_id.attr" or "element_id.attr + offset".

    Returns:
        New list of element dicts with all position references resolved
        to numeric values. Connections appear first (so they render behind).

    Raises:
        ValueError: If an expression references an unknown element or attribute.
    """
    # Phase 1: Separate connections from other elements
    connections: list[dict] = []
    other_elements: list[dict] = []

    for element in elements:
        if element.get("type") == "connection":
            connections.append(element)
        else:
            other_elements.append(element)

    # Phase 2: Process non-connection elements, build registry
    resolved_others: list[dict] = []
    element_registry: dict[str, dict] = {}

    for element in other_elements:
        resolved = _resolve_element(element, element_registry)
        resolved_others.append(resolved)

        element_id = resolved.get("id")
        if element_id:
            element_registry[element_id] = resolved

    # Phase 3: Resolve connections using full registry
    resolved_connections: list[dict] = []

    for connection in connections:
        resolved = _resolve_connection(connection, element_registry)
        resolved_connections.append(resolved)

    # Return connections first (render behind), then other elements
    return resolved_connections + resolved_others


def _resolve_connection(connection: dict, registry: dict[str, dict]) -> dict:
    """Resolve a connection element using the element registry.

    Calculates center points of from/to elements and adds x1, y1, x2, y2.
    """
    from_id = connection.get("from")
    to_id = connection.get("to")

    if from_id not in registry:
        raise ValueError(f"Unknown element reference: {from_id}")
    if to_id not in registry:
        raise ValueError(f"Unknown element reference: {to_id}")

    from_element = registry[from_id]
    to_element = registry[to_id]

    x1, y1 = get_element_center(from_element)
    x2, y2 = get_element_center(to_element)

    resolved = deepcopy(connection)
    resolved["x1"] = x1
    resolved["y1"] = y1
    resolved["x2"] = x2
    resolved["y2"] = y2

    return resolved


def _resolve_element(element: dict, registry: dict[str, dict]) -> dict:
    """Resolve position references in a single element."""
    resolved = deepcopy(element)

    for key, value in element.items():
        if isinstance(value, str) and key in POSITION_ATTRS:
            resolved[key] = _resolve_expression(value, registry)

    return resolved


def _resolve_expression(expr: str, registry: dict[str, dict]) -> float:
    """Parse and resolve a position expression.

    Args:
        expr: Expression like "box1.x" or "box1.x + 70"
        registry: Dict of element_id -> resolved element dict

    Returns:
        Resolved numeric value.

    Raises:
        ValueError: If the expression references an unknown element or attribute.
    """
    match = EXPR_PATTERN.match(expr.strip())
    if not match:
        raise ValueError(f"Invalid position expression: {expr}")

    element_id = match.group("element_id")
    attr = match.group("attr")
    op = match.group("op")
    offset_str = match.group("offset")

    if element_id not in registry:
        raise ValueError(f"Unknown element reference: {element_id}")

    element = registry[element_id]
    if attr not in element:
        raise ValueError(f"Unknown attribute '{attr}' on element '{element_id}'")

    base_value = float(element[attr])

    if op and offset_str:
        offset = float(offset_str)
        if op == "+":
            return base_value + offset
        else:  # op == "-"
            return base_value - offset

    return base_value
