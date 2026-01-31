"""AMDGCN instruction classification database.

This module provides instruction pattern matching and categorization
based on AMD CDNA ISA Reference Manual.

Why: Proper instruction classification is essential for MFMA density,
instruction mix analysis, and spill detection.
"""

import re
from typing import Optional

from wafer_core.lib.kernel_scope.amdgcn.types import InstructionCategory


# Instruction pattern -> category mapping
# Order matters: more specific patterns should come first
_INSTRUCTION_PATTERNS: list[tuple[re.Pattern, InstructionCategory]] = [
    # MFMA instructions (Matrix Fused Multiply-Add) - highest priority
    (re.compile(r"^v_mfma_"), InstructionCategory.MFMA),
    (re.compile(r"^v_smfmac_"), InstructionCategory.MFMA),  # Sparse MFMA
    # Spill operations - detect before general VMEM
    (re.compile(r"^scratch_store_"), InstructionCategory.SPILL),
    (re.compile(r"^scratch_load_"), InstructionCategory.SPILL),
    # Buffer operations to scratch space are also spills
    # (detected by context, but pattern helps)
    # LDS operations
    (re.compile(r"^ds_read"), InstructionCategory.LDS),
    (re.compile(r"^ds_write"), InstructionCategory.LDS),
    (re.compile(r"^ds_bpermute"), InstructionCategory.LDS),
    (re.compile(r"^ds_permute"), InstructionCategory.LDS),
    (re.compile(r"^ds_swizzle"), InstructionCategory.LDS),
    (re.compile(r"^ds_add"), InstructionCategory.LDS),
    (re.compile(r"^ds_sub"), InstructionCategory.LDS),
    (re.compile(r"^ds_rsub"), InstructionCategory.LDS),
    (re.compile(r"^ds_inc"), InstructionCategory.LDS),
    (re.compile(r"^ds_dec"), InstructionCategory.LDS),
    (re.compile(r"^ds_min"), InstructionCategory.LDS),
    (re.compile(r"^ds_max"), InstructionCategory.LDS),
    (re.compile(r"^ds_and"), InstructionCategory.LDS),
    (re.compile(r"^ds_or"), InstructionCategory.LDS),
    (re.compile(r"^ds_xor"), InstructionCategory.LDS),
    (re.compile(r"^ds_mskor"), InstructionCategory.LDS),
    (re.compile(r"^ds_cmpst"), InstructionCategory.LDS),
    (re.compile(r"^ds_append"), InstructionCategory.LDS),
    (re.compile(r"^ds_consume"), InstructionCategory.LDS),
    # Vector memory operations
    (re.compile(r"^global_load"), InstructionCategory.VMEM),
    (re.compile(r"^global_store"), InstructionCategory.VMEM),
    (re.compile(r"^global_atomic"), InstructionCategory.VMEM),
    (re.compile(r"^buffer_load"), InstructionCategory.VMEM),
    (re.compile(r"^buffer_store"), InstructionCategory.VMEM),
    (re.compile(r"^buffer_atomic"), InstructionCategory.VMEM),
    (re.compile(r"^flat_load"), InstructionCategory.VMEM),
    (re.compile(r"^flat_store"), InstructionCategory.VMEM),
    (re.compile(r"^flat_atomic"), InstructionCategory.VMEM),
    (re.compile(r"^tbuffer_load"), InstructionCategory.VMEM),
    (re.compile(r"^tbuffer_store"), InstructionCategory.VMEM),
    # Scalar memory operations
    (re.compile(r"^s_load_"), InstructionCategory.SMEM),
    (re.compile(r"^s_store_"), InstructionCategory.SMEM),
    (re.compile(r"^s_buffer_load"), InstructionCategory.SMEM),
    (re.compile(r"^s_buffer_store"), InstructionCategory.SMEM),
    (re.compile(r"^s_memtime"), InstructionCategory.SMEM),
    (re.compile(r"^s_memrealtime"), InstructionCategory.SMEM),
    (re.compile(r"^s_dcache"), InstructionCategory.SMEM),
    (re.compile(r"^s_gl1_inv"), InstructionCategory.SMEM),
    # Synchronization
    (re.compile(r"^s_barrier"), InstructionCategory.SYNC),
    (re.compile(r"^s_waitcnt"), InstructionCategory.SYNC),
    (re.compile(r"^s_wait_"), InstructionCategory.SYNC),  # s_wait_loadcnt, etc.
    (re.compile(r"^s_sleep"), InstructionCategory.SYNC),
    (re.compile(r"^s_nop"), InstructionCategory.SYNC),
    (re.compile(r"^s_setprio"), InstructionCategory.SYNC),
    # Control flow
    (re.compile(r"^s_branch"), InstructionCategory.CONTROL),
    (re.compile(r"^s_cbranch"), InstructionCategory.CONTROL),
    (re.compile(r"^s_setpc"), InstructionCategory.CONTROL),
    (re.compile(r"^s_swappc"), InstructionCategory.CONTROL),
    (re.compile(r"^s_getpc"), InstructionCategory.CONTROL),
    (re.compile(r"^s_call"), InstructionCategory.CONTROL),
    (re.compile(r"^s_endpgm"), InstructionCategory.CONTROL),
    (re.compile(r"^s_trap"), InstructionCategory.CONTROL),
    (re.compile(r"^s_icache"), InstructionCategory.CONTROL),
    (re.compile(r"^s_inst_prefetch"), InstructionCategory.CONTROL),
    # Export
    (re.compile(r"^exp "), InstructionCategory.EXPORT),
    # Vector ALU (catch-all for v_* instructions)
    (re.compile(r"^v_"), InstructionCategory.VALU),
    # Scalar ALU (catch-all for s_* instructions not matched above)
    (re.compile(r"^s_"), InstructionCategory.SALU),
]

