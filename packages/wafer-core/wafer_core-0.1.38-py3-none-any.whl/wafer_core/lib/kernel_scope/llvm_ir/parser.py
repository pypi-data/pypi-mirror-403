"""LLVM-IR Parser.

Parses LLVM Intermediate Representation files (.ll) to extract
function definitions, loop structure, and optimization metadata.

Design: Wafer-436 - AMD Kernel Scope (Phase 2)

Supports:
- Single-line and multi-line function definitions
- Various calling conventions (amdgpu_kernel, spir_kernel, etc.)
- GPU-specific intrinsics (llvm.amdgcn.*, llvm.nvvm.*)
"""

import re
from pathlib import Path
from typing import Optional

from wafer_core.lib.kernel_scope.llvm_ir.types import (
    LLVMIRParseResult,
    FunctionInfo,
    LoopInfo,
)


# LLVM-IR patterns
_TARGET_TRIPLE_PATTERN = re.compile(r'target\s+triple\s*=\s*"([^"]+)"')
_DATA_LAYOUT_PATTERN = re.compile(r'target\s+datalayout\s*=\s*"([^"]+)"')

# Pattern to detect start of function definition (captures everything up to the function name)
# This pattern intentionally does NOT capture parameters - we handle multi-line params separately
_FUNCTION_START_PATTERN = re.compile(
    r"define\s+"
    r"(?:(?:internal|external|private|linkonce|weak|common|appending|"
    r"extern_weak|linkonce_odr|weak_odr|dso_local|dso_preemptable)\s+)*"
    r"(?:(?:dllimport|dllexport)\s+)?"
    r"(?:(?:default|hidden|protected)\s+)?"
    # Calling conventions (amdgpu_kernel, spir_kernel, ptx_kernel, etc.)
    r"(?:(?:amdgpu_kernel|amdgpu_cs|amdgpu_vs|amdgpu_ps|amdgpu_gs|amdgpu_hs|"
    r"spir_kernel|spir_func|ptx_kernel|ptx_device|cuda_device|cuda_kernel|"
    r"ccc|fastcc|coldcc|webkit_jscc|anyregcc|preserve_mostcc|preserve_allcc|"
    r"swiftcc|swifttailcc|cfguard_checkcc)\s+)?"
    r"(?:(?:zeroext|signext|inreg)\s+)?"
    r"(\S+)\s+"  # Return type (group 1)
    r"@([^\s(]+)"  # Function name (group 2)
    r"\s*\("  # Opening paren for params
)

_BASIC_BLOCK_PATTERN = re.compile(r"^([a-zA-Z0-9_.]+):\s*(?:;.*)?$", re.MULTILINE)
_BRANCH_PATTERN = re.compile(r"\bbr\s+(?:i1|label)")
_LOOP_METADATA_PATTERN = re.compile(r"!llvm\.loop")


def parse_llvm_ir_file(file_path: str | Path) -> LLVMIRParseResult:
    """Parse an LLVM-IR file.

    Args:
        file_path: Path to the .ll file

    Returns:
        LLVMIRParseResult with parsed function and loop information
    """
    path = Path(file_path)

    if not path.exists():
        return LLVMIRParseResult(
            success=False,
            error=f"File not found: {file_path}",
            file_path=str(file_path),
        )

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return LLVMIRParseResult(
            success=False,
            error=f"Failed to read file: {e}",
            file_path=str(file_path),
        )

    result = parse_llvm_ir_text(text)

    return LLVMIRParseResult(
        success=result.success,
        error=result.error,
        functions=result.functions,
        loops=result.loops,
        target_triple=result.target_triple,
        data_layout=result.data_layout,
        raw_text=result.raw_text,
        file_path=str(file_path),
    )


def parse_llvm_ir_text(text: str) -> LLVMIRParseResult:
    """Parse LLVM-IR from text.

    Args:
        text: LLVM-IR source text

    Returns:
        LLVMIRParseResult with parsed information
    """
    if not text.strip():
        return LLVMIRParseResult(
            success=False,
            error="Empty input text",
            raw_text=text,
        )

    # Check if this looks like LLVM-IR
    if not _is_llvm_ir(text):
        return LLVMIRParseResult(
            success=False,
            error="File does not appear to be LLVM-IR",
            raw_text=text,
        )

    # Extract target information
    target_triple = _extract_target_triple(text)
    data_layout = _extract_data_layout(text)

    # Parse functions
    functions = _parse_functions(text)

    # Detect loops (simplified)
    loops = _detect_loops(text, functions)

    return LLVMIRParseResult(
        success=True,
        functions=tuple(functions),
        loops=tuple(loops),
        target_triple=target_triple,
        data_layout=data_layout,
        raw_text=text,
    )


def _is_llvm_ir(text: str) -> bool:
    """Check if text appears to be LLVM-IR."""
    # Look for characteristic LLVM-IR patterns
    has_target = "target triple" in text or "target datalayout" in text
    has_define = "define " in text
    has_llvm_types = re.search(r"\bi\d+\b", text) is not None  # i32, i64, etc.

    return has_target or has_define or has_llvm_types


def _extract_target_triple(text: str) -> Optional[str]:
    """Extract target triple from LLVM-IR."""
    match = _TARGET_TRIPLE_PATTERN.search(text)
    return match.group(1) if match else None


def _extract_data_layout(text: str) -> Optional[str]:
    """Extract data layout from LLVM-IR."""
    match = _DATA_LAYOUT_PATTERN.search(text)
    return match.group(1) if match else None


