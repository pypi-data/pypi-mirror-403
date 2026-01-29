"""Mutation commands: rename, comment, type, struct."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

from ida_cli.helpers import parse_address, try_resolve_function

if TYPE_CHECKING:
    from ida_domain import Database


def rename(
    db: Database,
    target: str,
    new_name: str,
) -> dict[str, Any]:
    """
    Rename a symbol (function, global, etc.).

    Args:
        db: The ida-domain database handle
        target: Current name or address
        new_name: New name to apply

    Returns:
        Mutation result
    """
    # Try to resolve as function first
    func = try_resolve_function(db, target)

    if func is not None:
        # Rename function
        success = db.functions.set_name(func, new_name)
        return {
            "success": success,
            "target": target,
            "address": hex(func.start_ea),
            "applied": new_name,
            "type": "function",
        }

    # Try as address - rename general symbol
    try:
        addr = parse_address(target)
        # Use names API if available, otherwise try generic approach
        success = db.names.set_name(addr, new_name)
        return {
            "success": success,
            "target": target,
            "address": hex(addr),
            "applied": new_name,
            "type": "symbol",
        }
    except ValueError as e:
        raise ValueError(f"Could not resolve target: {target}") from e


def set_comment(
    db: Database,
    address: str,
    comment: str,
    comment_type: Literal["line", "function", "repeatable"] = "line",
) -> dict[str, Any]:
    """
    Set a comment at an address.

    Args:
        db: The ida-domain database handle
        address: Target address
        comment: Comment text
        comment_type: Type of comment ("line", "function", "repeatable")

    Returns:
        Mutation result
    """
    from ida_domain.comments import CommentKind

    addr = parse_address(address)

    if comment_type == "function":
        # Set function comment
        func = db.functions.get_at(addr)
        if func is None:
            raise ValueError(f"No function at address: {address}")

        success = db.functions.set_comment(func, comment)
        return {
            "success": success,
            "target": address,
            "applied": comment,
            "type": "function",
        }

    elif comment_type == "repeatable":
        # Set repeatable comment
        success = db.comments.set_at(addr, comment, CommentKind.REPEATABLE)
        return {
            "success": success,
            "target": address,
            "applied": comment,
            "type": "repeatable",
        }

    else:  # line comment (default)
        # Set regular line comment
        success = db.comments.set_at(addr, comment, CommentKind.REGULAR)
        return {
            "success": success,
            "target": address,
            "applied": comment,
            "type": "line",
        }


def set_type(
    db: Database,
    target: str,
    type_str: str,
) -> dict[str, Any]:
    """
    Apply a C type declaration to a symbol.

    Args:
        db: The ida-domain database handle
        target: Symbol name or address
        type_str: C type declaration string

    Returns:
        Mutation result
    """
    # Resolve target address
    func = try_resolve_function(db, target)
    addr = func.start_ea if func is not None else parse_address(target)

    # Parse the type declaration
    # Use None for local library
    tinfo = db.types.parse_one_declaration(None, type_str, "")
    if tinfo is None:
        raise ValueError(f"Failed to parse type: {type_str}")

    # Apply to address
    success = db.types.apply_at(tinfo, addr)

    return {
        "success": success,
        "target": target,
        "address": hex(addr),
        "applied": type_str,
    }


def rename_local(
    db: Database,
    function: str,
    old_name: str,
    new_name: str,
) -> dict[str, Any]:
    """
    Rename a local variable in a function.

    Args:
        db: The ida-domain database handle
        function: Function name or address containing the local variable
        old_name: Current name of the local variable
        new_name: New name to apply

    Returns:
        Mutation result
    """
    import ida_hexrays

    from ida_cli.helpers import resolve_function

    func = resolve_function(db, function)
    func_ea = func.start_ea

    # Use ida_hexrays.rename_lvar to rename the local variable
    success = ida_hexrays.rename_lvar(func_ea, old_name, new_name)

    return {
        "success": success,
        "function": db.functions.get_name(func),
        "function_address": hex(func_ea),
        "old_name": old_name,
        "new_name": new_name,
    }


def create_struct(
    db: Database,
    name: str,
    definition: str,
) -> dict[str, Any]:
    """
    Create a new struct type from a C definition.

    Args:
        db: The ida-domain database handle
        name: Struct name
        definition: C struct definition

    Returns:
        Mutation result
    """
    # Parse the struct definition into the local type library
    # Use None for the local library
    errors = db.types.parse_declarations(None, definition)

    if errors > 0:
        raise ValueError(f"Failed to parse struct definition ({errors} errors): {definition}")

    # Verify the struct was created
    created_type = db.types.get_by_name(name)

    return {
        "success": created_type is not None,
        "target": name,
        "applied": definition,
        "type_exists": created_type is not None,
    }