# Packed instruction patterns (for packed instruction usage analysis)
_PACKED_INSTRUCTION_PATTERN = re.compile(r"^v_pk_")

# FMA instruction patterns
_FMA_INSTRUCTION_PATTERNS = [
    re.compile(r"^v_fma_"),
    re.compile(r"^v_fmac_"),
    re.compile(r"^v_fmaak_"),
    re.compile(r"^v_fmamk_"),
    re.compile(r"^v_pk_fma"),
]

# Full stall pattern (waitcnt 0 or equivalent)
_FULL_STALL_PATTERNS = [
    re.compile(r"s_waitcnt\s+0\b"),
    re.compile(r"s_waitcnt\s+vmcnt\(0\)\s+lgkmcnt\(0\)"),
    re.compile(r"s_wait_loadcnt\s+0x0"),
    re.compile(r"s_wait_storecnt\s+0x0"),
]


def classify_instruction(mnemonic: str) -> InstructionCategory:
    """Classify an instruction mnemonic into a category.

    Args:
        mnemonic: The instruction mnemonic (e.g., "v_add_f32", "s_load_dword")

    Returns:
        The instruction category

    Example:
        >>> classify_instruction("v_mfma_f32_32x32x8f16")
        InstructionCategory.MFMA
        >>> classify_instruction("global_load_dwordx4")
        InstructionCategory.VMEM
    """
    mnemonic_lower = mnemonic.lower().strip()

    for pattern, category in _INSTRUCTION_PATTERNS:
        if pattern.match(mnemonic_lower):
            return category

    return InstructionCategory.OTHER


def is_packed_instruction(mnemonic: str) -> bool:
    """Check if instruction is a packed vector instruction (v_pk_*).

    Packed instructions operate on multiple data elements simultaneously
    and are more efficient than their scalar equivalents.

    Args:
        mnemonic: The instruction mnemonic

    Returns:
        True if this is a packed instruction
    """
    return bool(_PACKED_INSTRUCTION_PATTERN.match(mnemonic.lower().strip()))


def is_fma_instruction(mnemonic: str) -> bool:
    """Check if instruction is a fused multiply-add (FMA).

    FMA instructions compute a*b+c in a single operation with better
    precision and performance than separate multiply and add.

    Args:
        mnemonic: The instruction mnemonic

    Returns:
        True if this is an FMA instruction
    """
    mnemonic_lower = mnemonic.lower().strip()
    return any(pattern.match(mnemonic_lower) for pattern in _FMA_INSTRUCTION_PATTERNS)


def is_full_stall(instruction_text: str) -> bool:
    """Check if instruction is a full stall (waitcnt 0 or equivalent).

    Full stalls wait for all outstanding memory operations to complete
    and can significantly impact performance.

    Args:
        instruction_text: The full instruction text including operands

    Returns:
        True if this is a full stall
    """
    text_lower = instruction_text.lower().strip()
    return any(pattern.search(text_lower) for pattern in _FULL_STALL_PATTERNS)


def is_barrier(mnemonic: str) -> bool:
    """Check if instruction is a barrier.

    Args:
        mnemonic: The instruction mnemonic

    Returns:
        True if this is a barrier instruction
    """
    return mnemonic.lower().strip() == "s_barrier"


def get_spill_type(mnemonic: str) -> Optional[str]:
    """Get the type of spill operation, if any.

    Args:
        mnemonic: The instruction mnemonic

    Returns:
        "store" for spill stores, "load" for spill loads, None if not a spill
    """
    mnemonic_lower = mnemonic.lower().strip()

    if mnemonic_lower.startswith("scratch_store"):
        return "store"
    if mnemonic_lower.startswith("scratch_load"):
        return "load"

    return None


def extract_mnemonic(instruction_line: str) -> Optional[str]:
    """Extract the instruction mnemonic from an assembly line.

    Handles various assembly line formats including labels, comments,
    and directives.

    Args:
        instruction_line: A line from the assembly file

    Returns:
        The instruction mnemonic, or None if not an instruction

    Example:
        >>> extract_mnemonic("  v_add_f32 v0, v1, v2  ; comment")
        "v_add_f32"
        >>> extract_mnemonic(".L_label:")
        None
    """
    line = instruction_line.strip()

    # Skip empty lines
    if not line:
        return None

    # Skip comments
    if line.startswith(";") or line.startswith("//"):
        return None

    # Skip directives (start with .)
    if line.startswith("."):
        return None

    # Skip labels (end with :)
    if ":" in line and not line.startswith((" ", "\t")):
        # Could be a label, check if it's just a label
        label_part = line.split(":")[0]
        if label_part.replace("_", "").replace(".", "").isalnum():
            # It's a label, check for instruction after colon
            after_colon = line.split(":", 1)[1].strip()
            if after_colon:
                return extract_mnemonic(after_colon)
            return None

    # Remove inline comment
    if ";" in line:
        line = line.split(";")[0].strip()
    if "//" in line:
        line = line.split("//")[0].strip()

    if not line:
        return None

    # Extract first word as mnemonic
    parts = line.split()
    if parts:
        return parts[0]

    return None
