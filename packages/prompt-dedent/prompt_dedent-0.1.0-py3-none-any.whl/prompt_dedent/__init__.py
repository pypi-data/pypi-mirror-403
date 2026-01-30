"""
Dedent - A library for writing multi-line strings with proper indentation in Python code.

This library allows you to write long, multi-line strings in your code with proper
indentation that matches your code structure, then automatically removes that
indentation from the final string.
"""

from .dedent import dedent, insert

__all__ = ["dedent", "insert"]
__version__ = "0.1.0"

