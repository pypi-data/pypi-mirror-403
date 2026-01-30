# ///////////////////////////////////////////////////////////////
# RUN_TESTS - Test Runner Script
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Test runner script for ezqt_widgets.

This script provides a convenient way to run tests with various
options including coverage reports and test filtering.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import argparse
import subprocess
import sys
from pathlib import Path

# ///////////////////////////////////////////////////////////////
# FUNCTIONS
# ///////////////////////////////////////////////////////////////


def run_command(cmd: str, description: str) -> bool:
    """
    Execute a command and display the result in real-time.

    Args:
        cmd: The command to execute as a string.
        description: Description of what the command does.

    Returns:
        bool: True if the command succeeded, False otherwise.
    """
    print(f"\n{'=' * 60}")
    print(f"🚀 {description}")
    print(f"{'=' * 60}\n")

    try:
        # Use Popen to stream output in real-time
        process = subprocess.Popen(  # noqa: S602, S603
            cmd,
            shell=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True,
            bufsize=1,  # Line buffered
        )

        # Wait for process to complete and get return code
        return_code = process.wait()
        return return_code == 0
    except Exception as e:
        print(f"❌ Error during execution: {e}", file=sys.stderr)
        return False


def main() -> None:
    """
    Main function.

    Parses command-line arguments and runs the appropriate tests.
    """
    parser = argparse.ArgumentParser(description="Test runner for ezqt_widgets")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "all"],
        default="unit",
        help="Type of tests to run",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate a coverage report",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose mode")
    parser.add_argument("--fast", action="store_true", help="Exclude slow tests")

    args = parser.parse_args()

    # Verify we are in the correct directory
    if not Path("pyproject.toml").exists():
        print(
            "❌ Error: pyproject.toml not found. Run this script from the project root."
        )
        sys.exit(1)

    # Build pytest command
    cmd_parts = ["python", "-m", "pytest"]

    if args.verbose:
        cmd_parts.append("-v")

    if args.fast:
        cmd_parts.extend(["-m", "not slow"])

    if args.type == "unit":
        cmd_parts.append("tests/unit/")
    elif args.type == "integration":
        cmd_parts.append("tests/integration/")
    else:  # "all"
        cmd_parts.append("tests/")

    if args.coverage:
        cmd_parts.extend(
            [
                "--cov=ezqt_widgets",
                "--cov-report=term-missing",
                "--cov-report=html:htmlcov",
            ]
        )

    cmd = " ".join(cmd_parts)

    # Execute tests
    success = run_command(cmd, f"Running {args.type} tests")

    if success:
        print("\n✅ Tests executed successfully!")

        if args.coverage:
            print("\n📊 Coverage report generated in htmlcov/")
            print("   Open htmlcov/index.html in your browser")
    else:
        print("\n❌ Test execution failed")
        sys.exit(1)


# ///////////////////////////////////////////////////////////////
# MAIN ENTRY POINT
# ///////////////////////////////////////////////////////////////

if __name__ == "__main__":
    main()
