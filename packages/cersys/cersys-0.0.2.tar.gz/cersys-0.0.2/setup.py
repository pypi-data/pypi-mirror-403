"""
Minimal setup.py to ensure platform-specific wheel is built.
The actual configuration is in pyproject.toml.
"""

from setuptools import setup
from setuptools.dist import Distribution


class BinaryDistribution(Distribution):
    """Distribution that forces a platform-specific wheel."""

    def has_ext_modules(self):
        return True


setup(distclass=BinaryDistribution)
