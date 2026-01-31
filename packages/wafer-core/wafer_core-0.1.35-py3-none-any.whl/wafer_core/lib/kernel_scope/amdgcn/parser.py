"""AMDGCN ISA Parser.

Parses AMDGCN assembly files (.s, .gcn, .asm) to extract kernel metadata
and instruction information.

Design: Wafer-436 - AMD Kernel Scope

Key directives parsed:
- .amdgcn_target: Target architecture
- .amdhsa_kernel: Kernel entry point
- .amdhsa_next_free_vgpr: VGPR allocation
- .amdhsa_next_free_sgpr: SGPR allocation
- .amdhsa_group_segment_fixed_size: LDS allocation
- .amdhsa_private_segment_fixed_size: Scratch allocation
"""

import re
from pathlib import Path
from typing import Optional

from wafer_core.lib.kernel_scope.amdgcn.types import (
    ISAParseResult,
    KernelMetadata,
    InstructionInfo,
    InstructionCategory,
)
from wafer_core.lib.kernel_scope.amdgcn.instruction_db import (
    classify_instruction,
    extract_mnemonic,
)


# Directive patterns
_TARGET_PATTERN = re.compile(r'\.amdgcn_target\s+"([^"]+)"')
_KERNEL_NAME_PATTERN = re.compile(r"\.amdhsa_kernel\s+(\S+)")
_VGPR_PATTERN = re.compile(r"\.amdhsa_next_free_vgpr\s+(\d+)")
_SGPR_PATTERN = re.compile(r"\.amdhsa_next_free_sgpr\s+(\d+)")
_AGPR_PATTERN = re.compile(r"\.amdhsa_accum_offset\s+(\d+)")  # AGPR offset indicates AGPR usage
_LDS_PATTERN = re.compile(r"\.amdhsa_group_segment_fixed_size\s+(\d+)")
_SCRATCH_PATTERN = re.compile(r"\.amdhsa_private_segment_fixed_size\s+(\d+)")
_WAVEFRONT_SIZE_PATTERN = re.compile(r"\.amdhsa_wavefront_size\d+\s+(\d+)")
_WORKGROUP_SIZE_PATTERN = re.compile(r"\.amdhsa_workgroup_processor_mode\s+(\d+)")

# Alternative pattern for architecture from triple
_TRIPLE_PATTERN = re.compile(r"amdgcn-amd-amdhsa--(\w+)")

# End of kernel descriptor
_END_AMDHSA_KERNEL_PATTERN = re.compile(r"\.end_amdhsa_kernel")

# Pattern for kernel function label (kernel_name:)
_KERNEL_LABEL_PATTERN = re.compile(r"^(\S+):$")


def parse_isa_file(file_path: str | Path) -> ISAParseResult:
    """Parse an AMDGCN ISA assembly file.

    Args:
        file_path: Path to the .s, .gcn, or .asm file

    Returns:
        ISAParseResult with parsed kernel metadata and instructions

    Example:
        >>> result = parse_isa_file("kernel.s")
        >>> if result.success:
        ...     for kernel in result.kernels:
        ...         print(f"{kernel.kernel_name}: {kernel.vgpr_count} VGPRs")
    """
    path = Path(file_path)

    if not path.exists():
        return ISAParseResult(
            success=False,
            error=f"File not found: {file_path}",
            file_path=str(file_path),
        )

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return ISAParseResult(
            success=False,
            error=f"Failed to read file: {e}",
            file_path=str(file_path),
        )

    result = parse_isa_text(text)

    # Add file path to result
    return ISAParseResult(
        success=result.success,
        error=result.error,
        kernels=result.kernels,
        instructions=result.instructions,
        raw_text=result.raw_text,
        file_path=str(file_path),
    )


