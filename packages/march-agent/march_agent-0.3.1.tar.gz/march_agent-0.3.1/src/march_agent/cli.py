"""CLI interface for March AI Agent framework.

Inspired by uvicorn's simple pattern: march-agent run main:app
"""

import sys
import argparse
import importlib
from pathlib import Path


def import_from_string(import_str: str):
    """
    Import an attribute from a module using uvicorn-style string.

    Examples:
        "main:app" → imports 'app' from 'main' module
        "main:setup" → imports 'setup' from 'main' module
        "main" → imports 'main' module and looks for 'app' attribute

    Args:
        import_str: Import string in format "module:attribute" or "module"

    Returns:
        tuple: (module, attribute_name, attribute_value)
    """
    # Add current directory to path
    sys.path.insert(0, str(Path.cwd()))

    # Parse import string
    if ":" in import_str:
        module_str, attr_str = import_str.split(":", 1)
    else:
        module_str = import_str
        attr_str = "app"  # Default to 'app' like uvicorn

    # Import module
    try:
        module = importlib.import_module(module_str)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_str}': {e}")

    # Get attribute
    if not hasattr(module, attr_str):
        raise AttributeError(
            f"Module '{module_str}' has no attribute '{attr_str}'. "
            f"Please ensure you have '{attr_str} = MarchAgentApp(...)' in your file."
        )

    attr = getattr(module, attr_str)
    return module, attr_str, attr


def run_agent(import_str: str) -> None:
    """
    Load and run an agent using uvicorn-style import string.

    Args:
        import_str: Import string like "main:app" or "main"
    """
    from march_agent import MarchAgentApp

    print(f"Loading agent from: {import_str}")

    # Import the app
    module, attr_name, app = import_from_string(import_str)

    # Validate it's a MarchAgentApp
    if not isinstance(app, MarchAgentApp):
        raise TypeError(
            f"Attribute '{attr_name}' must be a MarchAgentApp instance, "
            f"got {type(app).__name__} instead."
        )

    print(f"Running {attr_name}.run()...")
    app.run()


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="march-agent",
        description="March AI Agent CLI - Run AI agents with uvicorn-style imports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  march-agent run main:app             Run 'app' from 'main' module (recommended)
  march-agent run main                 Run 'app' from 'main' module (defaults to :app)
  march-agent run myagent:application  Run 'application' from 'myagent' module

Your agent file should have:
  app = MarchAgentApp(...)

  @app.agent(name="...", about="...", document="...")
  def my_agent(message):
      # Handle message
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser(
        "run",
        help="Run an agent",
        description="Load and run a March AI agent using module:attribute syntax",
    )
    run_parser.add_argument(
        "app",
        help="Import path in format 'module:attribute' (e.g., main:app)",
    )

    # version command
    version_parser = subparsers.add_parser(
        "version",
        help="Show version information",
    )

    args = parser.parse_args()

    # Handle commands
    if args.command == "run":
        try:
            run_agent(args.app)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "version":
        from march_agent import __version__
        print(f"march-agent version {__version__}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
