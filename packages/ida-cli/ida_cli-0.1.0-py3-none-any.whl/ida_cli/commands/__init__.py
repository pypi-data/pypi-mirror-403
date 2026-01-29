"""Command handlers for ida-cli daemon."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ida_cli.daemon import DaemonServer

# Import all command modules
from ida_cli.commands import analysis, functions, meta, mutate, search, xrefs


def register_all_handlers(server: DaemonServer) -> None:
    """Register all command handlers with the daemon server."""
    # Functions
    server.register_handler("functions_list", functions.list_functions)
    server.register_handler("functions_info", functions.function_info)

    # Analysis
    server.register_handler("decompile", analysis.decompile)
    server.register_handler("disassemble", analysis.disassemble)

    # Xrefs
    server.register_handler("xrefs", xrefs.get_xrefs)
    server.register_handler("callgraph", xrefs.get_callgraph)

    # Search
    server.register_handler("strings", search.search_strings)
    server.register_handler("search", search.search)
    server.register_handler("bytes", search.read_bytes)

    # Mutate
    server.register_handler("rename", mutate.rename)
    server.register_handler("rename_local", mutate.rename_local)
    server.register_handler("comment", mutate.set_comment)
    server.register_handler("set_type", mutate.set_type)
    server.register_handler("create_struct", mutate.create_struct)

    # Meta
    server.register_handler("segments", meta.get_segments)
    server.register_handler("info", meta.get_info)
    server.register_handler("exec", meta.exec_script)
