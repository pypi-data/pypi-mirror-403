"""Function-related commands."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ida_cli.helpers import format_flags, resolve_function

if TYPE_CHECKING:
    from ida_domain import Database


def list_functions(
    db: Database,
    filter_pattern: str | None = None,
    offset: int = 0,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    List all functions in the database.

    Args:
        db: The ida-domain database handle
        filter_pattern: Optional regex to filter function names
        offset: Number of functions to skip
        limit: Maximum number of functions to return

    Returns:
        List of function information dictionaries
    """
    results: list[dict[str, Any]] = []
    pattern = re.compile(filter_pattern) if filter_pattern else None

    for func in db.functions.get_all():
        name = db.functions.get_name(func)

        # Apply filter if provided
        if pattern and not pattern.search(name):
            continue

        flags = db.functions.get_flags(func)

        results.append({
            "address": hex(func.start_ea),
            "name": name,
            "size": func.end_ea - func.start_ea,
            "flags": format_flags(flags),
        })

    return results[offset : offset + limit]


def function_info(
    db: Database,
    target: str,
) -> dict[str, Any]:
    """
    Get detailed information about a specific function.

    Args:
        db: The ida-domain database handle
        target: Function name or address (hex string)

    Returns:
        Detailed function information
    """
    func = resolve_function(db, target)

    name = db.functions.get_name(func)
    flags = db.functions.get_flags(func)
    func_type = db.functions.get_type(func)

    # Get callers and callees counts
    callers = list(db.functions.get_callers(func))
    callees = list(db.functions.get_callees(func))

    # Get local variables if available
    local_vars: list[dict[str, Any]] = []
    try:
        for var in db.functions.get_local_variables(func):
            local_vars.append({
                "name": var.name,
                "type": str(var.type) if var.type else None,
                "offset": var.offset,
            })
    except Exception:
        pass  # Local variable enumeration may fail

    return {
        "address": hex(func.start_ea),
        "name": name,
        "size": func.end_ea - func.start_ea,
        "flags": format_flags(flags),
        "start_ea": hex(func.start_ea),
        "end_ea": hex(func.end_ea),
        "type": str(func_type) if func_type else None,
        "callers_count": len(callers),
        "callees_count": len(callees),
        "local_vars": local_vars,
    }
