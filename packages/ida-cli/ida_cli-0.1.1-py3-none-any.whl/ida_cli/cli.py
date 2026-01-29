"""Main CLI entry point using Click."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from ida_cli.daemon import (
    DEFAULT_TIMEOUT,
    connect_or_spawn,
    shutdown_all_daemons,
    shutdown_daemon,
)
from ida_cli.env_setup import setup_or_exit
from ida_cli.idb import resolve_idb


def output_json(data: dict[str, Any]) -> None:
    """Output JSON to stdout."""
    click.echo(json.dumps(data, indent=2))


def output_error(error: str, command: str) -> None:
    """Output an error response."""
    output_json({"success": False, "error": error, "command": command})
    sys.exit(1)


class IdaCliContext:
    """Context object passed to all commands."""

    def __init__(
        self,
        input_file: Path | None,
        idb_path: Path | None,
        timeout: int,
    ) -> None:
        self.input_file = input_file
        self.explicit_idb = idb_path
        self.timeout = timeout
        self._client: Any = None
        self._resolved_idb: Path | None = None

    @property
    def idb(self) -> Path:
        """Resolve and cache the IDB path."""
        if self._resolved_idb is None:
            self._resolved_idb = resolve_idb(self.input_file, self.explicit_idb)
        return self._resolved_idb

    @property
    def client(self) -> Any:
        """Get or create daemon client."""
        if self._client is None:
            self._client = connect_or_spawn(
                self.idb,
                self.input_file,
                self.timeout,
            )
        return self._client

    def send(self, command: str, **args: Any) -> dict[str, Any]:
        """Send a command to the daemon."""
        result: dict[str, Any] = self.client.send_command(command, args)
        return result


pass_context = click.make_pass_decorator(IdaCliContext)


@click.group()
@click.option(
    "-i",
    "--input",
    "input_file",
    type=click.Path(exists=True, path_type=Path),
    help="Input binary file (auto-detects/creates IDB)",
)
@click.option(
    "--idb",
    type=click.Path(exists=True, path_type=Path),
    help="Explicit IDB path (overrides auto-detection)",
)
@click.option(
    "--timeout",
    type=int,
    default=DEFAULT_TIMEOUT,
    help=f"Daemon idle timeout in seconds (default: {DEFAULT_TIMEOUT})",
)
@click.option(
    "--shutdown",
    is_flag=True,
    help="Shutdown daemon for current target",
)
@click.option(
    "--shutdown-all",
    is_flag=True,
    help="Shutdown all running daemons",
)
@click.pass_context
def main(
    ctx: click.Context,
    input_file: Path | None,
    idb: Path | None,
    timeout: int,
    shutdown: bool,
    shutdown_all: bool,
) -> None:
    """ida-cli: CLI tool for reverse engineering with IDA's idalib.

    Examples:

    \b
        ida-cli -i binary.exe info
        ida-cli -i binary.exe functions list
        ida-cli -i binary.exe decompile main
        ida-cli -i binary.exe strings --pattern "password"
    """
    # Ensure IDA environment is properly configured before any command
    setup_or_exit()

    if shutdown_all:
        count = shutdown_all_daemons()
        output_json({"success": True, "message": f"Stopped {count} daemon(s)"})
        sys.exit(0)

    if shutdown:
        if not input_file and not idb:
            output_error("--shutdown requires -i or --idb", "shutdown")
        try:
            idb_path = resolve_idb(input_file, idb)
            if shutdown_daemon(idb_path):
                output_json({"success": True, "message": "Daemon stopped"})
            else:
                output_json({"success": True, "message": "No daemon running"})
        except ValueError as e:
            output_error(str(e), "shutdown")
        sys.exit(0)

    ctx.obj = IdaCliContext(input_file, idb, timeout)


# =============================================================================
# Functions commands
# =============================================================================


@main.group()
def functions() -> None:
    """Function operations."""
    pass


@functions.command("list")
@click.option("--filter", "filter_pattern", help="Regex to filter function names")
@click.option("--offset", type=int, default=0, help="Skip first N results")
@click.option("--limit", type=int, default=100, help="Maximum results to return")
@pass_context
def functions_list(
    ctx: IdaCliContext,
    filter_pattern: str | None,
    offset: int,
    limit: int,
) -> None:
    """List all functions."""
    result = ctx.send(
        "functions_list",
        filter_pattern=filter_pattern,
        offset=offset,
        limit=limit,
    )
    output_json(result)


@functions.command("info")
@click.argument("target")
@pass_context
def functions_info(ctx: IdaCliContext, target: str) -> None:
    """Get detailed function information."""
    result = ctx.send("functions_info", target=target)
    output_json(result)


# =============================================================================
# Analysis commands
# =============================================================================


@main.command()
@click.argument("target")
@click.option("--start-line", type=int, help="Starting line number")
@click.option("--end-line", type=int, help="Ending line number")
@click.option("--max-lines", type=int, help="Maximum lines to return")
@pass_context
def decompile(
    ctx: IdaCliContext,
    target: str,
    start_line: int | None,
    end_line: int | None,
    max_lines: int | None,
) -> None:
    """Decompile a function to pseudocode."""
    result = ctx.send(
        "decompile",
        target=target,
        start_line=start_line,
        end_line=end_line,
        max_lines=max_lines,
    )
    output_json(result)


@main.command()
@click.argument("target")
@click.option("--max-instructions", type=int, default=100, help="Maximum instructions")
@pass_context
def disassemble(ctx: IdaCliContext, target: str, max_instructions: int) -> None:
    """Disassemble a function or address range."""
    result = ctx.send("disassemble", target=target, max_instructions=max_instructions)
    output_json(result)


# =============================================================================
# Cross-reference commands
# =============================================================================


@main.command()
@click.argument("target")
@click.option(
    "--direction",
    type=click.Choice(["to", "from", "both"]),
    default="both",
    help="Direction of references",
)
@click.option("--limit", type=int, default=100, help="Maximum results")
@pass_context
def xrefs(ctx: IdaCliContext, target: str, direction: str, limit: int) -> None:
    """Get cross-references to/from an address."""
    result = ctx.send("xrefs", target=target, direction=direction, limit=limit)
    output_json(result)


@main.command()
@click.argument("target")
@click.option("--depth", type=int, default=3, help="Maximum traversal depth")
@click.option(
    "--direction",
    type=click.Choice(["callers", "callees", "both"]),
    default="both",
    help="Direction to traverse",
)
@pass_context
def callgraph(ctx: IdaCliContext, target: str, depth: int, direction: str) -> None:
    """Get the callgraph for a function."""
    result = ctx.send(
        "callgraph", target=target, max_depth=depth, direction=direction
    )
    output_json(result)


# =============================================================================
# Search commands
# =============================================================================


@main.command()
@click.option("--pattern", help="Regex pattern to filter strings")
@click.option("--min-length", type=int, default=4, help="Minimum string length")
@click.option("--offset", type=int, default=0, help="Skip first N results")
@click.option("--limit", type=int, default=100, help="Maximum results")
@pass_context
def strings(
    ctx: IdaCliContext,
    pattern: str | None,
    min_length: int,
    offset: int,
    limit: int,
) -> None:
    """Search for strings in the binary."""
    result = ctx.send(
        "strings",
        pattern=pattern,
        min_length=min_length,
        offset=offset,
        limit=limit,
    )
    output_json(result)


@main.command()
@click.argument("query")
@click.option(
    "--type",
    "search_type",
    type=click.Choice(["bytes", "immediate", "text", "auto"]),
    default="auto",
    help="Search type",
)
@click.option("--start", "start_address", help="Starting address")
@click.option("--limit", type=int, default=100, help="Maximum results")
@pass_context
def search(
    ctx: IdaCliContext,
    query: str,
    search_type: str,
    start_address: str | None,
    limit: int,
) -> None:
    """Search for bytes, immediates, or text patterns."""
    result = ctx.send(
        "search",
        query=query,
        search_type=search_type,
        start_address=start_address,
        limit=limit,
    )
    output_json(result)


@main.command()
@click.argument("address")
@click.argument("size", type=int)
@pass_context
def bytes(ctx: IdaCliContext, address: str, size: int) -> None:
    """Read raw bytes at an address."""
    result = ctx.send("bytes", address=address, size=size)
    output_json(result)


# =============================================================================
# Mutation commands
# =============================================================================


@main.command()
@click.argument("target")
@click.argument("new_name")
@pass_context
def rename(ctx: IdaCliContext, target: str, new_name: str) -> None:
    """Rename a symbol (function, global, etc.)."""
    result = ctx.send("rename", target=target, new_name=new_name)
    output_json(result)


@main.command("rename-local")
@click.argument("function")
@click.argument("old_name")
@click.argument("new_name")
@pass_context
def rename_local(
    ctx: IdaCliContext, function: str, old_name: str, new_name: str
) -> None:
    """Rename a local variable in a function."""
    result = ctx.send(
        "rename_local", function=function, old_name=old_name, new_name=new_name
    )
    output_json(result)


@main.command()
@click.argument("address")
@click.argument("text")
@click.option(
    "--type",
    "comment_type",
    type=click.Choice(["line", "function", "repeatable"]),
    default="line",
    help="Comment type",
)
@pass_context
def comment(ctx: IdaCliContext, address: str, text: str, comment_type: str) -> None:
    """Add a comment at an address."""
    result = ctx.send(
        "comment", address=address, comment=text, comment_type=comment_type
    )
    output_json(result)


@main.command("set-type")
@click.argument("target")
@click.argument("type_str")
@pass_context
def set_type(ctx: IdaCliContext, target: str, type_str: str) -> None:
    """Apply a C type declaration to a symbol."""
    result = ctx.send("set_type", target=target, type_str=type_str)
    output_json(result)


@main.command("create-struct")
@click.argument("name")
@click.argument("definition")
@pass_context
def create_struct(ctx: IdaCliContext, name: str, definition: str) -> None:
    """Create a new struct type from a C definition."""
    result = ctx.send("create_struct", name=name, definition=definition)
    output_json(result)


# =============================================================================
# Meta commands
# =============================================================================


@main.command()
@pass_context
def segments(ctx: IdaCliContext) -> None:
    """List all memory segments."""
    result = ctx.send("segments")
    output_json(result)


@main.command()
@pass_context
def info(ctx: IdaCliContext) -> None:
    """Get database metadata."""
    result = ctx.send("info")
    output_json(result)


@main.command("exec")
@click.argument("script")
@pass_context
def exec_cmd(ctx: IdaCliContext, script: str) -> None:
    """Execute arbitrary IDAPython script."""
    result = ctx.send("exec", script=script)
    output_json(result)


if __name__ == "__main__":
    main()
