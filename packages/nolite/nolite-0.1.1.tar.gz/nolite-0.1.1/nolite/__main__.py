"""
Nolite Executable Entry Point

This file makes the 'nolite' package runnable using the `python -m nolite` command.
It now directly calls the main function from the cli module to avoid triggering
the package's main __init__.py and its dependencies during CLI execution.
"""

import sys
from nolite.cli import main

if __name__ == "__main__":
    # This ensures that if the script is run directly, it executes the CLI
    sys.exit(main())