def parse_isa_text(text: str) -> ISAParseResult:
    """Parse AMDGCN ISA assembly from text.

    Args:
        text: Assembly source text

    Returns:
        ISAParseResult with parsed kernel metadata and instructions
        
    Supports:
    - Files with explicit .amdhsa_kernel directives (full metadata)
    - Files with just AMDGCN instructions (inferred metadata from instructions)
    - Files with function labels but no explicit kernel descriptors
    """
    if not text.strip():
        return ISAParseResult(
            success=False,
            error="Empty input text",
            raw_text=text,
        )

    # Detect if this is AMDGCN ISA
    if not _is_amdgcn_isa(text):
        return ISAParseResult(
            success=False,
            error="File does not appear to be AMDGCN ISA (missing .amdgcn_target or .amdhsa_kernel directives)",
            raw_text=text,
        )

    # Extract global architecture target
    global_arch = _extract_architecture(text)

    # Parse instructions first to get line ranges
    instructions = _parse_instructions(text)

    # Find kernel code line ranges from function labels
    kernel_code_ranges = _find_kernel_code_ranges(text)

    # Parse kernels with code ranges
    kernels = _parse_kernels(text, global_arch, kernel_code_ranges)
    
    # If no kernels found via .amdhsa_kernel, try to infer from code structure
    if not kernels:
        kernels = _infer_kernels_from_code(text, global_arch, instructions, kernel_code_ranges)

    return ISAParseResult(
        success=True,
        kernels=tuple(kernels),
        instructions=tuple(instructions),
        raw_text=text,
    )


def _find_kernel_code_ranges(text: str) -> dict[str, tuple[int, int]]:
    """Find the line ranges for each kernel's code section.

    In AMDGCN ISA, kernel code starts with a label like 'kernel_name:'
    and ends when another label starts or s_endpgm is encountered.

    Returns:
        Dict mapping kernel_name -> (start_line, end_line) (1-indexed, inclusive)
    """
    lines = text.splitlines()
    ranges: dict[str, tuple[int, int]] = {}

    current_kernel: Optional[str] = None
    current_start: int = 0

    for line_num, line in enumerate(lines, start=1):
        line_stripped = line.strip()

        # Check for kernel function label
        label_match = _KERNEL_LABEL_PATTERN.match(line_stripped)
        if label_match:
            # Close previous kernel if any
            if current_kernel and current_start > 0:
                ranges[current_kernel] = (current_start, line_num - 1)

            # Start new kernel (label could be kernel name)
            label_name = label_match.group(1)
            # Skip non-kernel labels (e.g., .LBB, .Lfunc_begin)
            if not label_name.startswith("."):
                current_kernel = label_name
                current_start = line_num + 1  # Code starts after the label
            continue

        # Check for s_endpgm which ends a kernel
        if current_kernel and "s_endpgm" in line_stripped.lower():
            ranges[current_kernel] = (current_start, line_num)
            current_kernel = None
            current_start = 0

    # Close any remaining kernel
    if current_kernel and current_start > 0:
        ranges[current_kernel] = (current_start, len(lines))

    return ranges


def _is_amdgcn_isa(text: str) -> bool:
    """Check if text appears to be AMDGCN ISA assembly.
    
    Supports detection via:
    - Explicit directives (.amdgcn_target, .amdhsa_kernel)
    - AMDGCN-specific instruction patterns (v_*, s_*, global_*, ds_*, etc.)
    - AMD GPU architecture mentions (gfx*, mi100, mi200, etc.)
    """
    # Look for characteristic directives
    has_target = ".amdgcn_target" in text or "amdgcn-amd-amdhsa" in text
    has_kernel = ".amdhsa_kernel" in text

    # AMDGCN-specific instructions - expanded list
    amdgcn_instruction_patterns = [
        r"\bv_mfma_",           # Matrix FMA instructions
        r"\bs_waitcnt\b",       # Wait count
        r"\bglobal_load",       # Global memory load
        r"\bglobal_store",      # Global memory store
        r"\bds_read",           # LDS read
        r"\bds_write",          # LDS write
        r"\bflat_load",         # Flat memory load
        r"\bflat_store",        # Flat memory store
        r"\bv_add_[fiu]",       # Vector add (float/int/unsigned)
        r"\bv_mul_[fiu]",       # Vector multiply
        r"\bv_fma_f",           # Vector FMA
        r"\bv_mac_f",           # Vector MAC
        r"\bv_mov_b32\b",       # Vector move
        r"\bv_cmp_",            # Vector compare
        r"\bv_cndmask_",        # Vector conditional mask
        r"\bv_lshlrev_",        # Vector left shift
        r"\bv_lshrrev_",        # Vector right shift
        r"\bv_add_co_",         # Vector add with carry out
        r"\bv_addc_co_",        # Vector add with carry in/out
        r"\bs_mov_b32\b",       # Scalar move
        r"\bs_mov_b64\b",       # Scalar move 64-bit
        r"\bs_load_",           # Scalar load
        r"\bs_store_",          # Scalar store
        r"\bs_add_[iu]",        # Scalar add
        r"\bs_mul_[iu]",        # Scalar multiply
        r"\bs_cmp_",            # Scalar compare
        r"\bs_branch\b",        # Scalar branch
        r"\bs_cbranch_",        # Scalar conditional branch
        r"\bs_endpgm\b",        # End program
        r"\bs_barrier\b",       # Barrier
        r"\bs_and_b",           # Scalar AND
        r"\bs_or_b",            # Scalar OR
        r"\bs_xor_b",           # Scalar XOR
        r"\bv_pk_",             # Packed operations (FP16, etc.)
        r"\bv_exp_f",           # Vector exp
        r"\bv_log_f",           # Vector log
        r"\bv_rcp_f",           # Vector reciprocal
        r"\bv_rsq_f",           # Vector reciprocal sqrt
        r"\bv_sqrt_f",          # Vector sqrt
        r"\bbuffer_load",       # Buffer load
        r"\bbuffer_store",      # Buffer store
    ]
    
    has_amdgcn_instructions = any(
        re.search(pattern, text) for pattern in amdgcn_instruction_patterns
    )
    
    # Also check for architecture mentions
    has_arch_mention = bool(re.search(r"\bgfx\d{3,4}\b", text, re.IGNORECASE))

    return has_target or has_kernel or has_amdgcn_instructions or has_arch_mention


