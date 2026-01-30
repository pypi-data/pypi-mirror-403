"""Basic tests for chimpy-me package."""

from chimpy_me import __version__


def test_version():
    """Test that version is defined and has expected format."""
    assert __version__ == "0.0.1a1"
