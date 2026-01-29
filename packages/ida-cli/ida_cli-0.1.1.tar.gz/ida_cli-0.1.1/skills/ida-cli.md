---
name: ida-cli
description: Use for reverse engineering binaries with IDA Pro - decompilation, disassembly, xrefs, strings, and analysis
---

# IDA CLI - Reverse Engineering with IDA Pro

Use `uvx ida-cli` for binary analysis tasks: decompiling functions, examining disassembly, finding cross-references, searching strings, and modifying the database.

## Prerequisites

- IDA Pro 9.1+ with idalib support installed
- ida-cli auto-detects IDA in `/opt/ida-pro-*`, `/Applications/IDA*.app`, or set `IDADIR`

## Quick Reference

```bash
# Get binary metadata
uvx ida-cli -i <binary> info

# List functions (with optional regex filter)
uvx ida-cli -i <binary> functions list
uvx ida-cli -i <binary> functions list --filter "main|init"

# Decompile a function (by name or address)
uvx ida-cli -i <binary> decompile main
uvx ida-cli -i <binary> decompile 0x401000

# Disassemble
uvx ida-cli -i <binary> disassemble main --max-instructions 50

# Cross-references
uvx ida-cli -i <binary> xrefs main --direction both
uvx ida-cli -i <binary> callgraph main --depth 3

# Search strings
uvx ida-cli -i <binary> strings --pattern "password|secret"
uvx ida-cli -i <binary> search "48 89 e5" --type bytes

# Read raw bytes
uvx ida-cli -i <binary> bytes 0x401000 64

# Rename symbols
uvx ida-cli -i <binary> rename sub_401000 my_function
uvx ida-cli -i <binary> rename-local main var_8 buffer_size

# Add comments
uvx ida-cli -i <binary> comment 0x401000 "This is the entry point"

# Apply types
uvx ida-cli -i <binary> set-type my_function "int __fastcall my_function(char *buf, int len)"

# List segments
uvx ida-cli -i <binary> segments
```

## Workflow for Analysis

1. **Start with info** to understand the binary:
   ```bash
   uvx ida-cli -i target.exe info
   ```

2. **List functions** to find interesting targets:
   ```bash
   uvx ida-cli -i target.exe functions list --filter "crypt|auth|password"
   ```

3. **Decompile** functions of interest:
   ```bash
   uvx ida-cli -i target.exe decompile suspicious_function
   ```

4. **Trace references** to understand data flow:
   ```bash
   uvx ida-cli -i target.exe xrefs password_buffer --direction to
   uvx ida-cli -i target.exe callgraph check_password --direction callers
   ```

5. **Search for patterns**:
   ```bash
   uvx ida-cli -i target.exe strings --pattern "API|key|token"
   uvx ida-cli -i target.exe search "ff 15" --type bytes  # indirect calls
   ```

6. **Annotate findings** as you go:
   ```bash
   uvx ida-cli -i target.exe rename sub_401234 decrypt_config
   uvx ida-cli -i target.exe comment 0x401234 "XOR decryption routine"
   ```

## Output Format

All commands return JSON with this structure:
```json
{
  "success": true,
  "command": "decompile",
  "data": { ... },
  "meta": {
    "idb": "/path/to/binary.i64",
    "daemon_pid": 12345,
    "elapsed_ms": 42.5
  }
}
```

## Daemon Lifecycle

ida-cli uses a background daemon for performance. The daemon:
- Starts automatically on first command
- Stays alive for 15 minutes (configurable via `--timeout`)
- Can be stopped with `--shutdown` or `--shutdown-all`