def _extract_architecture(text: str) -> str:
    """Extract target architecture from assembly text."""
    # Try .amdgcn_target directive first
    match = _TARGET_PATTERN.search(text)
    if match:
        target = match.group(1)
        # Extract gfx* from target string
        triple_match = _TRIPLE_PATTERN.search(target)
        if triple_match:
            return triple_match.group(1)
        # Fallback: return last component
        parts = target.split("--")
        if len(parts) > 1:
            return parts[-1]
        return target

    return "unknown"


def _parse_kernels(
    text: str,
    default_arch: str,
    kernel_code_ranges: Optional[dict[str, tuple[int, int]]] = None,
) -> list[KernelMetadata]:
    """Parse all kernel definitions from assembly text.

    Args:
        text: Assembly source text
        default_arch: Default architecture from .amdgcn_target
        kernel_code_ranges: Optional dict mapping kernel names to (start_line, end_line)
    """
    kernels = []
    lines = text.splitlines()

    if kernel_code_ranges is None:
        kernel_code_ranges = {}

    current_kernel_name: Optional[str] = None
    current_kernel_data: dict = {}

    for line in lines:
        line_stripped = line.strip()

        # Start of kernel descriptor
        kernel_match = _KERNEL_NAME_PATTERN.match(line_stripped)
        if kernel_match:
            # Save previous kernel if exists
            if current_kernel_name:
                kernels.append(_build_kernel_metadata(
                    current_kernel_name, current_kernel_data, default_arch, kernel_code_ranges
                ))

            current_kernel_name = kernel_match.group(1)
            current_kernel_data = {}
            continue

        # End of kernel descriptor
        if _END_AMDHSA_KERNEL_PATTERN.match(line_stripped):
            if current_kernel_name:
                kernels.append(_build_kernel_metadata(
                    current_kernel_name, current_kernel_data, default_arch, kernel_code_ranges
                ))
                current_kernel_name = None
                current_kernel_data = {}
            continue

        # Skip if not in kernel descriptor
        if not current_kernel_name:
            continue

        # Parse kernel directives
        vgpr_match = _VGPR_PATTERN.match(line_stripped)
        if vgpr_match:
            current_kernel_data["vgpr_count"] = int(vgpr_match.group(1))
            continue

        sgpr_match = _SGPR_PATTERN.match(line_stripped)
        if sgpr_match:
            current_kernel_data["sgpr_count"] = int(sgpr_match.group(1))
            continue

        agpr_match = _AGPR_PATTERN.match(line_stripped)
        if agpr_match:
            # AGPR offset indicates where AGPRs start in the VGPR space
            # Higher offset means more VGPRs used before AGPRs
            current_kernel_data["agpr_offset"] = int(agpr_match.group(1))
            continue

        lds_match = _LDS_PATTERN.match(line_stripped)
        if lds_match:
            current_kernel_data["lds_size"] = int(lds_match.group(1))
            continue

        scratch_match = _SCRATCH_PATTERN.match(line_stripped)
        if scratch_match:
            current_kernel_data["scratch_size"] = int(scratch_match.group(1))
            continue

    # Don't forget the last kernel
    if current_kernel_name:
        kernels.append(_build_kernel_metadata(
            current_kernel_name, current_kernel_data, default_arch, kernel_code_ranges
        ))

    return kernels


