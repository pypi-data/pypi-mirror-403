"""
Reusable Layout Components


This file contains reusable layout components, such as a main page layout,
to ensure a consistent look and feel across your application.
"""

from flask import url_for

from nolite import Page
from nolite.components import (
    # Layout & UI
    Navbar,
    NavbarBrand,
    NavbarLinks,
    Container,
    Footer,
    Main,
    # Text & Links
    Anchor,
    ListItem,
    Paragraph,
)


def main_layout(children, title="My Nolite App"):
    """
    A reusable layout component that provides a consistent page structure.

    Args:
        children (list): A list of Nolite components to be rendered in the main content area.
        title (str): The title of the page for the browser tab.

    Returns:
        A Nolite Page object with the standard layout.
    """
    return Page(
        title=title,
        # Add a link to the application's stylesheet.
        # Files in the 'static' directory are served automatically.
        stylesheets=[url_for("static", filename="css/style.css")],
        # Set global styles on the top-level Page component
        font_family="sans-serif",
        bg_color="#f9fafb",
        children=[
            Navbar(
                bg_color="white",
                box_shadow="0 2px 4px rgba(0,0,0,0.1)",
                children=[
                    NavbarBrand(
                        children=[Anchor(href="/", children=["NoliteProject"])]
                    ),
                    NavbarLinks(
                        children=[
                            ListItem(children=[Anchor(href="/", children=["Home"])])
                        ]
                    ),
                ],
            ),
            Main(
                # Use min_height to ensure the footer stays at the bottom on short pages
                min_height="calc(100vh - 120px)",
                children=[
                    Container(padding_top=40, padding_bottom=40, children=children)
                ],
            ),
            Footer(
                bg_color="#e9ecef",
                padding=20,
                text_align="center",
                color="#6c757d",
                children=[Paragraph(children=["Powered by the Nolite Framework"])],
            ),
        ],
    )
