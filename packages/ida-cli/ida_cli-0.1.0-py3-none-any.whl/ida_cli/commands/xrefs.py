"""Cross-reference and callgraph commands."""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Any, Literal

from ida_cli.helpers import format_xref_type, parse_address, try_resolve_function

if TYPE_CHECKING:
    from ida_domain import Database


def get_xrefs(
    db: Database,
    target: str,
    direction: Literal["to", "from", "both"] = "both",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Get cross-references to/from an address.

    Args:
        db: The ida-domain database handle
        target: Target address or name
        direction: "to" (references to target), "from" (references from target), or "both"
        limit: Maximum number of xrefs to return

    Returns:
        List of cross-reference information
    """
    # Try to resolve as function first, then as address
    func = try_resolve_function(db, target)
    addr = func.start_ea if func is not None else parse_address(target)

    results: list[dict[str, Any]] = []

    if direction in ("to", "both"):
        for xref in db.xrefs.to_ea(addr):
            if len(results) >= limit:
                break

            # Try to get the function containing the source address
            src_func = db.functions.get_at(xref.from_ea)
            src_func_name = db.functions.get_name(src_func) if src_func else None

            results.append({
                "direction": "to",
                "from_address": hex(xref.from_ea),
                "to_address": hex(xref.to_ea),
                "type": format_xref_type(xref.type),
                "is_code": xref.is_code,
                "is_call": xref.is_call,
                "source_function": src_func_name,
            })

    if direction in ("from", "both"):
        for xref in db.xrefs.from_ea(addr):
            if len(results) >= limit:
                break

            # Try to get the function containing the target address
            dst_func = db.functions.get_at(xref.to_ea)
            dst_func_name = db.functions.get_name(dst_func) if dst_func else None

            results.append({
                "direction": "from",
                "from_address": hex(xref.from_ea),
                "to_address": hex(xref.to_ea),
                "type": format_xref_type(xref.type),
                "is_code": xref.is_code,
                "is_call": xref.is_call,
                "target_function": dst_func_name,
            })

    return results[:limit]


def get_callgraph(
    db: Database,
    target: str,
    max_depth: int = 3,
    direction: Literal["callers", "callees", "both"] = "both",
) -> dict[str, Any]:
    """
    Get the callgraph for a function.

    Args:
        db: The ida-domain database handle
        target: Function name or address
        max_depth: Maximum depth to traverse
        direction: "callers", "callees", or "both"

    Returns:
        Callgraph with nodes and edges
    """
    from ida_cli.helpers import resolve_function

    func = resolve_function(db, target)
    root_addr = func.start_ea
    root_name = db.functions.get_name(func)

    # Use sets to track visited nodes and edges
    nodes: dict[int, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    def add_node(addr: int) -> dict[str, Any]:
        if addr not in nodes:
            f = db.functions.get_at(addr)
            name = db.functions.get_name(f) if f else f"sub_{addr:x}"
            nodes[addr] = {
                "address": hex(addr),
                "name": name,
            }
        return nodes[addr]

    # Add root node
    add_node(root_addr)

    # BFS traversal for callers
    if direction in ("callers", "both"):
        visited_callers: set[int] = {root_addr}
        queue: deque[tuple[int, int]] = deque([(root_addr, 0)])

        while queue:
            current_addr, depth = queue.popleft()

            if depth >= max_depth:
                continue

            current_func = db.functions.get_at(current_addr)
            if current_func is None:
                continue

            for caller in db.functions.get_callers(current_func):
                caller_addr = caller.ea if hasattr(caller, 'ea') else caller
                if caller_addr in visited_callers:
                    continue

                visited_callers.add(caller_addr)
                add_node(caller_addr)

                edges.append({
                    "from": hex(caller_addr),
                    "to": hex(current_addr),
                    "type": "call",
                    "direction": "caller",
                })

                queue.append((caller_addr, depth + 1))

    # BFS traversal for callees
    if direction in ("callees", "both"):
        visited_callees: set[int] = {root_addr}
        queue = deque([(root_addr, 0)])

        while queue:
            current_addr, depth = queue.popleft()

            if depth >= max_depth:
                continue

            current_func = db.functions.get_at(current_addr)
            if current_func is None:
                continue

            for callee in db.functions.get_callees(current_func):
                callee_addr = callee.ea if hasattr(callee, 'ea') else callee
                if callee_addr in visited_callees:
                    continue

                visited_callees.add(callee_addr)
                add_node(callee_addr)

                edges.append({
                    "from": hex(current_addr),
                    "to": hex(callee_addr),
                    "type": "call",
                    "direction": "callee",
                })

                queue.append((callee_addr, depth + 1))

    return {
        "root": {
            "address": hex(root_addr),
            "name": root_name,
        },
        "nodes": list(nodes.values()),
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }
