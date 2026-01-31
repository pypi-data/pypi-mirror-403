"""
Ant Client - Python client for Anthive REST API.

Simple, secure, and fast client for querying single-cell expression databases.
"""

from .client import AntClient

__version__ = "0.3.0"
__all__ = ["AntClient", "sql"]

# Import sql module
from . import sql

# Widgets module temporarily shelved
# To re-enable: rename widgets.py.shelved → widgets.py
# try:
#     from . import widgets
#     __all__.append("widgets")
# except ImportError:
#     # ipywidgets not installed
#     widgets = None
widgets = None