def _infer_kernels_from_code(
    text: str,
    default_arch: str,
    instructions: list[InstructionInfo],
    kernel_code_ranges: dict[str, tuple[int, int]],
) -> list[KernelMetadata]:
    """Infer kernel metadata from code when .amdhsa_kernel directives are missing.
    
    This handles files that contain AMDGCN instructions but lack explicit
    kernel descriptors. We infer:
    - Kernel names from function labels
    - Register usage by analyzing instructions
    - LDS usage from ds_* instructions
    """
    kernels = []
    
    # If we have kernel code ranges from labels, use those
    if kernel_code_ranges:
        for kernel_name, (start_line, end_line) in kernel_code_ranges.items():
            # Analyze instructions within this kernel's range
            kernel_instructions = [
                inst for inst in instructions
                if start_line <= inst.line_number <= end_line
            ]
            
            # Infer register usage from instructions
            vgpr_count, sgpr_count, agpr_count = _infer_register_usage(kernel_instructions)
            
            # Check for LDS usage
            has_lds = any(
                inst.mnemonic.startswith("ds_") for inst in kernel_instructions
            )
            
            kernels.append(KernelMetadata(
                kernel_name=kernel_name,
                architecture=default_arch,
                vgpr_count=vgpr_count,
                sgpr_count=sgpr_count,
                agpr_count=agpr_count,
                lds_size=256 if has_lds else 0,  # Assume some LDS if ds_* instructions present
                scratch_size=0,
                code_start_line=start_line,
                code_end_line=end_line,
            ))
    
    # If no labels found, treat whole file as one kernel
    elif instructions:
        vgpr_count, sgpr_count, agpr_count = _infer_register_usage(instructions)
        has_lds = any(inst.mnemonic.startswith("ds_") for inst in instructions)
        
        kernels.append(KernelMetadata(
            kernel_name="<anonymous_kernel>",
            architecture=default_arch,
            vgpr_count=vgpr_count,
            sgpr_count=sgpr_count,
            agpr_count=agpr_count,
            lds_size=256 if has_lds else 0,
            scratch_size=0,
            code_start_line=1,
            code_end_line=len(text.splitlines()),
        ))
    
    return kernels


def _infer_register_usage(instructions: list[InstructionInfo]) -> tuple[int, int, int]:
    """Infer VGPR, SGPR, and AGPR usage from instructions.
    
    Returns:
        Tuple of (vgpr_count, sgpr_count, agpr_count)
    """
    max_vgpr = 0
    max_sgpr = 0
    max_agpr = 0
    
    # Patterns to extract register numbers
    vgpr_pattern = re.compile(r'\bv(\d+)\b')
    sgpr_pattern = re.compile(r'\bs(\d+)\b')
    agpr_pattern = re.compile(r'\ba(\d+)\b')
    
    # Also handle register ranges like v[0:3]
    vgpr_range_pattern = re.compile(r'\bv\[(\d+):(\d+)\]')
    sgpr_range_pattern = re.compile(r'\bs\[(\d+):(\d+)\]')
    agpr_range_pattern = re.compile(r'\ba\[(\d+):(\d+)\]')
    
    for inst in instructions:
        raw = inst.raw_text
        
        # Single registers
        for match in vgpr_pattern.finditer(raw):
            max_vgpr = max(max_vgpr, int(match.group(1)) + 1)
        for match in sgpr_pattern.finditer(raw):
            max_sgpr = max(max_sgpr, int(match.group(1)) + 1)
        for match in agpr_pattern.finditer(raw):
            max_agpr = max(max_agpr, int(match.group(1)) + 1)
        
        # Register ranges
        for match in vgpr_range_pattern.finditer(raw):
            max_vgpr = max(max_vgpr, int(match.group(2)) + 1)
        for match in sgpr_range_pattern.finditer(raw):
            max_sgpr = max(max_sgpr, int(match.group(2)) + 1)
        for match in agpr_range_pattern.finditer(raw):
            max_agpr = max(max_agpr, int(match.group(2)) + 1)
    
    # Round up to reasonable minimums
    if max_vgpr > 0:
        max_vgpr = max(max_vgpr, 4)  # At least 4 VGPRs if any are used
    if max_sgpr > 0:
        max_sgpr = max(max_sgpr, 8)  # At least 8 SGPRs if any are used
    
    return max_vgpr, max_sgpr, max_agpr


