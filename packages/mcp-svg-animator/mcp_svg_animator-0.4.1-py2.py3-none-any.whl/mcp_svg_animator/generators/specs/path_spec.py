"""Path element specification class."""

from typing import Literal

from pydantic import Field

from .element_spec import ElementSpec
from .segment_specs import SegmentSpec, segments_to_path_data


class PathSpec(ElementSpec):
    """Specification for a path element."""

    type: Literal["path"] = "path"
    d: str | None = None  # SVG path data (raw)
    segments: list[SegmentSpec] = Field(default_factory=list)  # Segment-based path
    fill: str = "none"
    stroke: str = "black"
    stroke_width: float = Field(default=1, alias="stroke_width")

    def get_path_data(self) -> str:
        """Get the SVG path data, either from d or by converting segments."""
        if self.d is not None:
            return self.d
        if self.segments:
            return segments_to_path_data(self.segments)
        raise ValueError("PathSpec requires either 'd' or 'segments'")
