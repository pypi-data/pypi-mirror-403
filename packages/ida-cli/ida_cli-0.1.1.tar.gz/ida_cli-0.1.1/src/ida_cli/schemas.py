"""Pydantic models for JSON output schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ResponseMeta(BaseModel):
    """Metadata included in every response."""

    idb: str
    daemon_pid: int
    elapsed_ms: float


class SuccessResponse(BaseModel):
    """Standard successful response wrapper."""

    success: bool = True
    command: str
    data: Any
    meta: ResponseMeta


class ErrorResponse(BaseModel):
    """Error response wrapper."""

    success: bool = False
    error: str
    command: str


# Function schemas


class FunctionInfo(BaseModel):
    """Function information."""

    address: str
    name: str
    size: int
    flags: list[str]


class FunctionDetail(BaseModel):
    """Detailed function information."""

    address: str
    name: str
    size: int
    flags: list[str]
    start_ea: str
    end_ea: str


# Decompilation schemas


class DecompileLine(BaseModel):
    """Single line of pseudocode."""

    line_no: int
    text: str


class DecompileResult(BaseModel):
    """Decompilation result."""

    address: str
    name: str
    pseudocode: str
    lines: list[DecompileLine]


# Disassembly schemas


class Instruction(BaseModel):
    """Single disassembled instruction."""

    address: str
    mnemonic: str
    operands: str
    bytes: str


class DisassembleResult(BaseModel):
    """Disassembly result."""

    address: str
    name: str
    instructions: list[Instruction]


# Cross-reference schemas


class XrefInfo(BaseModel):
    """Cross-reference information."""

    from_addr: str
    to_addr: str
    type: str
    from_func: str | None
    to_func: str | None


# Callgraph schemas


class CallgraphNode(BaseModel):
    """Node in a callgraph."""

    address: str
    name: str


class CallgraphEdge(BaseModel):
    """Edge in a callgraph."""

    from_addr: str
    to_addr: str


class CallgraphResult(BaseModel):
    """Callgraph result."""

    root: str
    nodes: list[CallgraphNode]
    edges: list[CallgraphEdge]


# String schemas


class StringInfo(BaseModel):
    """String information."""

    address: str
    value: str
    length: int
    encoding: str


# Search schemas


class SearchResult(BaseModel):
    """Search result."""

    address: str
    context: str


# Bytes schemas


class BytesResult(BaseModel):
    """Raw bytes result."""

    address: str
    hex: str
    raw_base64: str


# Segment schemas


class SegmentInfo(BaseModel):
    """Memory segment information."""

    name: str
    start: str
    end: str
    permissions: str
    seg_class: str


# Database info schemas


class DatabaseInfo(BaseModel):
    """Database metadata."""

    filename: str
    arch: str
    bits: int
    entry_point: str
    base_address: str


# Mutation result schemas


class MutationResult(BaseModel):
    """Result of a mutation operation."""

    success: bool = True
    target: str
    applied: str
