"""
Deprecated: Image models are deprecated in favor of File models.
Use File, FilePresigned, and FileConnection instead.
"""

from .file import File, FileConnection, FilePresigned

__all__ = ["Image", "ImagePresigned", "ImageConnection"]

# Backwards compatibility aliases
Image = File
ImagePresigned = FilePresigned
ImageConnection = FileConnection
