"""A client to Figshare."""

from .api import File, ensure_files, get_files

__all__ = [
    "File",
    "ensure_files",
    "get_files",
]
