"""
Nolite Database Module

This module provides the shared SQLAlchemy database instance (`db`).

This instance should be imported into your main application file to be initialized
with the Flask app, and into your models file to define your database tables.
"""

from flask_sqlalchemy import SQLAlchemy

# Create a SQLAlchemy instance.
# This instance is not yet bound to a specific Flask application.
# It will be initialized in the NoliteApp class.
db = SQLAlchemy()
