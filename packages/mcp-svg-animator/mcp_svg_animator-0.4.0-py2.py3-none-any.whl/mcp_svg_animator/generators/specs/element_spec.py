"""Base element specification class."""

from pydantic import BaseModel, Field

from .animation_spec import AnimationSpec


class ElementSpec(BaseModel):
    """Base specification for SVG elements."""

    id: str | None = None
    fill: str = "blue"
    stroke: str = "none"
    stroke_width: float = Field(default=0, alias="stroke-width")
    animations: list[AnimationSpec] = Field(default_factory=list)

    # Common styling attributes
    transform: str | None = None
    opacity: float | None = None
    stroke_dasharray: str | None = Field(default=None, alias="stroke-dasharray")
    stroke_linecap: str | None = Field(default=None, alias="stroke-linecap")
    stroke_linejoin: str | None = Field(default=None, alias="stroke-linejoin")
    fill_opacity: float | None = Field(default=None, alias="fill-opacity")
    stroke_opacity: float | None = Field(default=None, alias="stroke-opacity")

    model_config = {"populate_by_name": True}
