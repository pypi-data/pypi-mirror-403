"""Transform animation specification class."""

from pydantic import BaseModel, Field


class TransformAnimationSpec(BaseModel):
    """Specification for an SVG transform animation (animateTransform)."""

    type: str  # rotate, translate, scale, skewX, skewY
    dur: str
    values: str | None = None
    from_value: str | None = Field(default=None, alias="from")
    to_value: str | None = Field(default=None, alias="to")
    repeat_count: str | None = Field(default=None, alias="repeatCount")
    additive: str | None = None  # sum or replace

    model_config = {"populate_by_name": True}