def _parse_functions(text: str) -> list[FunctionInfo]:
    """Parse all function definitions from LLVM-IR.
    
    Handles both single-line and multi-line function definitions:
    - Single line: define void @foo(i32 %x) {
    - Multi-line:
        define void @foo(
            ptr %A,
            ptr %B
        ) {
    """
    functions = []
    lines = text.splitlines()
    i = 0
    
    while i < len(lines):
        line = lines[i]
        match = _FUNCTION_START_PATTERN.search(line)
        
        if not match:
            i += 1
            continue
        
        func_start_line = i + 1  # 1-indexed
        return_type = match.group(1)
        func_name = match.group(2)
        
        # Now we need to find the closing ) for parameters
        # It might be on the same line or span multiple lines
        params_str, body_start_line = _extract_multiline_params(lines, i)
        
        # Count parameters
        param_count = _count_parameters(params_str)
        
        # Find function body (starting from where params end)
        func_body = _extract_function_body(text, body_start_line - 1)
        
        # Count basic blocks
        basic_blocks = _BASIC_BLOCK_PATTERN.findall(func_body)
        bb_count = len(basic_blocks) + 1  # +1 for entry block
        
        # Count instructions (simplified: count lines with instructions)
        instr_count = len([l for l in func_body.splitlines() if _is_instruction(l)])
        
        # Detect loops (has backward branch)
        has_loop = bool(_BRANCH_PATTERN.search(func_body) and len(basic_blocks) > 1)
        
        # Extract attributes from the full definition
        full_def = "\n".join(lines[i:body_start_line])
        attrs = _extract_function_attributes(full_def)
        
        functions.append(FunctionInfo(
            name=func_name,
            line_number=func_start_line,
            return_type=return_type,
            parameter_count=param_count,
            basic_block_count=bb_count,
            instruction_count=instr_count,
            has_loop=has_loop,
            attributes=tuple(attrs),
        ))
        
        # Move past this function
        i = body_start_line
    
    return functions


def _extract_multiline_params(lines: list[str], start_idx: int) -> tuple[str, int]:
    """Extract parameters that may span multiple lines.
    
    Args:
        lines: All lines of the file
        start_idx: Index of the line containing 'define'
        
    Returns:
        Tuple of (params_string, line_index_after_closing_paren)
    """
    # Find opening paren position
    full_text = ""
    paren_depth = 0
    started = False
    params_start = 0
    
    for idx in range(start_idx, min(start_idx + 50, len(lines))):  # Max 50 lines for safety
        line = lines[idx]
        
        for char_idx, char in enumerate(line):
            if char == '(':
                if not started:
                    started = True
                    params_start = len(full_text) + char_idx + 1
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
                if started and paren_depth == 0:
                    # Found closing paren
                    params_end = len(full_text) + char_idx
                    full_text += line
                    params_str = full_text[params_start:params_end]
                    return params_str.strip(), idx + 1  # Return 1-indexed line number
        
        full_text += line + "\n"
    
    # If we get here, something went wrong - return empty params
    return "", start_idx + 1


def _count_parameters(params_str: str) -> int:
    """Count parameters in a parameter string, handling complex types."""
    if not params_str.strip():
        return 0
    
    # Remove newlines and excess whitespace
    params_str = " ".join(params_str.split())
    
    # Handle complex types with nested brackets/parens
    param_count = 0
    bracket_depth = 0
    paren_depth = 0
    angle_depth = 0
    
    for char in params_str:
        if char in '[':
            bracket_depth += 1
        elif char in ']':
            bracket_depth -= 1
        elif char == '(':
            paren_depth += 1
        elif char == ')':
            paren_depth -= 1
        elif char == '<':
            angle_depth += 1
        elif char == '>':
            angle_depth -= 1
        elif char == ',' and bracket_depth == 0 and paren_depth == 0 and angle_depth == 0:
            param_count += 1
    
    # If there's any content, there's at least one parameter
    if params_str.strip():
        param_count += 1
    
    return param_count


def _extract_function_body(text: str, start_line: int) -> str:
    """Extract function body from start line to closing brace."""
    lines = text.splitlines()
    if start_line >= len(lines):
        return ""

    brace_count = 0
    body_lines = []
    started = False

    for i in range(start_line, len(lines)):
        line = lines[i]
        if "{" in line:
            brace_count += line.count("{")
            started = True
        if "}" in line:
            brace_count -= line.count("}")

        if started:
            body_lines.append(line)

        if started and brace_count == 0:
            break

    return "\n".join(body_lines)


def _is_instruction(line: str) -> bool:
    """Check if line contains an LLVM instruction."""
    line = line.strip()
    if not line or line.startswith(";"):
        return False

    # Instructions typically have = or are terminators
    instruction_keywords = [
        "ret ", "br ", "switch ", "invoke ", "resume ",
        "unreachable", "call ", "store ", "fence ", "alloca ",
    ]

    if "=" in line:
        return True

    return any(kw in line for kw in instruction_keywords)


def _extract_function_attributes(line: str) -> list[str]:
    """Extract function attributes from define line."""
    attrs = []
    common_attrs = [
        "nounwind", "readnone", "readonly", "writeonly",
        "argmemonly", "speculatable", "willreturn",
        "norecurse", "nosync", "nofree",
    ]

    for attr in common_attrs:
        if attr in line:
            attrs.append(attr)

    return attrs


def _detect_loops(text: str, functions: list[FunctionInfo]) -> list[LoopInfo]:
    """Detect loops in LLVM-IR (simplified detection)."""
    loops = []

    # Look for loop metadata
    for func in functions:
        if not func.has_loop:
            continue

        # Simple loop detection based on basic block patterns
        # In practice, would need more sophisticated analysis
        loops.append(LoopInfo(
            function_name=func.name,
            header_label="entry",  # Placeholder
        ))

    return loops
