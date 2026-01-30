"""Path segment specification classes."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class MoveToSpec(BaseModel):
    """Move to a point without drawing."""

    type: Literal["move_to"] = "move_to"
    x: float
    y: float

    def to_path_data(self) -> str:
        return f"M{self.x},{self.y}"


class LineToSpec(BaseModel):
    """Draw a line to a point."""

    type: Literal["line_to"] = "line_to"
    x: float
    y: float

    def to_path_data(self) -> str:
        return f"L{self.x},{self.y}"


class CubicBezierSpec(BaseModel):
    """Draw a cubic bezier curve."""

    type: Literal["cubic_bezier"] = "cubic_bezier"
    x1: float  # First control point
    y1: float
    x2: float  # Second control point
    y2: float
    x: float  # End point
    y: float

    def to_path_data(self) -> str:
        return f"C{self.x1},{self.y1} {self.x2},{self.y2} {self.x},{self.y}"


class QuadraticBezierSpec(BaseModel):
    """Draw a quadratic bezier curve."""

    type: Literal["quadratic_bezier"] = "quadratic_bezier"
    x1: float  # Control point
    y1: float
    x: float  # End point
    y: float

    def to_path_data(self) -> str:
        return f"Q{self.x1},{self.y1} {self.x},{self.y}"


class ArcSpec(BaseModel):
    """Draw an elliptical arc."""

    type: Literal["arc"] = "arc"
    rx: float  # X radius
    ry: float  # Y radius
    rotation: float = 0  # X-axis rotation in degrees
    large_arc: bool = False  # Large arc flag
    sweep: bool = True  # Sweep direction (True = clockwise)
    x: float  # End point
    y: float

    def to_path_data(self) -> str:
        large = 1 if self.large_arc else 0
        sweep = 1 if self.sweep else 0
        return f"A{self.rx},{self.ry} {self.rotation} {large} {sweep} {self.x},{self.y}"


class CloseSpec(BaseModel):
    """Close the path back to the start."""

    type: Literal["close"] = "close"

    def to_path_data(self) -> str:
        return "Z"


SegmentSpec = Annotated[
    MoveToSpec | LineToSpec | CubicBezierSpec | QuadraticBezierSpec | ArcSpec | CloseSpec,
    Field(discriminator="type"),
]


def segments_to_path_data(segments: list[SegmentSpec]) -> str:
    """Convert a list of segment specs to SVG path data."""
    return " ".join(seg.to_path_data() for seg in segments)
