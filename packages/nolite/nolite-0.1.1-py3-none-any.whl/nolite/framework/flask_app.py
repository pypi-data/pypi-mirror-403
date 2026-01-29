"""
This module contains the architectural core of the Nolite rendering engine.

The `NoliteFlask` class defined here is a custom subclass of the standard Flask
application class. Its sole, critical purpose is to override the `make_response`
method. This override is the "magic" that allows your view functions to return
native Nolite `Page` objects, which are then automatically rendered into HTML
before being sent to the browser.

By centralizing this logic here, the framework seamlessly integrates with all
standard Flask features, including Blueprints, without requiring any special
decorators or hooks in your application code.
"""

from flask import Flask
from nolite.core.page import Page


class NoliteFlask(Flask):
    """A custom Flask app subclass that enables returning Nolite Page objects from views."""

    def make_response(self, rv):
        """
        Overrides the default `make_response` to automatically render Nolite `Page` objects.

        This method is the central point of Nolite's integration with Flask. It
        intercepts the return value (`rv`) of any view function.

        - If `rv` is a Nolite `Page`, it is rendered to an HTML string before being
          passed to Flask's original `make_response` method.
        - For any other return type (e.g., a `redirect` or a raw string), it
          behaves exactly like the standard `make_response`.

        Args:
            rv (any): The return value from a Flask view function.

        Returns:
            A valid Flask Response object.
        """
        if isinstance(rv, Page):
            # The return value is a Nolite Page. Render it to HTML.
            rendered_html = rv.render()
            # Let the original Flask `make_response` handle the rendered string.
            return super().make_response(rendered_html)

        # The return value is not a Page (e.g., a redirect), so we let Flask
        # handle it with its default behavior.
        return super().make_response(rv)
