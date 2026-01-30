# ///////////////////////////////////////////////////////////////
# CLI_RUNNER - Example Runner Module
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Example runner module for EzQt Widgets CLI.

Handles the execution of example files with proper error handling and feedback.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import os
import subprocess
import sys
from pathlib import Path

# Third-party imports
import click

# ///////////////////////////////////////////////////////////////
# CLASSES
# ///////////////////////////////////////////////////////////////


class ExampleRunner:
    """Handles running EzQt Widgets examples.

    Provides functionality to discover, list, and execute example files
    from the EzQt Widgets package.

    Args:
        verbose: Whether to enable verbose output (default: False).
    """

    # ///////////////////////////////////////////////////////////////
    # INIT
    # ///////////////////////////////////////////////////////////////

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the example runner."""
        self.verbose: bool = verbose
        self.examples_dir: Path = self._find_examples_dir()

    # ------------------------------------------------
    # PRIVATE METHODS
    # ------------------------------------------------

    def _find_examples_dir(self) -> Path:
        """Find the examples directory relative to the package.

        Returns:
            Path to the examples directory.

        Raises:
            FileNotFoundError: If the examples directory cannot be found.
        """
        # First priority: examples in the project root
        package_dir = Path(__file__).parent.parent.parent
        examples_dir = package_dir / "examples"

        if examples_dir.exists():
            return examples_dir

        # Second priority: examples inside the package (ezqt_widgets/examples/)
        package_examples = Path(__file__).parent.parent / "examples"
        if package_examples.exists():
            return package_examples

        # Fallback: try to find examples in the current directory
        current_examples = Path.cwd() / "examples"
        if current_examples.exists():
            return current_examples

        raise FileNotFoundError("Examples directory not found")

    def _execute_example(self, example_path: Path) -> bool:
        """Execute a specific example file.

        Args:
            example_path: Path to the example file to execute.

        Returns:
            True if execution was successful, False otherwise.
        """
        if self.verbose:
            click.echo(f"🚀 Running: {example_path.name}")

        try:
            # Change to the examples directory to ensure relative imports work
            original_cwd = os.getcwd()
            os.chdir(example_path.parent)

            result = subprocess.run(  # noqa: S603
                [sys.executable, str(example_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Restore original working directory
            os.chdir(original_cwd)

            if result.returncode != 0:
                click.echo(f"❌ Error running {example_path.name}: {result.stderr}")
                return False

            return True

        except subprocess.TimeoutExpired:
            click.echo(f"⏰ Timeout running {example_path.name}")
            return False
        except Exception as e:
            click.echo(f"❌ Exception running {example_path.name}: {e}")
            return False

    # ///////////////////////////////////////////////////////////////
    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////

    def get_available_examples(self) -> list[Path]:
        """Get list of available example files.

        Returns:
            List of paths to available example files.
        """
        examples: list[Path] = []
        for pattern in ["*_example.py", "run_all_examples.py"]:
            examples.extend(self.examples_dir.glob(pattern))
        return sorted(examples)

    def run_example(self, example_name: str) -> bool:
        """Run a specific example by name.

        Args:
            example_name: Name of the example to run (without .py extension).

        Returns:
            True if execution was successful, False otherwise.
        """
        example_path = self.examples_dir / f"{example_name}.py"

        if not example_path.exists():
            click.echo(f"❌ Example not found: {example_name}")
            return False

        return self._execute_example(example_path)

    def run_all_examples(self, use_gui_launcher: bool = True) -> bool:
        """Run all examples or use the GUI launcher.

        Args:
            use_gui_launcher: Whether to use the GUI launcher if available
                (default: True).

        Returns:
            True if all examples ran successfully, False otherwise.
        """
        if use_gui_launcher:
            launcher_path = self.examples_dir / "run_all_examples.py"
            if launcher_path.exists():
                return self._execute_example(launcher_path)
            else:
                click.echo("⚠️  GUI launcher not found, running examples sequentially")
                use_gui_launcher = False

        if not use_gui_launcher:
            # Run each example sequentially
            examples = [
                "button_example",
                "input_example",
                "label_example",
                "misc_example",
            ]
            success_count = 0

            for example in examples:
                click.echo(f"\n{'=' * 50}")
                click.echo(f"🚀 Running: {example}")
                click.echo(f"{'=' * 50}")

                if self.run_example(example):
                    success_count += 1
                else:
                    click.echo(f"❌ Failed to run: {example}")

            click.echo(
                f"\n✅ Successfully ran {success_count}/{len(examples)} examples"
            )
            return success_count == len(examples)

        return False

    def list_examples(self) -> None:
        """List all available examples."""
        examples = self.get_available_examples()

        if not examples:
            click.echo("❌ No examples found")
            return

        click.echo("📋 Available examples:")
        click.echo("=" * 40)

        for example in examples:
            status = "✅" if example.exists() else "❌"
            click.echo(f"{status} {example.stem}")

        click.echo(f"\nTotal: {len(examples)} examples found")


# ///////////////////////////////////////////////////////////////
# PUBLIC FUNCTIONS
# ///////////////////////////////////////////////////////////////


def run_example_by_category(category: str, verbose: bool = False) -> bool:
    """Run examples by category.

    Args:
        category: Category name (buttons, inputs, labels, misc).
        verbose: Whether to enable verbose output (default: False).

    Returns:
        True if execution was successful, False otherwise.
    """
    runner = ExampleRunner(verbose)

    category_mapping = {
        "buttons": "button_example",
        "inputs": "input_example",
        "labels": "label_example",
        "misc": "misc_example",
    }

    if category not in category_mapping:
        click.echo(f"❌ Unknown category: {category}")
        click.echo(f"Available categories: {', '.join(category_mapping.keys())}")
        return False

    return runner.run_example(category_mapping[category])


def run_all_examples(use_gui: bool = True, verbose: bool = False) -> bool:
    """Run all examples.

    Args:
        use_gui: Whether to use the GUI launcher if available (default: True).
        verbose: Whether to enable verbose output (default: False).

    Returns:
        True if all examples ran successfully, False otherwise.
    """
    runner = ExampleRunner(verbose)
    return runner.run_all_examples(use_gui)


def list_available_examples() -> None:
    """List all available examples."""
    runner = ExampleRunner()
    runner.list_examples()
