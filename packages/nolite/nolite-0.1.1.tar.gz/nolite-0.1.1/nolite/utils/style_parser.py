import re
from typing import Dict, Any

# Style Mapping and Constants

# Maps Python-friendly style kwargs to their CSS equivalents.
STYLE_MAPPING = {
    # Layout - Box Model
    "margin": "margin",
    "m": "margin",
    "margin_top": "margin-top",
    "mt": "margin-top",
    "margin_right": "margin-right",
    "mr": "margin-right",
    "margin_bottom": "margin-bottom",
    "mb": "margin-bottom",
    "margin_left": "margin-left",
    "ml": "margin-left",
    "padding": "padding",
    "p": "padding",
    "padding_top": "padding-top",
    "pt": "padding-top",
    "padding_right": "padding-right",
    "pr": "padding-right",
    "padding_bottom": "padding-bottom",
    "pb": "padding-bottom",
    "padding_left": "padding-left",
    "pl": "padding-left",
    "width": "width",
    "w": "width",
    "height": "height",
    "h": "height",
    "max_width": "max-width",
    "max_h": "max-height",
    "min_width": "min-width",
    "min_h": "min-height",
    "border": "border",
    "border_radius": "border-radius",
    "box_shadow": "box-shadow",
    "display": "display",
    "position": "position",
    "top": "top",
    "right": "right",
    "bottom": "bottom",
    "left": "left",
    "overflow": "overflow",
    "overflow_x": "overflow-x",
    "overflow_y": "overflow-y",
    "z_index": "z-index",
    # Typography
    "color": "color",
    "font_size": "font-size",
    "font_family": "font-family",
    "font_weight": "font-weight",
    "text_align": "text-align",
    "line_height": "line-height",
    "letter_spacing": "letter-spacing",
    "text_decoration": "text-decoration",
    "text_transform": "text-transform",
    # Background & Color
    "background_color": "background-color",
    "bg_color": "background-color",
    "background": "background",
    "bg": "background",
    "opacity": "opacity",
    # Flexbox
    "flex": "flex",
    "flex_direction": "flex-direction",
    "justify_content": "justify-content",
    "align_items": "align-items",
    "flex_wrap": "flex-wrap",
    "flex_grow": "flex-grow",
    "flex_shrink": "flex-shrink",
    "flex_basis": "flex-basis",
    "align_self": "align-self",
    # Grid
    "grid_template_columns": "grid-template-columns",
    "grid_template_rows": "grid-template-rows",
    "grid_gap": "grid-gap",
    "gap": "gap",
    # Transitions & Animations
    "transition": "transition",
    "animation": "animation",
    # Misc
    "cursor": "cursor",
    "list_style": "list-style",
}

# CSS properties that do not require a unit like 'px'.
UNITLESS_PROPERTIES = {
    "opacity",
    "z-index",
    "font-weight",
    "line-height",
    "flex",
    "flex-grow",
    "flex-shrink",
}


# Helper Functions


def _to_kebab_case(name: str) -> str:
    """Converts snake_case or camelCase string to kebab-case."""
    name = re.sub("(.)([A-Z][a-z]+)", r"\\1_\\2", name)
    name = re.sub("([a-z0-9])([A-Z])", r"\\1_\\2", name).lower()
    return name.replace("_", "-")


def _parse_style_value(css_property: str, value: Any) -> str:
    """
    Parses a Python value into a CSS-compatible string.
    - Adds 'px' to numbers for properties that need units.
    - Converts tuples into space-separated values (e.g., for margin, padding).
    """
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, (int, float)):
        if css_property in UNITLESS_PROPERTIES:
            return str(value)
        return f"{value}px"

    if isinstance(value, (list, tuple)):
        return " ".join(_parse_style_value(css_property, item) for item in value)

    return str(value)


# Core Processing Function


def process_styles(style: Dict[str, Any], **kwargs: Any) -> Dict[str, str]:
    """
    Processes Pythonic style kwargs and a style dict into a single CSS style dict.

    Kwargs with Python-friendly names (e.g., `bg_color`) are prioritized over
    the `style` dictionary. The `style` dictionary can contain standard CSS
    property names (camelCase or snake_case).

    Returns:
        A dictionary where keys are kebab-case CSS properties and values are
        CSS-compatible strings.
    """
    processed_style = {}

    # First, process the direct style dictionary
    if style:
        for key, value in style.items():
            css_property = _to_kebab_case(key)
            processed_style[css_property] = _parse_style_value(css_property, value)

    # Then, process kwargs, which will override the style dict if there are conflicts
    for key, value in kwargs.items():
        if key in STYLE_MAPPING:
            css_property = STYLE_MAPPING[key]
            processed_style[css_property] = _parse_style_value(css_property, value)

    return processed_style


# CSS Generation


def generate_css_class(
    class_name: str, style_dict: Dict[str, str], pseudo_selector: str = ""
) -> str:
    """
    Generates a complete CSS rule string from a class name and style dictionary.
    """
    if not style_dict:
        return ""

    style_str = "; ".join(f"{prop}: {val}" for prop, val in style_dict.items())

    return f".{class_name}{pseudo_selector} {{ {style_str}; }}"
