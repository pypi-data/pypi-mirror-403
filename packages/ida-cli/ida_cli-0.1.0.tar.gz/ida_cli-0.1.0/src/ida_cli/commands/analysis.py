"""Decompilation and disassembly commands."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ida_cli.helpers import resolve_function

if TYPE_CHECKING:
    from ida_domain import Database


def decompile(
    db: Database,
    target: str,
    start_line: int | None = None,
    end_line: int | None = None,
    max_lines: int | None = None,
) -> dict[str, Any]:
    """
    Decompile a function to pseudocode.

    Args:
        db: The ida-domain database handle
        target: Function name or address (hex string)
        start_line: Starting line number (optional, 1-indexed)
        end_line: Ending line number (optional, 1-indexed)
        max_lines: Maximum lines to return (optional)

    Returns:
        Decompilation result with pseudocode
    """
    func = resolve_function(db, target)
    name = db.functions.get_name(func)

    # Get pseudocode lines
    lines = db.functions.get_pseudocode(func)

    # Apply line range filters
    if start_line is not None:
        lines = lines[start_line - 1 :]  # Convert to 0-indexed

    if end_line is not None:
        lines = lines[: end_line - (start_line - 1 if start_line else 0)]

    if max_lines is not None:
        lines = lines[:max_lines]

    # Build lines with line numbers
    line_offset = start_line - 1 if start_line else 0
    numbered_lines = [
        {"line_no": i + 1 + line_offset, "text": line}
        for i, line in enumerate(lines)
    ]

    return {
        "address": hex(func.start_ea),
        "name": name,
        "pseudocode": "\n".join(lines),
        "lines": numbered_lines,
        "total_lines": len(db.functions.get_pseudocode(func)),
    }


def disassemble(
    db: Database,
    target: str,
    max_instructions: int = 100,
) -> dict[str, Any]:
    """
    Disassemble a function or address range.

    Args:
        db: The ida-domain database handle
        target: Function name, address, or range (start-end)
        max_instructions: Maximum instructions to return

    Returns:
        Disassembly result with instruction list
    """
    import idc

    func = resolve_function(db, target)
    name = db.functions.get_name(func)

    instructions: list[dict[str, Any]] = []

    # Get instructions for the function
    for insn in db.functions.get_instructions(func):
        if len(instructions) >= max_instructions:
            break

        # Get bytes for this instruction
        insn_bytes = db.bytes.get_bytes_at(insn.ea, insn.size)

        # Get operands text
        operands = []
        for i in range(8):  # Max 8 operands
            op_str = idc.print_operand(insn.ea, i)
            if op_str:
                operands.append(op_str)
            else:
                break

        instructions.append({
            "address": hex(insn.ea),
            "mnemonic": insn.get_canon_mnem(),
            "operands": operands,
            "op_str": ", ".join(operands),
            "bytes": insn_bytes.hex() if insn_bytes else "",
            "size": insn.size,
        })

    # Also get the full disassembly lines for context
    disasm_lines = db.functions.get_disassembly(func)

    return {
        "address": hex(func.start_ea),
        "name": name,
        "instructions": instructions,
        "instruction_count": len(instructions),
        "disassembly": disasm_lines[:max_instructions] if disasm_lines else [],
    }
