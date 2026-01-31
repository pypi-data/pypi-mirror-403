"""
Safe utilities module for fishertools.

This module provides beginner-friendly versions of common operations
that prevent typical mistakes and provide helpful error messages.
"""

from .collections import safe_get, safe_divide, safe_max, safe_min, safe_sum
from .files import (
    safe_read_file, safe_write_file, safe_file_exists, safe_get_file_size, safe_list_files,
    safe_open, find_file, project_root, ensure_dir, get_file_hash, read_last_lines
)
from .strings import safe_string_operations

__all__ = [
    "safe_get", "safe_divide", "safe_max", "safe_min", "safe_sum",
    "safe_read_file", "safe_write_file", "safe_file_exists", "safe_get_file_size", "safe_list_files",
    "safe_open", "find_file", "project_root",
    "ensure_dir", "get_file_hash", "read_last_lines",
    "safe_string_operations"
]