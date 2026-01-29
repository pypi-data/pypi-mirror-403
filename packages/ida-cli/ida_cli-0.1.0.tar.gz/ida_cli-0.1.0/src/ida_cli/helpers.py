"""Shared utility functions for ida-cli commands."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ida_domain import Database
    from ida_domain.functions import FunctionFlags
    from idaapi import func_t


def parse_address(target: str) -> int:
    """
    Parse hex address string to int.

    Args:
        target: Address string (e.g., "0x401000" or "401000")

    Returns:
        Integer address

    Raises:
        ValueError: If the string cannot be parsed as an address
    """
    if target.startswith("0x") or target.startswith("0X"):
        return int(target, 16)
    try:
        return int(target, 16)
    except ValueError as e:
        raise ValueError(f"Invalid address: {target}") from e


def resolve_function(db: Database, target: str) -> func_t:
    """
    Resolve function by name or address.

    Args:
        db: The database instance
        target: Function name or address (hex string)

    Returns:
        The function object

    Raises:
        ValueError: If function not found
    """
    # Try as address first
    try:
        addr = parse_address(target)
        func = db.functions.get_at(addr)
        if func is not None:
            return func
    except ValueError:
        pass

    # Try as name
    func = db.functions.get_function_by_name(target)
    if func is not None:
        return func

    raise ValueError(f"Function not found: {target}")


def try_resolve_function(db: Database, target: str) -> func_t | None:
    """
    Try to resolve function by name or address.

    Args:
        db: The database instance
        target: Function name or address (hex string)

    Returns:
        The function object or None if not found
    """
    try:
        return resolve_function(db, target)
    except ValueError:
        return None


def format_flags(flags: FunctionFlags) -> list[str]:
    """
    Format function flags as a list of string names.

    Args:
        flags: Function flags from ida-domain

    Returns:
        List of flag names
    """
    from ida_domain.functions import FunctionFlags

    result = []
    # Check each flag
    if FunctionFlags.LIB in flags:
        result.append("library")
    if FunctionFlags.THUNK in flags:
        result.append("thunk")
    if FunctionFlags.NORET in flags:
        result.append("noreturn")
    if FunctionFlags.FAR in flags:
        result.append("far")
    if FunctionFlags.HIDDEN in flags:
        result.append("hidden")
    if FunctionFlags.FRAME in flags:
        result.append("frame")
    if FunctionFlags.TAIL in flags:
        result.append("tail")
    if FunctionFlags.LUMINA in flags:
        result.append("lumina")

    return result


def format_permissions(perm: int) -> str:
    """
    Format segment permissions as rwx string.

    Args:
        perm: Permission bits from segment

    Returns:
        Permission string like "rwx" or "r-x"
    """
    from ida_domain.segments import SegmentPermissions

    r = "r" if perm & SegmentPermissions.READ else "-"
    w = "w" if perm & SegmentPermissions.WRITE else "-"
    x = "x" if perm & SegmentPermissions.EXEC else "-"
    return f"{r}{w}{x}"


def format_xref_type(xref_type: int) -> str:
    """
    Format xref type as human-readable string.

    Args:
        xref_type: XrefType enum value

    Returns:
        Human-readable string
    """
    from ida_domain.xrefs import XrefType

    type_names = {
        XrefType.CALL_NEAR: "call",
        XrefType.CALL_FAR: "call_far",
        XrefType.JUMP_NEAR: "jump",
        XrefType.JUMP_FAR: "jump_far",
        XrefType.ORDINARY_FLOW: "flow",
        XrefType.READ: "read",
        XrefType.WRITE: "write",
        XrefType.OFFSET: "offset",
        XrefType.INFORMATIONAL: "info",
        XrefType.TEXT: "text",
        XrefType.SYMBOLIC: "symbolic",
    }
    return type_names.get(xref_type, "unknown")
