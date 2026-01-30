# ///////////////////////////////////////////////////////////////
# CONFTEST - Pytest Configuration
# Project: ezqt_widgets
# ///////////////////////////////////////////////////////////////

"""
Pytest configuration for ezqt_widgets unit tests.

This module contains pytest fixtures and configuration for all tests.
"""

from __future__ import annotations

# ///////////////////////////////////////////////////////////////
# IMPORTS
# ///////////////////////////////////////////////////////////////
# Standard library imports
import sys

# Third-party imports
import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

# ///////////////////////////////////////////////////////////////
# FIXTURES
# ///////////////////////////////////////////////////////////////


@pytest.fixture(scope="session")
def qt_application() -> QApplication:
    """
    Create a QApplication instance for all tests.

    This fixture is necessary for testing Qt widgets. It creates a
    single QApplication instance that is shared across all tests in
    the session.

    Yields:
        QApplication: The Qt application instance.

    Note:
        The application is automatically cleaned up after all tests
        are completed.
    """
    # Create Qt application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    yield app

    # Cleanup after tests
    app.quit()


@pytest.fixture
def qt_widget_cleanup(qt_application: QApplication) -> QApplication:
    """
    Clean up widgets after each test.

    This fixture ensures that all Qt events are processed after each
    test, which helps prevent widget-related issues between tests.

    Args:
        qt_application: The Qt application instance.

    Yields:
        QApplication: The Qt application instance.
    """
    yield qt_application

    # Force widget cleanup
    qt_application.processEvents()


@pytest.fixture
def wait_for_signal(qt_application: QApplication):
    """
    Wait for a signal to be emitted.

    This fixture provides a helper function to wait for Qt signals
    to be emitted with an optional timeout.

    Args:
        qt_application: The Qt application instance.

    Yields:
        A function that waits for a signal to be emitted.

    Example:
        ```python
        def test_signal(wait_for_signal):
            signal = SomeWidget.someSignal
            result = wait_for_signal(signal, timeout=1000)
            assert result
        ```
    """

    def _wait_for_signal(signal, timeout: int = 1000) -> bool:
        """
        Wait for a signal to be emitted with a timeout.

        Args:
            signal: The Qt signal to wait for.
            timeout: Maximum time to wait in milliseconds. Defaults to 1000.

        Returns:
            bool: True if the signal was emitted before timeout, False otherwise.
        """
        timer = QTimer()
        timer.setSingleShot(True)
        timer.start(timeout)

        # Connect signal to a slot that stops the timer
        def stop_timer() -> None:
            timer.stop()

        signal.connect(stop_timer)

        # Wait for timer to stop
        while timer.isActive():
            qt_application.processEvents()

        return not timer.isActive()

    return _wait_for_signal


@pytest.fixture
def mock_icon_path(tmp_path):
    """
    Create a temporary icon file path.

    This fixture creates a minimal PNG icon file for testing purposes.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        str: Path to the temporary icon file.
    """
    icon_file = tmp_path / "test_icon.png"
    # Create a simple temporary icon file
    with open(icon_file, "wb") as f:
        # Minimal PNG header
        f.write(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xf5\xc7\xd3\xf7\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    return str(icon_file)


@pytest.fixture
def mock_svg_path(tmp_path):
    """
    Create a temporary SVG file path.

    This fixture creates a minimal SVG file for testing purposes.

    Args:
        tmp_path: Pytest temporary path fixture.

    Returns:
        str: Path to the temporary SVG file.
    """
    svg_file = tmp_path / "test_icon.svg"
    # Create a simple temporary SVG file
    svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="16" height="16" xmlns="http://www.w3.org/2000/svg">
    <rect width="16" height="16" fill="red"/>
</svg>"""

    with open(svg_file, "w", encoding="utf-8") as f:
        f.write(svg_content)

    return str(svg_file)
