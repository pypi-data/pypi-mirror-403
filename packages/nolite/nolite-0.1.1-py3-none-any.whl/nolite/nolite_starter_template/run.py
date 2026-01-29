"""
Main entry point for the Nolite application.

To run the application, execute this script from your terminal:
    python run.py
"""

# Import the main application object from our 'app' package.
# The app package handles all initialization and registration.
from app import app

# Start the Nolite development server.
if __name__ == "__main__":
    # The run method handles database creation (if any models exist)
    # and starts the Flask server.
    app.run()
