"""
Nolite Extended Components

This module provides more complex, higher-level components that often combine
basic HTML components with pre-defined styles and behaviors to create common
UI patterns like layouts and modals.

Styling is handled via Pythonic keyword arguments (e.g., `bg_color`, `font_size`).
"""

from typing import List, Optional, Any, Dict

from .html_components import Div, Button, UnorderedList, ListItem, Anchor, Span
from ..core.component import Component


# Layout Components


class Container(Div):
    """
    A centered container component to limit the width of its content.

    This is useful for the main content area of a page on larger screens.
    """

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        **kwargs: Any,
    ):
        """
        Initializes a Container instance.

        Args:
            children (Optional[List[Any]]): The content of the container.
            **kwargs: Pythonic style and other HTML attributes.
                      Default `max_width` is "1140px".
        """
        base_styles = {
            "max_width": "1140px",
            "margin": "0 auto",
            "padding": (0, 20),
            "box_sizing": "border-box",
        }
        # User-provided kwargs will override the base styles
        final_kwargs = {**base_styles, **kwargs}
        super().__init__(children=children, **final_kwargs)


class Row(Div):
    """
    A layout component that arranges its children (typically Columns) in a row.

    This component uses CSS Flexbox.
    """

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        **kwargs: Any,
    ):
        """
        Initializes a Row instance.

        Args:
            children (Optional[List[Any]]): The columns or content of the row.
            **kwargs: Pythonic style and other HTML attributes.
        """
        base_styles = {
            "display": "flex",
            "flex_wrap": "wrap",
            "margin_left": -15,  # Gutter compensation
            "margin_right": -15,
        }
        final_kwargs = {**base_styles, **kwargs}
        super().__init__(children=children, **final_kwargs)


class Column(Div):
    """
    A layout component that represents a column within a Row.

    Should be used as a child of a Row component.
    """

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        **kwargs: Any,
    ):
        """
        Initializes a Column instance.

        Args:
            children (Optional[List[Any]]): The content of the column.
            **kwargs: Pythonic style and other HTML attributes.
        """
        base_styles = {
            "flex": "1",
            "padding_left": 15,  # Gutter
            "padding_right": 15,
            "box_sizing": "border-box",
            "min_width": 0,  # Prevents flexbox overflow issues
        }
        final_kwargs = {**base_styles, **kwargs}
        super().__init__(children=children, **final_kwargs)


# Interactive Components


class Modal(Component):
    """
    An interactive modal dialog that can be shown or hidden.

    The Modal is hidden by default and can be toggled by any component
    (like a Button) with an `on_click` action targeting the modal's ID.
    """

    tag: str = "div"

    def __init__(
        self,
        id: str,
        children: Optional[List[Any]] = None,
        show_close_button: bool = True,
        backdrop_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """
        Initializes a Modal instance.

        Args:
            id (str): A unique ID for the modal, used for targeting. Required.
            children (Optional[List[Any]]): The content to be displayed inside the modal.
            show_close_button (bool): If True, a default close button is added.
            backdrop_kwargs (Optional[Dict[str, Any]]): Pythonic style and HTML
                                                      attributes for the outer backdrop.
            **kwargs: Pythonic style and HTML attributes for the inner content wrapper.
        """
        if not id:
            raise ValueError("Modal component requires a unique 'id'.")
        self.id = id

        modal_content_children = children if children is not None else []

        if show_close_button:
            close_button = Button(
                children=["X"],  # The 'x' character
                className="nolite-modal-close",
                on_click={
                    "action": "toggle-class",
                    "target": f"#{self.id}",
                    "class": "is-visible",
                },
                aria_label="Close",
            )
            modal_content_children.insert(0, close_button)

        # The inner, styled content area
        modal_content = Div(
            className="nolite-modal-content",
            children=modal_content_children,
            **kwargs,
        )

        # The outer, backdrop div
        backdrop_kwargs = backdrop_kwargs or {}
        user_class = backdrop_kwargs.pop("className", "")
        full_class = f"nolite-modal-backdrop {user_class}".strip()

        super().__init__(
            id=self.id,
            className=full_class,
            children=[modal_content],
            **backdrop_kwargs,
        )


class ModalToggleButton(Button):
    """
    A helper Button pre-configured to toggle the visibility of a Modal.
    """

    def __init__(
        self,
        target_id: str,
        children: Optional[List[Any]] = None,
        **kwargs: Any,
    ):
        """
        Initializes a ModalToggleButton instance.

        Args:
            target_id (str): The ID of the Modal component to toggle.
            children (Optional[List[Any]]): The content of the button (e.g., "Open Modal").
            **kwargs: Pythonic style and HTML attributes for the button.
        """
        if not target_id:
            raise ValueError("ModalToggleButton requires a 'target_id'.")

        on_click_action = {
            "action": "toggle-class",
            "target": f"#{target_id}",
            "class": "is-visible",
        }

        super().__init__(children=children, on_click=on_click_action, **kwargs)


# UI Components


class Slider(Component):
    """
    An interactive carousel/slider component for displaying images or other content.

    This component is powered by a client-side JavaScript class and is highly
    customizable.
    """

    tag: str = "div"

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        show_arrows: bool = True,
        show_dots: bool = True,
        **kwargs: Any,
    ):
        """
        Initializes a Slider instance.

        Args:
            children (Optional[List[Any]]): A list of components that will act as the slides.
            show_arrows (bool): If True, displays previous/next navigation arrows.
            show_dots (bool): If True, displays dot indicators for navigation.
            **kwargs: Pythonic style and HTML attributes for the main slider container.
        """
        user_class = kwargs.pop("className", "")
        full_class = f"nolite-slider {user_class}".strip()
        kwargs["className"] = full_class

        # Add the main data attribute to activate the JS
        kwargs["data_nolite_component"] = "slider"

        # Build the Slider Internals

        # The track that holds the slides
        track = Div(
            className="nolite-slider-track",
            children=[
                Div(className="nolite-slider-slide", children=[slide])
                for slide in (children or [])
            ],
        )

        # Optional navigation arrows
        nav_arrows = []
        if show_arrows:
            nav_arrows = [
                Button(
                    className="nolite-slider-nav prev",
                    children=["&#10094;"],
                    aria_label="Previous Slide",
                ),
                Button(
                    className="nolite-slider-nav next",
                    children=["&#10095;"],
                    aria_label="Next Slide",
                ),
            ]

        # Optional navigation dots
        dots = []
        if show_dots:
            dots = [Div(className="nolite-slider-dots")]

        # Assemble the final component structure
        slider_children = [track] + nav_arrows + dots
        super().__init__(children=slider_children, **kwargs)


