"""Text element specification class."""

from typing import Literal

from pydantic import Field

from .element_spec import ElementSpec


class TextSpec(ElementSpec):
    """Specification for a text element."""

    type: Literal["text"] = "text"
    text: str = ""
    font_size: float = Field(default=16, alias="font-size")
    x: float = 0
    y: float = 0
    fill: str = "black"
    stroke: str = "none"
    text_anchor: str | None = Field(default=None, alias="text-anchor")

    # Font-related attributes
    font_family: str | None = Field(default=None, alias="font-family")
    font_weight: str | None = Field(default=None, alias="font-weight")
    font_style: str | None = Field(default=None, alias="font-style")
    dominant_baseline: str | None = Field(default=None, alias="dominant-baseline")

    # Background panel
    background: str | None = None
    background_padding: float = Field(default=4, alias="background-padding")
