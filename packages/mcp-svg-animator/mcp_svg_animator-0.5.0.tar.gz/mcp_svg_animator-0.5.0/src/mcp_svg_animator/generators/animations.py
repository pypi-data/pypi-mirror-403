"""Animated SVG diagram generator using drawsvg."""

from typing import cast

import drawsvg as draw

from .position_resolver import resolve_positions
from .specs.animation_spec import AnimationSpec
from .specs.circle_spec import CircleSpec
from .specs.element_spec import ElementSpec
from .specs.ellipse_spec import EllipseSpec
from .specs.group_spec import GroupSpec
from .specs.line_spec import LineSpec
from .specs.path_spec import PathSpec
from .specs.rectangle_spec import RectangleSpec
from .specs.text_spec import TextSpec
from .specs.transform_animation_spec import TransformAnimationSpec
from .specs.connection_spec import ConnectionSpec


def create_animated_diagram(arguments: dict) -> str:
    """Create an animated SVG diagram.

    Args:
        arguments: Dictionary containing:
            - width: Canvas width (default 400)
            - height: Canvas height (default 300)
            - elements: List of shape specifications. Position attributes
                can use relative references like "element_id.x + 70".

    Returns:
        SVG content as a string.
    """
    width = arguments.get("width", 400)
    height = arguments.get("height", 300)
    elements = arguments.get("elements", [])

    # Resolve relative position references before creating elements
    resolved_elements = resolve_positions(elements)

    d = draw.Drawing(width, height)

    for element in resolved_elements:
        shape = _create_element(element)
        d.append(shape)

    return cast(str, d.as_svg())


def _build_common_kwargs(spec: ElementSpec) -> dict:
    """Build kwargs dict for common SVG attributes."""
    kwargs: dict = {
        "fill": spec.fill,
        "stroke": spec.stroke,
        "stroke_width": spec.stroke_width,
    }
    if spec.transform:
        kwargs["transform"] = spec.transform
    if spec.opacity is not None:
        kwargs["opacity"] = spec.opacity
    if spec.stroke_dasharray:
        kwargs["stroke_dasharray"] = spec.stroke_dasharray
    if spec.stroke_linecap:
        kwargs["stroke_linecap"] = spec.stroke_linecap
    if spec.stroke_linejoin:
        kwargs["stroke_linejoin"] = spec.stroke_linejoin
    if spec.fill_opacity is not None:
        kwargs["fill_opacity"] = spec.fill_opacity
    if spec.stroke_opacity is not None:
        kwargs["stroke_opacity"] = spec.stroke_opacity
    return kwargs


def _create_circle(spec: CircleSpec):
    kwargs = _build_common_kwargs(spec)
    return draw.Circle(spec.cx, spec.cy, spec.r, **kwargs)


def _create_ellipse(spec: EllipseSpec):
    kwargs = _build_common_kwargs(spec)
    return draw.Ellipse(spec.cx, spec.cy, spec.rx, spec.ry, **kwargs)  # type: ignore[attr-defined]


def _create_rectangle(spec: RectangleSpec):
    kwargs = _build_common_kwargs(spec)
    if spec.rx is not None:
        kwargs["rx"] = spec.rx
    if spec.ry is not None:
        kwargs["ry"] = spec.ry
    return draw.Rectangle(spec.x, spec.y, spec.width, spec.height, **kwargs)


def _create_arrow_marker(color: str = "black"):
    """Create an arrow marker for line endings."""
    arrow = draw.Marker(-0.1, -0.5, 0.9, 0.5, scale=4, orient="auto", id="arrow")
    arrow.append(draw.Lines(-0.1, -0.5, -0.1, 0.5, 0.9, 0, fill=color, close=True))
    return arrow


def _create_line(spec: LineSpec):
    kwargs = _build_common_kwargs(spec)
    # Line doesn't use fill
    del kwargs["fill"]
    if spec.marker_end == "arrow":
        kwargs["marker_end"] = _create_arrow_marker(spec.stroke)
    return draw.Line(spec.x1, spec.y1, spec.x2, spec.y2, **kwargs)


