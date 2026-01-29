"""Resolve relative position references in element specifications."""

import re
from copy import deepcopy

# Pattern to match expressions like "box1.x", "box1.x + 70", "box1.cx - 30"
EXPR_PATTERN = re.compile(
    r"^(?P<element_id>\w+)\.(?P<attr>\w+)(?:\s*(?P<op>[+-])\s*(?P<offset>\d+(?:\.\d+)?))?$"
)

# Attributes that can be referenced for position calculations
POSITION_ATTRS = {"x", "y", "cx", "cy", "x1", "y1", "x2", "y2", "width", "height", "r", "rx", "ry"}


def resolve_positions(elements: list[dict]) -> list[dict]:
    """Resolve relative position references in element specifications.

    Processes elements in order, resolving string expressions that reference
    previously defined elements.

    Args:
        elements: List of element specification dicts. String values in
            position attributes can reference other elements using syntax
            like "element_id.attr" or "element_id.attr + offset".

    Returns:
        New list of element dicts with all position references resolved
        to numeric values.

    Raises:
        ValueError: If an expression references an unknown element or attribute.
    """
    resolved_elements: list[dict] = []
    element_registry: dict[str, dict] = {}

    for element in elements:
        resolved = _resolve_element(element, element_registry)
        resolved_elements.append(resolved)

        element_id = resolved.get("id")
        if element_id:
            element_registry[element_id] = resolved

    return resolved_elements


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
