"""Circle element specification class."""

from typing import Literal

from .element_spec import ElementSpec


class CircleSpec(ElementSpec):
    """Specification for a circle element."""

    type: Literal["circle"] = "circle"
    cx: float = 50
    cy: float = 50
    r: float = 25
