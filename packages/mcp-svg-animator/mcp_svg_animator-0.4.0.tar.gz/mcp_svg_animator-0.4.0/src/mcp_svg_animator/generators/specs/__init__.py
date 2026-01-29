"""Spec classes for SVG elements and animations."""

from .animation_spec import AnimationSpec
from .circle_spec import CircleSpec
from .connection_spec import ConnectionSpec
from .element_spec import ElementSpec
from .ellipse_spec import EllipseSpec
from .group_spec import GroupSpec
from .line_spec import LineSpec
from .path_spec import PathSpec
from .rectangle_spec import RectangleSpec
from .segment_specs import (
    ArcSpec,
    CloseSpec,
    CubicBezierSpec,
    LineToSpec,
    MoveToSpec,
    QuadraticBezierSpec,
    SegmentSpec,
    segments_to_path_data,
)
from .text_spec import TextSpec
from .transform_animation_spec import TransformAnimationSpec

__all__ = [
    "AnimationSpec",
    "ArcSpec",
    "CircleSpec",
    "CloseSpec",
    "ConnectionSpec",
    "CubicBezierSpec",
    "ElementSpec",
    "EllipseSpec",
    "GroupSpec",
    "LineSpec",
    "LineToSpec",
    "MoveToSpec",
    "PathSpec",
    "QuadraticBezierSpec",
    "RectangleSpec",
    "SegmentSpec",
    "TextSpec",
    "TransformAnimationSpec",
    "segments_to_path_data",
]
