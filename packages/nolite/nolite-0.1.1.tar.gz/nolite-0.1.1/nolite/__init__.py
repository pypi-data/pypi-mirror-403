"""
Nolite: The Full-Stack Python Web Framework

This is the main package for the Nolite framework.

To build a full-stack application, you will primarily use components
imported from the `nolite.framework` and `nolite.components` modules.

Basic Usage:
    from nolite.framework import NoliteApp, db
    from nolite.components import H1, Paragraph
    from nolite import Page
"""

__version__ = "1.0.0"

# Core Building Blocks
# These are the fundamental, dependency-light classes for creating UI.
# They are safe to import at the top level.
from .core.page import Page
from .core.component import Component

# Note: The full-stack components like `NoliteApp` and `db` are NOT
# imported here. They should be explicitly imported from `nolite.framework`
# by the user. This prevents dependency issues when using the CLI tool
# and follows best practices for large framework design.

__all__ = [
    "Page",
    "Component",
]
