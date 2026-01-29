"""
This module defines the base `Component` class, which is the foundational
building block for all UI elements in the Nolite framework. It handles the
logic for rendering Python objects into HTML, including managing children,
applying styles, and generating CSS for interactive effects like hover.
"""

import re
import uuid
from typing import List, Dict, Any, Optional

from ..utils.style_parser import process_styles, generate_css_class


class Component:
    """The foundational building block for all UI elements in Nolite.

    This class provides the core logic for translating a Python object into an
    HTML element. It manages a component's children, processes Pythonic styling
    arguments, generates CSS for effects like hover, and renders the final
    HTML string.

    Every UI element in the `nolite.components` library is a subclass of this
    `Component`.

    Attributes:
        tag (str): The HTML tag to be rendered (e.g., 'div', 'p', 'span').
                   Subclasses should override this.
    """

    tag: str = "div"  # Default HTML tag

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        style: Optional[Dict[str, Any]] = None,
        hover_style: Optional[Dict[str, Any]] = None,
        on_click: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ):
        """Initializes a Component, processing its children and styling.

        This method separates styling keyword arguments (like `bg_color`) from
        standard HTML attributes (like `id` or `href`), processes them through
        the style parser, and prepares the component for rendering.

        Args:
            children: A list of child `Component` objects or strings to be
                rendered inside this component.
            style: A dictionary of CSS styles. Can be overridden by
                conflicting style keyword arguments.
            hover_style: A dictionary of styles to apply on mouse hover.
            on_click: Describes a client-side action to be performed on click.
            **kwargs: Python-friendly style attributes (e.g., `font_size=16`)
                and standard HTML attributes (e.g., `id="my-div"`).
        """
        self.children = children if children is not None else []
        self.on_click = on_click

        # Each component gets a unique ID to attach hover/animation styles
        self.nolite_id = f"nolite-id-{uuid.uuid4().hex[:8]}"

        # Separate HTML attributes from style kwargs
        html_attrs = {}
        style_kwargs = {}
        known_html_attrs = {
            "id",
            "className",
            "href",
            "src",
            "alt",
            "target",
            "rel",
            "type",
            "name",
            "placeholder",
            "value",
            "action",
            "method",
            "disabled",
            "required",
            "checked",
            "selected",
            "readOnly",
            "aria_label",
        }
        for key, value in kwargs.items():
            if key in known_html_attrs or key.startswith("data_"):
                html_attrs[key] = value
            else:
                style_kwargs[key] = value

        self.attributes = html_attrs

        # Process styles using the new utility
        # style_kwargs will override any conflicting keys in the `style` dict
        self.style = process_styles(style or {}, **style_kwargs)
        self.hover_style = process_styles(hover_style or {}, **{})

    def get_generated_css(self) -> str:
        """Generates instance-specific CSS rules, such as for hover effects.

        This method is called by the `Page` object during the rendering process.
        It checks for any special styling (like `hover_style`) and generates
        the necessary CSS rules, which are then injected into a `<style>` tag
        in the document's head.

        Returns:
            A string containing CSS rules, or an empty string if none are needed.
        """
        css_rules = []
        if self.hover_style:
            css_rules.append(
                generate_css_class(
                    self.nolite_id, self.hover_style, pseudo_selector=":hover"
                )
            )
        return "\n".join(css_rules)

    def _render_style(self) -> str:
        """Renders the component's inline styles into an HTML `style` attribute string."""
        if not self.style:
            return ""

        style_str = "; ".join(f"{key}: {value}" for key, value in self.style.items())
        return f' style="{style_str}"'

    def _to_kebab_case(self, name: str) -> str:
        """Converts a snake_case or camelCase string to kebab-case for HTML/CSS."""
        # Convert camelCase to snake_case first
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()
        # Convert snake_case to kebab-case
        return name.replace("_", "-")

    def _render_attributes(self) -> str:
        """Renders all HTML attributes into a single string for the opening tag.

        This method handles several important translations:
        - Injects a unique `nolite-id-` class for CSS targeting.
        - Converts the Python `className` argument to the HTML `class` attribute.
        - Translates the `on_click` dictionary into `data-nolite-*` attributes.
        - Handles boolean attributes (e.g., `disabled=True` becomes `disabled`).
        """
        attrs = self.attributes.copy()

        # Handle on_click actions by converting them to data-* attributes
        if self.on_click:
            if "action" not in self.on_click:
                raise ValueError("on_click dictionary must contain an 'action' key.")
            for key, value in self.on_click.items():
                attr_name = f"data-nolite-{self._to_kebab_case(key)}"
                attrs[attr_name] = value

        # Add the unique nolite ID to the class list
        user_classes = attrs.pop("className", "")
        all_classes = f"{self.nolite_id} {user_classes}".strip()
        if all_classes:
            attrs["class"] = all_classes

        # Handle boolean attributes and attribute value escaping
        attr_parts = []
        for key, value in attrs.items():
            if value is None:
                continue

            kebab_key = self._to_kebab_case(key)

            if isinstance(value, bool):
                if value:
                    attr_parts.append(kebab_key)
            else:
                escaped_value = str(value).replace("&", "&amp;").replace('"', "&quot;")
                attr_parts.append(f'{kebab_key}="{escaped_value}"')

        return " " + " ".join(attr_parts) if attr_parts else ""

    def _render_children(self) -> str:
        """Recursively renders all child components and strings into a single HTML string.

        This method iterates through the `self.children` list. If an item is a
        `Component`, its `render()` method is called. If it is a string, it is
        HTML-escaped for security.
        """
        rendered_children = []
        for child in self.children:
            if isinstance(child, Component):
                rendered_children.append(child.render())
            elif isinstance(child, str):
                escaped_child = (
                    child.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                rendered_children.append(escaped_child)
            else:
                rendered_children.append(str(child))
        return "".join(rendered_children)

    def get_all_descendant_css(self) -> str:
        """Recursively collects all generated CSS from this component and its children."""
        all_css = [self.get_generated_css()]
        for child in self.children:
            if isinstance(child, Component):
                all_css.append(child.get_all_descendant_css())

        return "\n".join(filter(None, all_css))

    def render(self) -> str:
        """Renders the component and its children into a final HTML string.

        This is the main public method for a component. It orchestrates the
        calling of all internal `_render_*` methods to assemble the final
        HTML representation. It also correctly handles self-closing tags.

        Returns:
            The complete HTML string for this component and all its descendants.
        """
        style_str = self._render_style()
        attrs_str = self._render_attributes()
        children_str = self._render_children()

        self_closing_tags = ["input", "img", "br", "hr", "meta", "link"]
        if self.tag.lower() in self_closing_tags:
            return f"<{self.tag}{attrs_str}{style_str}>"
        else:
            return f"<{self.tag}{attrs_str}{style_str}>{children_str}</{self.tag}>"
