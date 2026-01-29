"""
Lumecode - AI-powered coding agent with multi-model LLM support.

This Python package provides easy installation and management of the Lumecode CLI tool.
"""

__version__ = "1.0.0"
__author__ = "anonymus-netizien"

from .cli import main
from .installer import install, uninstall, get_binary_path

__all__ = ["main", "install", "uninstall", "get_binary_path", "__version__"]
