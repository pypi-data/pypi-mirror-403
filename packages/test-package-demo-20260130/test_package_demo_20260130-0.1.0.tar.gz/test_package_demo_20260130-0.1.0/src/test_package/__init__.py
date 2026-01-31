"""Test package for demonstrating Python package publishing."""

__version__ = "0.1.0"

from test_package.utils import add, greet

__all__ = ["add", "greet", "__version__"]
