"""
Application Factory and Package Initialization

This file initializes the core components of your Nolite application.
It creates the main app instance, configures the database, and registers
the routes and models.
"""

import os

# Import the full-stack framework components explicitly from nolite.framework
# This is the correct, robust way to import these objects.
from nolite.framework import NoliteApp, db

# Application Configuration

# Get the absolute path of the directory where this file resides.
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the path for the SQLite database file.
# It will be created in your project's root directory as 'app.db'.
DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, '..', 'app.db')}"


# Application Initialization

# Create the main Nolite application instance.
# This object, named 'app', is the central point of your application.
app = NoliteApp(__name__, db_uri=DATABASE_URI)


# Import Routes & Models
# These are imported at the end to avoid circular dependencies, as they
# will need to import the 'app' or 'db' objects defined above.
from . import routes, models
