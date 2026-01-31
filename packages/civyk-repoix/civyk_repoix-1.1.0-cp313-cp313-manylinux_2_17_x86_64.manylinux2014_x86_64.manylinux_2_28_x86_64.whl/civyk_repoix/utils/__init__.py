"""Utility functions for civyk-repoix.

This package provides shared utility functions used across the codebase:

Submodules:
    - git_utils: Git log/diff parsing and repository operations
    - path_filter: Path filtering for indexing (skip node_modules, etc.)
    - language_filter: Source code vs documentation language detection
    - timing: Performance metrics collection and decorators

Exported Functions:
    - is_process_alive: Cross-platform process liveness check
    - verify_no_symlinks_in_path: Security check for symlink traversal
    - is_indexable_path: Check if path should be indexed
    - should_skip_directory: Check if directory should be skipped
    - is_non_api_file: Check if file is a non-API type (docs, SQL)
    - is_source_language: Check if language is source code
"""

import os
import sys
from pathlib import Path

from civyk_repoix.utils.language_filter import (
    NON_API_EXTENSIONS,
    SOURCE_LANGUAGES,
    get_source_language_placeholders,
    is_non_api_file,
    is_source_language,
)
from civyk_repoix.utils.path_filter import (
    ALLOWED_HIDDEN_DIRS,
    ALWAYS_SKIP_DIRS,
    GITHUB_ALLOWED_SUBDIRS,
    is_indexable_path,
    should_skip_directory,
    should_skip_path,
)

__all__ = [
    "ALLOWED_HIDDEN_DIRS",
    "ALWAYS_SKIP_DIRS",
    "GITHUB_ALLOWED_SUBDIRS",
    "NON_API_EXTENSIONS",
    "SOURCE_LANGUAGES",
    "get_source_language_placeholders",
    "is_indexable_path",
    "is_non_api_file",
    "is_process_alive",
    "is_source_language",
    "should_skip_directory",
    "should_skip_path",
    "verify_no_symlinks_in_path",
]


def is_process_alive(pid: int) -> bool:
    """Check if a process with the given PID is alive.

    Args:
        pid: Process ID to check.

    Returns:
        True if process is running, False otherwise.
    """
    if sys.platform == "win32":
        return _is_process_alive_windows(pid)
    return _is_process_alive_unix(pid)


def _is_process_alive_unix(pid: int) -> bool:
    """Check if process is alive on Unix."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _is_process_alive_windows(pid: int) -> bool:
    """Check if process is alive on Windows."""
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        STILL_ACTIVE = 259

        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False

        try:
            exit_code = wintypes.DWORD()
            if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
                return exit_code.value == STILL_ACTIVE
            return False
        finally:
            kernel32.CloseHandle(handle)
    except Exception:
        return False


def verify_no_symlinks_in_path(path: Path) -> None:
    """Verify no component in the path is a symlink.

    Security function to prevent symlink-based path traversal attacks.

    Args:
        path: Path to check.

    Raises:
        ValueError: If any path component is a symlink.
    """
    # Make path absolute if not already
    if not path.is_absolute():
        path = Path.cwd() / path

    # Check each component of the path from root to leaf
    current = Path(path.anchor)
    for part in path.parts[1:]:  # Skip the root/anchor
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Path contains symlink at: {current}")