class Card(Div):
    """
    A versatile and pre-styled container for content.
    """

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        **kwargs: Any,
    ):
        """
        Initializes a Card instance.

        Args:
            children (Optional[List[Any]]): The content of the card.
            **kwargs: Pythonic style and HTML attributes.
        """
        user_class = kwargs.pop("className", "")
        full_class = f"nolite-card {user_class}".strip()
        super().__init__(children=children, className=full_class, **kwargs)


class Alert(Div):
    """
    A component for displaying success, warning, or error messages.
    """

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        status: str = "success",  # 'success', 'warning', or 'error'
        **kwargs: Any,
    ):
        """
        Initializes an Alert instance.

        Args:
            children (Optional[List[Any]]): The message to display.
            status (str): The type of alert. Can be 'success', 'warning', or 'error'.
            **kwargs: Pythonic style and HTML attributes.
        """
        if status not in ["success", "warning", "error"]:
            raise ValueError("Alert status must be 'success', 'warning', or 'error'.")

        user_class = kwargs.pop("className", "")
        status_class = f"nolite-alert-{status}"
        full_class = f"nolite-alert {status_class} {user_class}".strip()

        super().__init__(children=children, className=full_class, **kwargs)


class Navbar(Component):
    """
    A responsive navigation bar component.
    """

    tag: str = "nav"

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        **kwargs: Any,
    ):
        """
        Initializes a Navbar instance.

        Args:
            children (Optional[List[Any]]): The content of the navbar, typically
                                          NavbarBrand and NavbarLinks.
            **kwargs: Pythonic style and HTML attributes.
        """
        user_class = kwargs.pop("className", "")
        full_class = f"nolite-navbar {user_class}".strip()
        super().__init__(children=children, className=full_class, **kwargs)


class NavbarBrand(Div):
    """
    The branding section of a Navbar, for a logo or title.
    """

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        **kwargs: Any,
    ):
        """
        Initializes a NavbarBrand instance.

        Args:
            children (Optional[List[Any]]): The brand content (e.g., text, an Image).
            **kwargs: Pythonic style and HTML attributes.
        """
        user_class = kwargs.pop("className", "")
        full_class = f"nolite-navbar-brand {user_class}".strip()
        super().__init__(children=children, className=full_class, **kwargs)


class NavbarLinks(UnorderedList):
    """
    A container for navigation links within a Navbar.
    """

    def __init__(
        self,
        children: Optional[List[Any]] = None,
        **kwargs: Any,
    ):
        """
        Initializes a NavbarLinks instance.

        Args:
            children (Optional[List[Any]]): The list items containing links.
            **kwargs: Pythonic style and HTML attributes.
        """
        user_class = kwargs.pop("className", "")
        full_class = f"nolite-navbar-links {user_class}".strip()
        super().__init__(children=children, className=full_class, **kwargs)
