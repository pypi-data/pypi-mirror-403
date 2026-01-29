import argparse
import os
import shutil
import sys


def new_project(args):
    """
    Handles the creation of a new Nolite project from the starter template.
    """
    project_name = args.project_name

    # The path where the new project will be created (current working directory)
    dest_path = os.path.join(os.getcwd(), project_name)

    # Check if a directory with the same name already exists
    if os.path.exists(dest_path):
        print(f"Error: Directory '{project_name}' already exists.", file=sys.stderr)
        sys.exit(1)

    # Find the path to the starter template.
    # It is located inside the installed 'nolite' package.
    try:
        # __file__ gives the path to the current script (cli.py)
        # We navigate from here to the template directory.
        source_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "nolite_starter_template"
        )
        if not os.path.isdir(source_path):
            raise FileNotFoundError
    except (NameError, FileNotFoundError):
        print("Error: Could not find the project template.", file=sys.stderr)
        print(
            "Please ensure your Nolite installation is not corrupted.", file=sys.stderr
        )
        sys.exit(1)

    # Copy the template directory to the destination
    try:
        shutil.copytree(source_path, dest_path)
    except OSError as e:
        print(f"Error: Could not create project directory. {e}", file=sys.stderr)
        sys.exit(1)

    print(f"#> Successfully created Nolite project '{project_name}'.")
    print("\nTo get started, run the following commands:")
    print(f"  > cd {project_name}")
    print("  > python run.py")
    print("\nYour new Nolite application will be running at http://127.0.0.1:5000")


def main():
    """
    The main entry point for the Nolite command-line interface.
    """
    parser = argparse.ArgumentParser(
        prog="nolite",
        description="The official command-line interface for the Nolite framework.",
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )

    # 'new' command
    new_parser = subparsers.add_parser(
        "new",
        help="Create a new Nolite project from the starter template.",
        description="Creates a new directory with a minimal, ready-to-run Nolite application.",
    )
    new_parser.add_argument(
        "project_name",
        help="The name of the new project directory to be created.",
    )
    new_parser.set_defaults(func=new_project)

    args = parser.parse_args()

    # Execute the function associated with the chosen command
    args.func(args)


if __name__ == "__main__":
    main()
