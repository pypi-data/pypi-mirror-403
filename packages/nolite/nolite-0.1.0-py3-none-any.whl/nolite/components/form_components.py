"""
Nolite Form Components

This module provides higher-level, more Pythonic components for building forms.
These components abstract away some of the complexities of standard HTML forms
and integrate seamlessly with Nolite's styling system.
"""

from typing import List, Optional, Any, Union, Tuple

from ..core.component import Component
from .html_components import Input, Button, Div


class Label(Component):
    """Represents a <label> element, often used with form inputs."""

    tag: str = "label"

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        for_id: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initializes a Label instance.

        Args:
            children (Optional[List[Any]]): The text or content of the label.
            for_id (Optional[str]): The ID of the input element this label is for.
            **kwargs: Pythonic style and other HTML attributes.
        """
        # The 'for' attribute in HTML is a reserved keyword in Python,
        # so use 'for_id' and map it.
        html_attrs = kwargs
        if for_id:
            html_attrs["for"] = for_id

        super().__init__(children=children, **html_attrs)


class StyledInput(Input):
    """A user-friendly and styled input component for various types."""

    def __init__(
        self,
        name: str,
        type: str = "text",
        placeholder: Optional[str] = None,
        value: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initializes a StyledInput instance.

        Args:
            name (str): The name of the input, used for form submission.
            type (str): The input type (e.g., 'text', 'number', 'password'). Defaults to 'text'.
            placeholder (Optional[str]): Placeholder text.
            value (Optional[str]): The default value of the input.
            **kwargs: Pythonic style and other HTML attributes.
        """
        base_style = {
            "padding": (8, 12),
            "font_size": 16,
            "border": "1px solid #ccc",
            "border_radius": 4,
            "width": "100%",
            "box_sizing": "border-box",  # Ensures padding doesn't affect width
        }

        # User-provided kwargs override base styles
        final_kwargs = {**base_style, **kwargs}

        super().__init__(
            type=type,
            name=name,
            placeholder=placeholder,
            value=value,
            **final_kwargs,
        )


class Textarea(Component):
    """Represents a <textarea> element for multi-line text input."""

    tag: str = "textarea"

    def __init__(
        self,
        name: str,
        placeholder: Optional[str] = None,
        value: Optional[str] = None,
        rows: int = 4,
        **kwargs: Any,
    ):
        """
        Initializes a Textarea instance.

        Args:
            name (str): The name of the textarea, used for form submission.
            placeholder (Optional[str]): Placeholder text.
            value (Optional[str]): The default content of the textarea.
            rows (int): The visible number of text lines.
            **kwargs: Pythonic style and other HTML attributes.
        """
        base_style = {
            "padding": (8, 12),
            "font_size": 16,
            "border": "1px solid #ccc",
            "border_radius": 4,
            "width": "100%",
            "font_family": "inherit",
            "box_sizing": "border-box",
        }
        final_kwargs = {**base_style, **kwargs}

        # Text area content is passed as a child
        children = [value] if value is not None else []

        super().__init__(
            children=children,
            name=name,
            placeholder=placeholder,
            rows=rows,
            **final_kwargs,
        )


class Checkbox(Component):
    """Represents an <input type="checkbox"> with a label."""

    tag: str = "div"  # We wrap the input and label in a div for styling

    def __init__(
        self,
        name: str,
        label: str,
        checked: bool = False,
        **kwargs: Any,
    ):
        """
        Initializes a Checkbox instance.

        Args:
            name (str): The name of the checkbox, used for form submission.
            label (str): The text label to display next to the checkbox.
            checked (bool): Whether the checkbox is checked by default.
            **kwargs: Pythonic style and other HTML attributes for the wrapper div.
        """
        checkbox_id = f"nolite-checkbox-{name}"

        base_style = {
            "display": "flex",
            "align_items": "center",
            "margin_bottom": 10,
        }
        final_kwargs = {**base_style, **kwargs}

        checkbox_input = Input(
            type="checkbox",
            id=checkbox_id,
            name=name,
            checked=checked,
            margin_right=8,  # Use Pythonic styling
        )

        label_component = Label(for_id=checkbox_id, children=[label], cursor="pointer")

        super().__init__(children=[checkbox_input, label_component], **final_kwargs)


class Option(Component):
    """Represents an <option> element inside a Select."""

    tag: str = "option"

    def __init__(
        self,
        value: str,
        children: Optional[List[Any]] = None,
        selected: bool = False,
        **kwargs: Any,
    ):
        super().__init__(value=value, children=children, selected=selected, **kwargs)


