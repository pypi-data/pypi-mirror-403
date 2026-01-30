"""Example test file to demonstrate testing setup."""

from appdevcommons import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_package_import():
    """Test that the package can be imported."""
    import appdevcommons

    assert appdevcommons is not None
