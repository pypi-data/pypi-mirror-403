"""Transport layer for daemon communication.

This package provides the communication infrastructure for the daemon architecture,
enabling reliable message passing between the MCP shim, daemon manager, and repository
workers using a framed JSON-RPC protocol over Unix domain sockets or TCP.

Components:
    - FramedProtocol: Bidirectional JSON-RPC protocol handler with request tracking
    - SocketTransport: Cross-platform socket server/client abstraction
    - read_message/write_message: Low-level framed message I/O
    - Keepalive protocol: Ping/pong mechanism for connection health monitoring

Protocol:
    Uses length-prefix framing (4-byte big-endian header + JSON body).
    Maximum message size: 16MB. Supports timeouts for all I/O operations.

Platform Support:
    - Unix/macOS: Unix domain sockets with 0600 permissions
    - Windows: TCP on localhost (127.0.0.1) with deterministic port allocation
"""

from civyk_repoix.transport.protocol import (
    LATENCY_WARNING_THRESHOLD_MS,
    PACKET_LOSS_WARNING_THRESHOLD,
    FramedProtocol,
    read_message,
    write_message,
)
from civyk_repoix.transport.socket import (
    SocketTransport,
    get_socket_path,
    is_socket_available,
)

__all__ = [
    "FramedProtocol",
    "LATENCY_WARNING_THRESHOLD_MS",
    "PACKET_LOSS_WARNING_THRESHOLD",
    "SocketTransport",
    "get_socket_path",
    "is_socket_available",
    "read_message",
    "write_message",
]
