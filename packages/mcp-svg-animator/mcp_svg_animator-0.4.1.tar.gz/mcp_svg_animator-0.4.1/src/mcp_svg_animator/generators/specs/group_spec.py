"""Group element specification class."""

from typing import Literal

from pydantic import BaseModel, Field

from .transform_animation_spec import TransformAnimationSpec


class GroupSpec(BaseModel):
    """Specification for a group element."""

    id: str | None = None
    type: Literal["group"] = "group"
    transform: str | None = None
    transform_animations: list[TransformAnimationSpec] = Field(default_factory=list)
    elements: list[dict] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
