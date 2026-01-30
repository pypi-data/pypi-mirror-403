"""Unit tests for kubepath console."""

import pytest
from io import StringIO
from unittest.mock import patch

from kubepath.console import get_console, print_banner, KUBEPATH_THEME


class TestGetConsole:
    """Tests for the get_console function."""

    def test_returns_console(self):
        """Test that get_console returns a Console instance."""
        from rich.console import Console
        console = get_console()
        assert isinstance(console, Console)

    def test_singleton_pattern(self):
        """Test that get_console returns the same instance."""
        console1 = get_console()
        console2 = get_console()
        assert console1 is console2

    def test_console_uses_custom_theme(self):
        """Test that console uses the kubepath theme styles."""
        console = get_console()
        # Test that the console can render our custom styles
        # by checking if the style is recognized
        from rich.style import Style
        style = console.get_style("info")
        assert style is not None


class TestKubepathTheme:
    """Tests for the kubepath theme."""

    def test_theme_has_info_style(self):
        """Test that theme has info style."""
        assert "info" in KUBEPATH_THEME.styles

    def test_theme_has_error_style(self):
        """Test that theme has error style."""
        assert "error" in KUBEPATH_THEME.styles

    def test_theme_has_success_style(self):
        """Test that theme has success style."""
        assert "success" in KUBEPATH_THEME.styles

    def test_theme_has_chapter_style(self):
        """Test that theme has chapter style."""
        assert "chapter" in KUBEPATH_THEME.styles

    def test_theme_has_points_style(self):
        """Test that theme has points style."""
        assert "points" in KUBEPATH_THEME.styles


class TestPrintBanner:
    """Tests for the print_banner function."""

    def test_banner_prints_without_error(self):
        """Test that print_banner runs without raising."""
        # Just ensure it doesn't raise an exception
        print_banner()

    def test_banner_contains_kubepath(self):
        """Test that banner output contains kubepath ASCII art."""
        from rich.console import Console
        output = StringIO()
        console = Console(file=output, force_terminal=True)

        # Temporarily replace get_console to use our test console
        import kubepath.console as console_module
        original_console = console_module._console
        console_module._console = console

        try:
            print_banner()
            content = output.getvalue()
            # Check for parts of the ASCII art
            assert "kubepath" in content.lower() or "/_/" in content
        finally:
            console_module._console = original_console

    def test_banner_contains_learn_message(self):
        """Test that banner contains the learn message."""
        from rich.console import Console
        output = StringIO()
        console = Console(file=output, force_terminal=True)

        import kubepath.console as console_module
        original_console = console_module._console
        console_module._console = console

        try:
            print_banner()
            content = output.getvalue()
            assert "Learn Kubernetes" in content
        finally:
            console_module._console = original_console
