"""Line element specification class."""

from typing import Literal

from pydantic import Field

from .element_spec import ElementSpec


class LineSpec(ElementSpec):
    """Specification for a line element."""

    type: Literal["line"] = "line"
    x1: float = 0
    y1: float = 0
    x2: float = 100
    y2: float = 100
    stroke: str = "black"
    stroke_width: float = Field(default=2, alias="stroke_width")
    marker_end: str | None = None
