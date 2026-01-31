"""File and process monitoring components.

This package provides monitoring infrastructure for real-time change detection
and process lifecycle management in the indexing service.

Components:
    FileWatcher: Watches directory tree for file changes with debouncing
    GitWatcher: Monitors git repository for branch changes
    ParentProcessWatcher: Monitors IDE parent process for graceful shutdown

Key Features:
    - Cross-platform file system monitoring via watchdog
    - 500ms debounce window to batch rapid file changes
    - Branch-specific database path management
    - LRU cleanup for old branch indexes
    - Disk quota enforcement for index storage
    - Unix/Windows parent process liveness detection

Usage:
    # File watching
    watcher = create_file_watcher(repo_root, on_file_change)
    watcher.start(asyncio.get_event_loop())

    # Git branch watching
    git_watcher = create_git_watcher(repo_root, data_dir, on_branch_change)
    await git_watcher.start()

    # Parent process watching
    parent_watcher = await watch_parent_process(parent_pid, on_exit)
"""

from civyk_repoix.monitors.file_watcher import (
    DebouncedEventHandler,
    FileEvent,
    FileEventType,
    FileWatcher,
    create_file_watcher,
)
from civyk_repoix.monitors.git_watcher import (
    BranchInfo,
    GitWatcher,
    create_git_watcher,
)
from civyk_repoix.monitors.parent_watcher import (
    ParentProcessWatcher,
    watch_parent_process,
)

__all__ = [
    "BranchInfo",
    "DebouncedEventHandler",
    "FileEvent",
    "FileEventType",
    "FileWatcher",
    "GitWatcher",
    "ParentProcessWatcher",
    "create_file_watcher",
    "create_git_watcher",
    "watch_parent_process",
]