def _create_text(spec: TextSpec):
    kwargs: dict = {"fill": spec.fill}
    if spec.text_anchor:
        kwargs["text_anchor"] = spec.text_anchor
    if spec.font_family:
        kwargs["font_family"] = spec.font_family
    if spec.font_weight:
        kwargs["font_weight"] = spec.font_weight
    if spec.font_style:
        kwargs["font_style"] = spec.font_style
    if spec.dominant_baseline:
        kwargs["dominant_baseline"] = spec.dominant_baseline
    if spec.transform:
        kwargs["transform"] = spec.transform

    text_element = draw.Text(spec.text, spec.font_size, spec.x, spec.y, **kwargs)

    # If background is specified, wrap text in a group with a background rect
    if spec.background:
        group = draw.Group()

        # Create background rectangle
        # Approximate text dimensions based on font size and text length
        padding = spec.background_padding
        char_width = spec.font_size * 0.6  # Approximate character width
        text_width = len(spec.text) * char_width
        text_height = spec.font_size

        # Position rect behind text (text y is baseline, rect needs top-left)
        rect_x = spec.x - padding
        rect_y = spec.y - text_height + padding / 2
        rect_width = text_width + 2 * padding
        rect_height = text_height + padding

        background_rect = draw.Rectangle(
            rect_x, rect_y, rect_width, rect_height,
            fill=spec.background, stroke="none"
        )
        group.append(background_rect)
        group.append(text_element)
        return group

    return text_element


def _create_path(spec: PathSpec):
    kwargs = _build_common_kwargs(spec)
    return draw.Path(d=spec.get_path_data(), **kwargs)


def _create_connection(spec: ConnectionSpec, resolved_dict: dict):
    """Create a connection element as a line between two elements.

    The resolved_dict contains x1, y1, x2, y2 coordinates calculated
    by resolve_positions from the centers of the from/to elements.
    """
    kwargs: dict = {
        "stroke": spec.stroke,
        "stroke_width": spec.stroke_width,
    }
    if spec.opacity is not None:
        kwargs["opacity"] = spec.opacity
    if spec.stroke_dasharray:
        kwargs["stroke_dasharray"] = spec.stroke_dasharray
    if spec.stroke_linecap:
        kwargs["stroke_linecap"] = spec.stroke_linecap
    if spec.marker_end == "arrow":
        kwargs["marker_end"] = _create_arrow_marker(spec.stroke)

    # Use coordinates from resolved dict (added by resolve_positions)
    x1 = resolved_dict["x1"]
    y1 = resolved_dict["y1"]
    x2 = resolved_dict["x2"]
    y2 = resolved_dict["y2"]

    return draw.Line(x1, y1, x2, y2, **kwargs)


_ELEMENT_CREATORS = {
    "circle": (CircleSpec, _create_circle),
    "ellipse": (EllipseSpec, _create_ellipse),
    "rectangle": (RectangleSpec, _create_rectangle),
    "line": (LineSpec, _create_line),
    "text": (TextSpec, _create_text),
    "path": (PathSpec, _create_path),
}


def _apply_animations(element, animations: list[AnimationSpec]):
    """Apply animations to an SVG element."""
    for spec in animations:
        anim = draw.Animate(
            spec.attribute,
            spec.dur,
            from_or_values=spec.from_value,
            to=spec.to_value,
            repeatCount=spec.repeat_count,
        )
        element.append_anim(anim)


def _create_group(spec: GroupSpec):
    """Create a group element with its children."""
    kwargs = {}
    if spec.transform:
        kwargs["transform"] = spec.transform

    group = draw.Group(**kwargs)

    for child_dict in spec.elements:
        child = _create_element(child_dict)
        group.append(child)

    # Apply transform animations
    for anim in spec.transform_animations:
        group.append(_create_transform_animation(anim))

    return group


def _create_transform_animation(spec: TransformAnimationSpec):
    """Create an animateTransform element."""
    attrs = [
        'attributeName="transform"',
        f'type="{spec.type}"',
        f'dur="{spec.dur}"',
    ]
    if spec.values:
        attrs.append(f'values="{spec.values}"')
    if spec.from_value:
        attrs.append(f'from="{spec.from_value}"')
    if spec.to_value:
        attrs.append(f'to="{spec.to_value}"')
    if spec.repeat_count:
        attrs.append(f'repeatCount="{spec.repeat_count}"')
    if spec.additive:
        attrs.append(f'additive="{spec.additive}"')

    return draw.Raw(f'<animateTransform {" ".join(attrs)}/>')


def _create_element(spec_dict: dict):
    """Create a single SVG element from a specification."""
    element_type = spec_dict.get("type")
    if element_type is None:
        raise ValueError("Element spec missing 'type' key")

    # Handle groups specially due to recursive nature
    if element_type == "group":
        spec = GroupSpec.model_validate(spec_dict)
        return _create_group(spec)

    # Handle connections specially - they need the resolved dict for coordinates
    if element_type == "connection":
        spec = ConnectionSpec.model_validate(spec_dict)
        element = _create_connection(spec, spec_dict)
        if spec.animations:
            _apply_animations(element, spec.animations)
        return element

    creator_info = _ELEMENT_CREATORS.get(element_type)
    if creator_info is None:
        raise ValueError(f"Unknown element type: {element_type}")

    spec_class, creator = creator_info
    spec = spec_class.model_validate(spec_dict)
    element = creator(spec)

    if spec.animations:
        _apply_animations(element, spec.animations)

    return element