def _build_kernel_metadata(
    name: str,
    data: dict,
    default_arch: str,
    kernel_code_ranges: Optional[dict[str, tuple[int, int]]] = None,
) -> KernelMetadata:
    """Build KernelMetadata from parsed data."""
    # Calculate AGPR count from offset if available
    # AGPRs are allocated after VGPRs, so AGPR_count = VGPR_count - AGPR_offset
    vgpr_count = data.get("vgpr_count", 0)
    agpr_offset = data.get("agpr_offset", vgpr_count)
    agpr_count = max(0, vgpr_count - agpr_offset) if agpr_offset < vgpr_count else 0

    # Get code line range if available
    code_start_line = None
    code_end_line = None
    if kernel_code_ranges and name in kernel_code_ranges:
        code_start_line, code_end_line = kernel_code_ranges[name]

    return KernelMetadata(
        kernel_name=name,
        architecture=default_arch,
        vgpr_count=vgpr_count,
        sgpr_count=data.get("sgpr_count", 0),
        agpr_count=agpr_count,
        lds_size=data.get("lds_size", 0),
        scratch_size=data.get("scratch_size", 0),
        code_start_line=code_start_line,
        code_end_line=code_end_line,
    )


def _parse_instructions(text: str) -> list[InstructionInfo]:
    """Parse all instructions from assembly text."""
    instructions = []
    lines = text.splitlines()

    in_code_section = False

    for line_num, line in enumerate(lines, start=1):
        line_stripped = line.strip()

        # Track code section (after .text directive)
        if line_stripped.startswith(".text"):
            in_code_section = True
            continue

        # Skip non-code sections
        if line_stripped.startswith(".section"):
            in_code_section = ".text" in line_stripped
            continue

        # Skip if not in code section and line looks like a directive
        if not in_code_section and line_stripped.startswith("."):
            continue

        # Try to extract mnemonic
        mnemonic = extract_mnemonic(line)
        if not mnemonic:
            continue

        # Classify instruction
        category = classify_instruction(mnemonic)

        # Extract operands (everything after mnemonic, before comment)
        operands = _extract_operands(line, mnemonic)

        # Extract comment
        comment = _extract_comment(line)

        instructions.append(InstructionInfo(
            line_number=line_num,
            raw_text=line,
            mnemonic=mnemonic,
            category=category,
            operands=tuple(operands),
            comment=comment,
        ))

    return instructions


def _extract_operands(line: str, mnemonic: str) -> list[str]:
    """Extract operands from instruction line."""
    # Remove comment
    if ";" in line:
        line = line.split(";")[0]
    if "//" in line:
        line = line.split("//")[0]

    line = line.strip()

    # Find mnemonic position and extract rest
    mnemonic_lower = mnemonic.lower()
    line_lower = line.lower()

    idx = line_lower.find(mnemonic_lower)
    if idx == -1:
        return []

    operand_str = line[idx + len(mnemonic):].strip()
    if not operand_str:
        return []

    # Split by comma, handling potential nested brackets
    operands = []
    current = ""
    bracket_depth = 0

    for char in operand_str:
        if char in "([{":
            bracket_depth += 1
            current += char
        elif char in ")]}":
            bracket_depth -= 1
            current += char
        elif char == "," and bracket_depth == 0:
            if current.strip():
                operands.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        operands.append(current.strip())

    return operands


def _extract_comment(line: str) -> Optional[str]:
    """Extract inline comment from instruction line."""
    if ";" in line:
        return line.split(";", 1)[1].strip()
    if "//" in line:
        return line.split("//", 1)[1].strip()
    return None
