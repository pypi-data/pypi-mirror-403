"""Daemon management for persistent IDB sessions."""

from __future__ import annotations

import os
import signal
import socket
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ida_cli.protocol import (
    CACHE_DIR,
    DaemonProtocol,
    get_log_path,
    get_pid_path,
    get_socket_path,
    is_daemon_running,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from ida_domain import Database

# Default idle timeout in seconds (15 minutes)
DEFAULT_TIMEOUT = 900


class DaemonClient:
    """Client for communicating with the daemon."""

    def __init__(self, idb_path: Path) -> None:
        self.idb_path = idb_path
        self.socket_path = get_socket_path(idb_path)

    def send_command(self, command: str, args: dict[str, Any]) -> dict[str, Any]:
        """Send a command to the daemon and return the response."""
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(str(self.socket_path))
            DaemonProtocol.send_message(sock, {"command": command, "args": args})
            return DaemonProtocol.recv_message(sock)

    def is_running(self) -> bool:
        """Check if the daemon is running."""
        return is_daemon_running(self.idb_path)


class DaemonServer:
    """Server that holds an IDB open and handles commands."""

    def __init__(
        self,
        idb_path: Path,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self.idb_path = idb_path
        self.timeout = timeout
        self.socket_path = get_socket_path(idb_path)
        self.pid_path = get_pid_path(idb_path)
        self.log_path = get_log_path(idb_path)
        self.last_activity = time.time()
        self.running = False
        self.handlers: dict[str, Callable[..., Any]] = {}

        # Will be set after idalib initialization
        self.db: Database | None = None

    def register_handler(
        self, command: str, handler: Callable[..., Any]
    ) -> None:
        """Register a command handler."""
        self.handlers[command] = handler

    def log(self, message: str) -> None:
        """Write a log message."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

    def handle_client(self, conn: socket.socket) -> None:
        """Handle a single client connection."""
        try:
            request = DaemonProtocol.recv_message(conn)
            command = request.get("command", "")
            args = request.get("args", {})

            self.last_activity = time.time()
            start_time = time.time()

            if command == "shutdown":
                self.running = False
                response = {"success": True, "message": "Shutting down"}
            elif command in self.handlers:
                try:
                    result = self.handlers[command](self.db, **args)
                    elapsed_ms = (time.time() - start_time) * 1000
                    response = {
                        "success": True,
                        "command": command,
                        "data": result,
                        "meta": {
                            "idb": str(self.idb_path),
                            "daemon_pid": os.getpid(),
                            "elapsed_ms": round(elapsed_ms, 2),
                        },
                    }
                except Exception as e:
                    response = {
                        "success": False,
                        "error": str(e),
                        "command": command,
                    }
            else:
                response = {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "command": command,
                }

            DaemonProtocol.send_message(conn, response)
        except Exception as e:
            self.log(f"Error handling client: {e}")
        finally:
            conn.close()

    def check_timeout(self) -> bool:
        """Check if the daemon should shut down due to inactivity."""
        return time.time() - self.last_activity > self.timeout

    def cleanup(self) -> None:
        """Clean up socket and PID files."""
        self.socket_path.unlink(missing_ok=True)
        self.pid_path.unlink(missing_ok=True)

    def run(self) -> None:
        """Run the daemon server."""
        # Clean up any stale socket
        self.socket_path.unlink(missing_ok=True)

        # Write PID file
        self.pid_path.write_text(str(os.getpid()))

        # Set up signal handlers
        def handle_signal(signum: int, frame: Any) -> None:
            self.running = False

        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

        self.log(f"Starting daemon for {self.idb_path}")
        self.log(f"Socket: {self.socket_path}")
        self.log(f"Timeout: {self.timeout}s")

        # Create and bind socket
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(str(self.socket_path))
        server.listen(5)
        server.settimeout(1.0)  # Check timeout every second

        self.running = True
        try:
            while self.running:
                try:
                    conn, _ = server.accept()
                    self.handle_client(conn)
                except TimeoutError:
                    if self.check_timeout():
                        self.log("Idle timeout reached, shutting down")
                        break
        finally:
            server.close()
            self.cleanup()
            self.log("Daemon stopped")


def spawn_daemon(
    idb_path: Path,
    input_file: Path | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> None:
    """
    Spawn a daemon process for the given IDB.

    If input_file is provided and no IDB exists, performs initial analysis.
    """
    if is_daemon_running(idb_path):
        return

    # Fork to create daemon
    pid = os.fork()
    if pid > 0:
        # Parent: wait briefly for daemon to start
        time.sleep(0.5)
        return

    # Child: become daemon
    os.setsid()

    # Fork again to prevent zombie
    pid = os.fork()
    if pid > 0:
        os._exit(0)

    # Redirect stdio
    sys.stdin.close()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize server
    server = DaemonServer(idb_path, timeout)

    # Initialize ida-domain and open database
    try:
        # idapro must be imported before ida_domain
        import idapro  # noqa: F401

        from ida_domain import Database
        from ida_domain.database import IdaCommandOptions

        # Determine which file to open
        idb_exists = idb_path.exists()
        if idb_exists:
            # Opening existing IDB
            file_to_open = str(idb_path)
            server.log(f"Opening existing database: {idb_path}")
        elif input_file is not None:
            # Creating new database from input file
            file_to_open = str(input_file)
            server.log(f"Creating new database from {input_file}")
        else:
            raise RuntimeError(
                f"IDB file does not exist and no input file provided: {idb_path}"
            )

        ida_options = IdaCommandOptions(auto_analysis=True)
        server.db = Database.open(file_to_open, ida_options, save_on_close=True)
        server.log(f"Database opened successfully: {server.db.path}")
    except ImportError as e:
        server.log(f"Failed to import ida_domain: {e}")
        server.log("Ensure IDA Pro 9.1+ with idalib is installed and ida_domain is available")
        os._exit(1)
    except Exception as e:
        server.log(f"Failed to open database: {e}")
        os._exit(1)

    # Register command handlers
    from ida_cli.commands import register_all_handlers

    register_all_handlers(server)

    server.run()

    # Close database on exit
    if server.db is not None:
        try:
            server.db.close()
        except Exception as e:
            server.log(f"Error closing database: {e}")

    os._exit(0)


def connect_or_spawn(
    idb_path: Path,
    input_file: Path | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> DaemonClient:
    """
    Connect to existing daemon or spawn a new one.

    Returns a client ready to send commands.
    """
    client = DaemonClient(idb_path)

    if not client.is_running():
        spawn_daemon(idb_path, input_file, timeout)
        # Wait for daemon to be ready
        for _ in range(50):  # 5 seconds max
            if client.is_running():
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("Failed to start daemon")

    return client


def shutdown_daemon(idb_path: Path) -> bool:
    """Shutdown the daemon for the given IDB."""
    client = DaemonClient(idb_path)
    if not client.is_running():
        return False

    try:
        client.send_command("shutdown", {})
        return True
    except Exception:
        return False


def shutdown_all_daemons() -> int:
    """Shutdown all running ida-cli daemons. Returns count of daemons stopped."""
    count = 0
    for pid_file in Path("/tmp").glob("ida-cli-*.pid"):
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            count += 1
        except (ValueError, ProcessLookupError, PermissionError):
            pass
        pid_file.unlink(missing_ok=True)

    # Clean up socket files
    for sock_file in Path("/tmp").glob("ida-cli-*.sock"):
        sock_file.unlink(missing_ok=True)

    return count
