"""
Nolite Full-Stack Framework Core

This package contains the core classes for building full-stack Nolite applications,
including the main application object, database integration, and routing.
"""

from .app import NoliteApp
from .database import db

__all__ = [
    "NoliteApp",
    "db",
]