class Select(Component):
    """
    A user-friendly <select> (dropdown) component.
    """

    tag: str = "select"

    def __init__(
        self,
        name: str,
        options: List[Union[str, Tuple[str, str]]],
        value: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initializes a Select instance.

        Args:
            name (str): The name of the select element for form submission.
            options (List[Union[str, Tuple[str, str]]]): A list of options.
                Each item can be a simple string (where value and display text are the same)
                or a tuple of (value, display_text).
            value (Optional[str]): The value of the option to be selected by default.
            **kwargs: Pythonic style and other HTML attributes.
        """
        base_style = {
            "padding": (8, 12),
            "font_size": 16,
            "border": "1px solid #ccc",
            "border_radius": 4,
            "width": "100%",
            "box_sizing": "border-box",
            "background_color": "white",
        }
        final_kwargs = {**base_style, **kwargs}

        option_components = []
        for option in options:
            if isinstance(option, str):
                option_value, display_text = option, option
            elif isinstance(option, tuple) and len(option) == 2:
                option_value, display_text = option
            else:
                raise TypeError(
                    "Options must be a list of strings or (value, text) tuples."
                )

            is_selected = value is not None and option_value == value
            option_components.append(
                Option(
                    value=option_value, children=[display_text], selected=is_selected
                )
            )

        super().__init__(children=option_components, name=name, **final_kwargs)


class PrimaryButton(Button):
    """
    A pre-styled, general-purpose button for primary actions.
    """

    def __init__(self, children: Optional[List[Any]] = None, **kwargs: Any):
        """
        Initializes a PrimaryButton instance.

        Args:
            children (Optional[List[Any]]): The button's label (e.g., "Click Me").
            **kwargs: Pythonic style and other HTML attributes. Defaults to type="button".
        """
        base_style = {
            "padding": (10, 20),
            "font_size": 16,
            "color": "white",
            "background_color": "#007bff",
            "border": "none",
            "border_radius": 5,
            "cursor": "pointer",
            "width": "auto",
        }
        default_hover_style = {"background_color": "#0056b3"}

        # Separate user's hover_style to prevent duplicate kwarg error
        user_hover_style = kwargs.pop("hover_style", {})
        final_hover_style = {**default_hover_style, **user_hover_style}

        # Merge remaining kwargs with base styles
        final_kwargs = {**base_style, **kwargs}

        # Default to 'button' unless overridden by the user
        if "type" not in final_kwargs:
            final_kwargs["type"] = "button"

        super().__init__(
            children=children,
            hover_style=final_hover_style,
            **final_kwargs,
        )


class SubmitButton(PrimaryButton):
    """
    A pre-styled button specifically for form submissions. Inherits styles from
    PrimaryButton but always has type="submit".
    """

    def __init__(self, children: Optional[List[Any]] = None, **kwargs: Any):
        """
        Initializes a SubmitButton instance.

        Args:
            children (Optional[List[Any]]): The button's label (e.g., "Submit").
            **kwargs: Pythonic style and other HTML attributes. `type` is always 'submit'.
        """
        # Force the type to be 'submit' and disallow overriding it
        if "type" in kwargs:
            del kwargs["type"]

        super().__init__(children=children, type="submit", **kwargs)


class FileUpload(Component):
    """
    A styled file upload component.
    """

    tag: str = "div"

    def __init__(
        self,
        name: str,
        label: str = "Click to upload a file",
        multiple: bool = False,
        **kwargs: Any,
    ):
        """
        Initializes a FileUpload instance.

        Args:
            name (str): The name of the input, used for form submission.
            label (str): The text to display in the upload area.
            multiple (bool): Whether to allow multiple file uploads.
            **kwargs: Pythonic style and HTML attributes for the wrapper div.
        """
        user_class = kwargs.pop("className", "")
        full_class = f"nolite-file-upload-wrapper {user_class}".strip()
        kwargs["className"] = full_class

        input_id = f"nolite-file-upload-{name}"

        file_input = Input(
            id=input_id,
            name=name,
            type="file",
            multiple=multiple,
            className="nolite-file-upload-input",
        )

        label_component = Label(
            for_id=input_id,
            className="nolite-file-upload-label",
            children=[label],
        )

        super().__init__(children=[file_input, label_component], **kwargs)
