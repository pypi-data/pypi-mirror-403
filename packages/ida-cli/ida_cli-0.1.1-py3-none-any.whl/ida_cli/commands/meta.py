"""Metadata and utility commands."""

from __future__ import annotations

import io
import traceback
from contextlib import redirect_stdout
from typing import TYPE_CHECKING, Any

from ida_cli.helpers import format_permissions

if TYPE_CHECKING:
    from ida_domain import Database


def get_segments(
    db: Database,
) -> list[dict[str, Any]]:
    """
    List all memory segments.

    Args:
        db: The ida-domain database handle

    Returns:
        List of segment information
    """
    results: list[dict[str, Any]] = []

    for seg in db.segments.get_all():
        seg_class = db.segments.get_class(seg)
        results.append({
            "name": db.segments.get_name(seg),
            "start": hex(seg.start_ea),
            "end": hex(seg.end_ea),
            "size": db.segments.get_size(seg),
            "permissions": format_permissions(seg.perm),
            "seg_class": seg_class or "",
            "bitness": db.segments.get_bitness(seg),
        })

    return results


def get_info(
    db: Database,
) -> dict[str, Any]:
    """
    Get database metadata.

    Args:
        db: The ida-domain database handle

    Returns:
        Database information
    """
    return {
        "filename": db.path or "",
        "arch": db.architecture or "",
        "bits": db.bitness or 0,
        "entry_point": hex(db.start_ip) if db.start_ip else "",
        "base_address": hex(db.base_address) if db.base_address else "",
    }


def exec_script(
    db: Database,
    script: str,
) -> dict[str, Any]:
    """
    Execute arbitrary IDAPython script.

    Args:
        db: The ida-domain database handle
        script: Python code to execute

    Returns:
        Script output or result
    """
    # Capture stdout
    stdout_capture = io.StringIO()

    # Create a namespace for the script with access to the database
    script_globals: dict[str, Any] = {
        "db": db,
        "__builtins__": __builtins__,
    }

    try:
        with redirect_stdout(stdout_capture):
            exec(script, script_globals)

        output = stdout_capture.getvalue()

        # Check if there's a 'result' variable in the namespace
        result = script_globals.get("result")

        return {
            "success": True,
            "output": output,
            "result": result,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "output": stdout_capture.getvalue(),
        }
