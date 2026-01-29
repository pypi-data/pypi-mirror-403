"""Ellipse element specification class."""

from typing import Literal

from .element_spec import ElementSpec


class EllipseSpec(ElementSpec):
    """Specification for an ellipse element."""

    type: Literal["ellipse"] = "ellipse"
    cx: float = 0
    cy: float = 0
    rx: float = 50
    ry: float = 25
