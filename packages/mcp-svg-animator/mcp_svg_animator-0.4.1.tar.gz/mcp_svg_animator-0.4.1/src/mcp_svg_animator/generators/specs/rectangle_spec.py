"""Rectangle element specification class."""

from typing import Literal

from .element_spec import ElementSpec


class RectangleSpec(ElementSpec):
    """Specification for a rectangle element."""

    type: Literal["rectangle"] = "rectangle"
    x: float = 0
    y: float = 0
    width: float = 100
    height: float = 50
    rx: float | None = None
    ry: float | None = None
