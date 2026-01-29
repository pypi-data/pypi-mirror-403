"""Animation specification class."""

from pydantic import BaseModel, Field


class AnimationSpec(BaseModel):
    """Specification for an SVG animation."""

    attribute: str
    dur: str
    from_value: str | None = None
    to_value: str | None = None
    repeat_count: str | None = Field(default=None, alias="repeatCount")

    model_config = {"populate_by_name": True}
