"""Socket protocol for daemon communication."""

from __future__ import annotations

import hashlib
import json
import os
import socket
from pathlib import Path
from typing import Any

# Socket and file locations
SOCKET_DIR = Path("/tmp")
CACHE_DIR = Path.home() / ".cache" / "ida-cli"


def get_idb_hash(idb_path: Path) -> str:
    """Generate a short hash for an IDB path."""
    return hashlib.sha256(str(idb_path.resolve()).encode()).hexdigest()[:12]


def get_socket_path(idb_path: Path) -> Path:
    """Get the Unix socket path for an IDB."""
    return SOCKET_DIR / f"ida-cli-{get_idb_hash(idb_path)}.sock"


def get_pid_path(idb_path: Path) -> Path:
    """Get the PID file path for an IDB daemon."""
    return SOCKET_DIR / f"ida-cli-{get_idb_hash(idb_path)}.pid"


def get_log_path(idb_path: Path) -> Path:
    """Get the log file path for an IDB daemon."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"daemon-{get_idb_hash(idb_path)}.log"


class DaemonProtocol:
    """Protocol for communicating with the daemon."""

    HEADER_SIZE = 8  # 8 bytes for message length

    @staticmethod
    def encode_message(data: dict[str, Any]) -> bytes:
        """Encode a message with length header."""
        payload = json.dumps(data).encode("utf-8")
        header = len(payload).to_bytes(DaemonProtocol.HEADER_SIZE, byteorder="big")
        return header + payload

    @staticmethod
    def decode_header(header: bytes) -> int:
        """Decode the length from a header."""
        return int.from_bytes(header, byteorder="big")

    @staticmethod
    def send_message(sock: socket.socket, data: dict[str, Any]) -> None:
        """Send a message over a socket."""
        sock.sendall(DaemonProtocol.encode_message(data))

    @staticmethod
    def recv_message(sock: socket.socket) -> dict[str, Any]:
        """Receive a message from a socket."""
        header = sock.recv(DaemonProtocol.HEADER_SIZE)
        if len(header) < DaemonProtocol.HEADER_SIZE:
            raise ConnectionError("Connection closed unexpectedly")

        length = DaemonProtocol.decode_header(header)
        chunks: list[bytes] = []
        received = 0

        while received < length:
            chunk = sock.recv(min(length - received, 8192))
            if not chunk:
                raise ConnectionError("Connection closed unexpectedly")
            chunks.append(chunk)
            received += len(chunk)

        payload = b"".join(chunks)
        return json.loads(payload.decode("utf-8"))  # type: ignore[no-any-return]


def is_daemon_running(idb_path: Path) -> bool:
    """Check if a daemon is running for the given IDB."""
    pid_path = get_pid_path(idb_path)
    if not pid_path.exists():
        return False

    try:
        pid = int(pid_path.read_text().strip())
        # Check if process exists
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, PermissionError):
        # Clean up stale PID file
        pid_path.unlink(missing_ok=True)
        return False
