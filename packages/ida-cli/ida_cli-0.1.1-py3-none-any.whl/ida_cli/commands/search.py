"""Search and bytes commands."""

from __future__ import annotations

import base64
import re
from typing import TYPE_CHECKING, Any, Literal

from ida_cli.helpers import parse_address

if TYPE_CHECKING:
    from ida_domain import Database


def search_strings(
    db: Database,
    pattern: str | None = None,
    min_length: int = 4,
    offset: int = 0,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Search for strings in the binary.

    Args:
        db: The ida-domain database handle
        pattern: Optional regex pattern to filter strings
        min_length: Minimum string length
        offset: Number of results to skip
        limit: Maximum results to return

    Returns:
        List of string information
    """
    results: list[dict[str, Any]] = []
    regex = re.compile(pattern) if pattern else None

    for s in db.strings.get_all():
        # Filter by minimum length
        if s.length < min_length:
            continue

        # Decode string contents
        try:
            value = s.contents.decode("utf-8", errors="replace")
        except (AttributeError, UnicodeDecodeError):
            value = str(s.contents)

        # Apply regex filter if provided
        if regex and not regex.search(value):
            continue

        results.append({
            "address": hex(s.address),
            "value": value,
            "length": s.length,
            "encoding": s.encoding if hasattr(s, "encoding") else "unknown",
        })

    return results[offset : offset + limit]


def search(
    db: Database,
    query: str,
    search_type: Literal["bytes", "immediate", "text", "auto"] = "auto",
    start_address: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Search for bytes, immediates, or text patterns.

    Args:
        db: The ida-domain database handle
        query: Search query
        search_type: Type of search ("bytes", "immediate", "text", "auto")
        start_address: Address to start searching from
        limit: Maximum results to return

    Returns:
        List of search results with addresses and context
    """
    results: list[dict[str, Any]] = []

    # Parse start address if provided
    start_ea = parse_address(start_address) if start_address else None

    # Auto-detect search type if needed
    if search_type == "auto":
        search_type = _detect_search_type(query)

    if search_type == "bytes":
        # Convert hex string to bytes
        query_clean = query.replace(" ", "").replace("0x", "")
        try:
            pattern_bytes = bytes.fromhex(query_clean)
        except ValueError as e:
            raise ValueError(f"Invalid hex pattern: {query}") from e

        # Find all occurrences
        addresses = db.bytes.find_binary_sequence(pattern_bytes, start_ea=start_ea)

        for addr in addresses[:limit]:
            # Get context around the match
            context_bytes = db.bytes.get_bytes_at(addr, len(pattern_bytes) + 16)
            disasm = db.bytes.get_disassembly_at(addr)

            results.append({
                "address": hex(addr),
                "type": "bytes",
                "match": pattern_bytes.hex(),
                "context_hex": context_bytes.hex() if context_bytes else "",
                "disassembly": disasm,
            })

    elif search_type == "immediate":
        # Parse immediate value
        try:
            if query.startswith("0x") or query.startswith("0X"):
                value = int(query, 16)
            else:
                value = int(query)
        except ValueError as e:
            raise ValueError(f"Invalid immediate value: {query}") from e

        # Search for immediate value
        addr = db.bytes.find_immediate_between(value, start_ea=start_ea)
        while addr is not None and len(results) < limit:
            disasm = db.bytes.get_disassembly_at(addr)

            results.append({
                "address": hex(addr),
                "type": "immediate",
                "value": hex(value),
                "disassembly": disasm,
            })

            # Continue searching from next address
            addr = db.bytes.find_immediate_between(value, start_ea=addr + 1)

    elif search_type == "text":
        # Search for text string
        addr = db.bytes.find_text_between(query, start_ea=start_ea)
        while addr is not None and len(results) < limit:
            # Get context
            context_bytes = db.bytes.get_bytes_at(addr, len(query) + 16)

            results.append({
                "address": hex(addr),
                "type": "text",
                "match": query,
                "context_hex": context_bytes.hex() if context_bytes else "",
            })

            # Continue searching from next address
            addr = db.bytes.find_text_between(query, start_ea=addr + 1)

    return results


def _detect_search_type(query: str) -> Literal["bytes", "immediate", "text"]:
    """Auto-detect the search type based on the query format."""
    # Check if it looks like a hex byte pattern (e.g., "48 89 5C" or "0x48895C")
    query_clean = query.replace(" ", "").replace("0x", "").replace("0X", "")
    if all(c in "0123456789abcdefABCDEF" for c in query_clean) and len(query_clean) >= 4:
        return "bytes"

    # Check if it looks like an immediate value
    try:
        int(query, 0)  # Handles both decimal and hex with 0x prefix
        return "immediate"
    except ValueError:
        pass

    # Default to text search
    return "text"


def read_bytes(
    db: Database,
    address: str,
    size: int,
) -> dict[str, Any]:
    """
    Read raw bytes at an address.

    Args:
        db: The ida-domain database handle
        address: Start address (hex string)
        size: Number of bytes to read

    Returns:
        Bytes as hex string and base64
    """
    addr = parse_address(address)
    data = db.bytes.get_bytes_at(addr, size)

    if data is None:
        raise ValueError(f"Failed to read {size} bytes at {address}")

    return {
        "address": address,
        "size": size,
        "hex": data.hex(),
        "raw_base64": base64.b64encode(data).decode("ascii"),
    }
