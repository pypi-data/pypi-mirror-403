"""
Database Models

This file defines the structure of your database tables. Each class that inherits
from `db.Model` will be translated into a table in your database.
"""

# Import the shared database instance from the app package
from . import db


# -----------------------------------------------------------------------------
# User Model
# -----------------------------------------------------------------------------
# This is an example model that creates a 'user' table in the database.
# You can use it as a template for your own models.
# -----------------------------------------------------------------------------
class User(db.Model):
    """Represents a user in the database."""

    # `id`: The primary key for the table. It is an integer that
    #       auto-increments for each new user.
    id = db.Column(db.Integer, primary_key=True)

    # `username`: A unique, non-empty string to identify the user.
    username = db.Column(db.String(80), unique=True, nullable=False)

    # `email`: The user's email address. It must also be unique and non-empty.
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        """
        Provides a developer-friendly string representation of a User object,
        which is useful for debugging.
        """
        return f"<User {self.username}>"
