# ///////////////////////////////////////////////////////////////
# CLI_MAIN - CLI Main Entry Point
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
EzQt Widgets CLI - Main entry point.

Command-line interface for running examples and utilities.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import subprocess
import sys

# Third-party imports
import click

# Local imports
from .runner import (
    list_available_examples,
    run_all_examples,
    run_example_by_category,
)

# ///////////////////////////////////////////////////////////////
# CLI COMMANDS
# ///////////////////////////////////////////////////////////////


@click.group()
@click.version_option(version="1.0.0", prog_name="EzQt Widgets CLI")
def cli() -> None:
    """EzQt Widgets CLI - Launch examples and utilities.

    A command-line interface for running EzQt Widgets examples
    and managing the development workflow.
    """


@cli.command()
@click.option(
    "--all", "-a", "run_all", is_flag=True, help="Run all examples with GUI launcher"
)
@click.option(
    "--buttons",
    "-b",
    is_flag=True,
    help="Run button examples (DateButton, IconButton, LoaderButton)",
)
@click.option(
    "--inputs",
    "-i",
    is_flag=True,
    help="Run input examples (AutoComplete, Password, Search, TabReplace)",
)
@click.option(
    "--labels",
    "-l",
    is_flag=True,
    help="Run label examples (ClickableTag, Framed, Hover, Indicator)",
)
@click.option(
    "--misc",
    "-m",
    is_flag=True,
    help="Run misc examples (CircularTimer, DraggableList, OptionSelector, ToggleIcon, ToggleSwitch)",
)
@click.option(
    "--no-gui", is_flag=True, help="Run examples sequentially without GUI launcher"
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Verbose output with detailed information"
)
def run(
    run_all: bool,
    buttons: bool,
    inputs: bool,
    labels: bool,
    misc: bool,
    no_gui: bool,
    verbose: bool,
) -> None:
    """Run EzQt Widgets examples.

    Launch interactive examples to explore widget functionality.
    Use --help for available options.
    """
    # Check if any option is selected
    options_selected = any([run_all, buttons, inputs, labels, misc])

    if not options_selected:
        click.echo("❌ Please specify which examples to run.")
        click.echo("\n📋 Available options:")
        click.echo("  --all, -a        Run all examples with GUI launcher")
        click.echo("  --buttons, -b    Run button examples")
        click.echo("  --inputs, -i     Run input examples")
        click.echo("  --labels, -l     Run label examples")
        click.echo("  --misc, -m       Run misc examples")
        click.echo("\n💡 Example: ezqt run --buttons")
        return

    if verbose:
        click.echo("🔍 Verbose mode enabled")

    # Run selected examples
    success = True

    if run_all:
        click.echo("🎯 Running all examples...")
        success = run_all_examples(use_gui=not no_gui, verbose=verbose)

    elif buttons:
        click.echo("🎛️  Running button examples...")
        success = run_example_by_category("buttons", verbose)

    elif inputs:
        click.echo("⌨️  Running input examples...")
        success = run_example_by_category("inputs", verbose)

    elif labels:
        click.echo("🏷️  Running label examples...")
        success = run_example_by_category("labels", verbose)

    elif misc:
        click.echo("🔧 Running misc examples...")
        success = run_example_by_category("misc", verbose)

    if success:
        click.echo("✅ Examples completed successfully!")
    else:
        click.echo("❌ Some examples failed to run.")
        sys.exit(1)


@cli.command()
def list() -> None:
    """List available examples.

    Show all available example files and their status.
    """
    list_available_examples()


@cli.command()
@click.option("--unit", "-u", is_flag=True, help="Run unit tests")
@click.option("--coverage", "-c", is_flag=True, help="Run tests with coverage")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def test(unit: bool, coverage: bool, verbose: bool) -> None:
    """Run tests.

    Execute the test suite for EzQt Widgets.
    """
    if not any([unit, coverage]):
        # Default to unit tests
        unit = True

    try:
        if unit:
            click.echo("🧪 Running unit tests...")
            cmd = ["python", "-m", "pytest", "tests/unit/"]
            if verbose:
                cmd.append("-v")
            subprocess.run(cmd, check=True)  # noqa: S603

        if coverage:
            click.echo("📊 Running tests with coverage...")
            cmd = [
                "python",
                "-m",
                "pytest",
                "--cov=ezqt_widgets",
                "--cov-report=html",
            ]
            if verbose:
                cmd.append("-v")
            subprocess.run(cmd, check=True)  # noqa: S603
            click.echo("📈 Coverage report generated in htmlcov/")

        click.echo("✅ Tests completed successfully!")

    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Tests failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        click.echo("❌ pytest not found. Install with: pip install pytest")
        sys.exit(1)


@cli.command()
@click.option("--serve", "-s", is_flag=True, help="Serve documentation locally")
@click.option("--port", "-p", default=8000, help="Port for documentation server")
def docs(serve: bool, port: int) -> None:
    """Documentation utilities.

    Access and manage EzQt Widgets documentation.
    """
    if serve:
        try:
            import http.server
            import os
            import socketserver

            # Change to docs directory
            docs_dir = os.path.join(os.path.dirname(__file__), "..", "..", "docs")
            if os.path.exists(docs_dir):
                os.chdir(docs_dir)
                click.echo(f"📖 Serving documentation at http://localhost:{port}")
                click.echo("Press Ctrl+C to stop the server")

                with socketserver.TCPServer(
                    ("", port), http.server.SimpleHTTPRequestHandler
                ) as httpd:
                    httpd.serve_forever()
            else:
                click.echo("❌ Documentation directory not found")

        except KeyboardInterrupt:
            click.echo("\n⏹️  Documentation server stopped")
        except Exception as e:
            click.echo(f"❌ Error serving documentation: {e}")
    else:
        click.echo("📖 Documentation options:")
        click.echo("  --serve, -s     Serve documentation locally")
        click.echo("  --port, -p      Specify port (default: 8000)")
        click.echo("\n💡 Example: ezqt docs --serve --port 8080")


@cli.command()
def info() -> None:
    """Show package information.

    Display information about EzQt Widgets installation.
    """
    try:
        import ezqt_widgets

        click.echo("🎨 EzQt Widgets Information")
        click.echo("=" * 40)
        click.echo(f"Version: {getattr(ezqt_widgets, '__version__', 'Unknown')}")
        click.echo(f"Location: {ezqt_widgets.__file__}")

        # Check PySide6
        try:
            import PySide6

            click.echo(f"PySide6: {PySide6.__version__}")
        except ImportError:
            click.echo("PySide6: Not installed")

        # Check examples
        from .runner import ExampleRunner

        try:
            runner = ExampleRunner()
            examples = runner.get_available_examples()
            click.echo(f"Examples: {len(examples)} found")
        except FileNotFoundError:
            click.echo("Examples: Not found")

        click.echo("=" * 40)

    except ImportError:
        click.echo("❌ EzQt Widgets not found in current environment")


# ///////////////////////////////////////////////////////////////
# MAIN ENTRY POINT
# ///////////////////////////////////////////////////////////////

if __name__ == "__main__":
    cli()
