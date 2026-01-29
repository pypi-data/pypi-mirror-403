import os
from typing import Callable, Any
from .flask_app import NoliteFlask
from .database import db


class NoliteApp:
    """
    The main application class for a full-stack Nolite project.

    This class acts as a factory and central hub for your application. It
    initializes the core components:
    - The custom `NoliteFlask` app for rendering.
    - The SQLAlchemy database connection (`db`).
    - Configuration for file uploads.

    An instance of this class is typically created as `app` in your project's
    `app/__init__.py` file.
    """

    def __init__(
        self,
        import_name: str,
        db_uri: str = "sqlite:///nolite_app.db",
        upload_folder: str = "uploads",
    ):
        """
        Initializes the Nolite application.

        Args:
            import_name (str): The name of the application package, typically `__name__`.
            db_uri (str): The database connection URI. Defaults to a local SQLite database.
            upload_folder (str): The directory to store uploaded files.
        """
        # This is the core Flask application object, customized for Nolite.
        self.app = NoliteFlask(import_name)
        self.upload_folder = os.path.abspath(upload_folder)

        # Configure the SQLAlchemy database URI.
        self.app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        # Initialize the database with the Flask app.
        db.init_app(self.app)

        # Configure the folder where file uploads will be saved.
        self.app.config["UPLOAD_FOLDER"] = self.upload_folder
        os.makedirs(self.upload_folder, exist_ok=True)

        print(f" * Database URI: {self.app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f" * Upload folder: {self.app.config['UPLOAD_FOLDER']}")

    def route(self, rule: str, **options: Any) -> Callable:
        """
        A decorator to register a view function for a given URL rule.

        This is a direct wrapper around Flask's own route decorator, provided
        as a convenience for simple, single-file applications.

        For building scalable, modular applications, it is highly recommended to
        use Flask's standard Blueprint objects, as demonstrated in the Nolite
        Shop e-commerce example. Nolite's rendering engine is designed to work
        seamlessly with Blueprints.
        """
        return self.app.route(rule, **options)

    def run(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = True):
        """
        Starts the Nolite development server.

        This method serves two key purposes:
        1. It ensures that all database tables defined in your models are
           created before the application starts.
        2. It starts the underlying Flask development server.

        Args:
            host (str): The hostname to listen on.
            port (int): The port of the web server.
            debug (bool): If True, the server will automatically reload on code changes.
        """
        # Use an application context to safely interact with the database.
        with self.app.app_context():
            print(" * Creating database tables...")
            # SQLAlchemy's create_all() is idempotent - it will only create tables
            # that do not already exist.
            db.create_all()
            print(" * Database tables created.")

        print(f" * Nolite server running on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)
