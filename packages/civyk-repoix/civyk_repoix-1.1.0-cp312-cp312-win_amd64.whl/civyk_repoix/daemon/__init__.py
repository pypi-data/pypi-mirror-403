"""Daemon process management for multi-IDE/multi-repo support.

This package implements the daemon architecture that enables sharing a single
index across multiple IDE instances and sessions.

Architecture:
    ┌─────────┐     stdio      ┌──────────┐    socket    ┌───────────┐
    │   IDE   │◄──────────────►│   Shim   │◄─────────────►│  Daemon   │
    │(MCP CLT)│                │(bridge)  │              │ (manager) │
    └─────────┘                └──────────┘              └─────┬─────┘
                                                               │
                                           ┌───────────────────┼───────────────────┐
                                           │                   │                   │
                                     ┌─────▼─────┐       ┌─────▼─────┐       ┌─────▼─────┐
                                     │  Worker   │       │  Worker   │       │  Worker   │
                                     │  (repo1)  │       │  (repo2)  │       │  (repo3)  │
                                     └───────────┘       └───────────┘       └───────────┘

Components:
    DaemonManager: Central coordinator managing worker pool and connections
    RepoWorker: Per-repository worker handling indexing and MCP tool calls
    run_shim: stdio-to-socket bridge for MCP compatibility

Features:
    - Multi-repository support with isolated workers
    - Automatic daemon startup on first IDE connection
    - Graceful shutdown with goodbye protocol
    - Keepalive ping/pong for connection health
    - Automatic reconnection with exponential backoff
    - Worker health monitoring and restart
"""

from civyk_repoix.daemon.manager import DaemonManager
from civyk_repoix.daemon.shim import run_shim
from civyk_repoix.daemon.worker import RepoWorker

__all__ = [
    "DaemonManager",
    "RepoWorker",
    "run_shim",
]
