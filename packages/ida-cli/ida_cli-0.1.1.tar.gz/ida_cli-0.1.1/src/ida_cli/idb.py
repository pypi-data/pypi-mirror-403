"""IDB file detection and creation."""

from __future__ import annotations

from pathlib import Path


def find_existing_idb(input_file: Path) -> Path | None:
    """
    Find an existing IDB for the given input file.

    Search priority:
    1. {input_basename}.idb in same directory
    2. {input_basename}.i64 in same directory (64-bit)

    Returns None if no existing IDB found.
    """
    parent = input_file.parent
    stem = input_file.stem

    # Check for .idb (32-bit)
    idb_path = parent / f"{stem}.idb"
    if idb_path.exists():
        return idb_path

    # Check for .i64 (64-bit)
    i64_path = parent / f"{stem}.i64"
    if i64_path.exists():
        return i64_path

    return None


def get_idb_path(input_file: Path) -> Path:
    """
    Get the IDB path for an input file.

    Returns existing IDB if found, otherwise returns the path
    where a new IDB would be created.
    """
    existing = find_existing_idb(input_file)
    if existing:
        return existing

    # Default to .i64 for new databases (most binaries are 64-bit now)
    return input_file.parent / f"{input_file.stem}.i64"


def resolve_idb(
    input_file: Path | None = None,
    explicit_idb: Path | None = None,
) -> Path:
    """
    Resolve the IDB path from arguments.

    Priority:
    1. Explicit --idb path
    2. Auto-detect from input file

    Raises ValueError if neither is provided or IDB cannot be determined.
    """
    if explicit_idb:
        if not explicit_idb.exists():
            raise ValueError(f"IDB file not found: {explicit_idb}")
        return explicit_idb

    if input_file:
        if not input_file.exists():
            raise ValueError(f"Input file not found: {input_file}")
        return get_idb_path(input_file)

    raise ValueError("Either -i/--input or --idb must be provided")


def needs_analysis(input_file: Path) -> bool:
    """Check if the input file needs initial analysis (no IDB exists)."""
    return find_existing_idb(input_file) is None
