"""Connection element specification class."""

from typing import Literal

from pydantic import Field

from .element_spec import ElementSpec


class ConnectionSpec(ElementSpec):
    """Specification for a connection element.

    Connections draw lines between the centers of two referenced elements.
    """

    type: Literal["connection"] = "connection"
    from_id: str = Field(alias="from")
    to_id: str = Field(alias="to")
    stroke: str = "black"
    stroke_width: float = Field(default=2, alias="stroke-width")
    marker_end: str | None = Field(default=None, alias="marker-end")
