"""Type definitions for AMDGCN ISA parsing and analysis.

These types follow frozen dataclass patterns per code style guidelines.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class InstructionCategory(Enum):
    """Categories of AMDGCN instructions for analysis.

    Based on AMD CDNA3 ISA Reference Manual instruction classification.
    """

    VALU = auto()  # Vector ALU: v_add_*, v_mul_*, v_fma_*, etc.
    SALU = auto()  # Scalar ALU: s_add_*, s_mul_*, s_and_*, etc.
    VMEM = auto()  # Vector memory: global_load_*, global_store_*, buffer_*
    SMEM = auto()  # Scalar memory: s_load_*, s_store_*
    LDS = auto()  # Local Data Share: ds_read_*, ds_write_*
    MFMA = auto()  # Matrix FMA: v_mfma_f32_*, v_mfma_f16_*
    CONTROL = auto()  # Control flow: s_branch_*, s_cbranch_*, s_endpgm
    SYNC = auto()  # Synchronization: s_barrier, s_waitcnt
    EXPORT = auto()  # Export: exp_*
    SPILL = auto()  # Register spill operations: scratch_store_*, scratch_load_*
    OTHER = auto()  # Uncategorized instructions


@dataclass(frozen=True)
class InstructionInfo:
    """Information about a single instruction in the ISA.

    Attributes:
        line_number: Line number in the source file (1-indexed)
        raw_text: Raw instruction text from the assembly
        mnemonic: Instruction mnemonic (e.g., "v_add_f32")
        category: Instruction category for analysis
        operands: List of operand strings
        comment: Optional inline comment
    """

    line_number: int
    raw_text: str
    mnemonic: str
    category: InstructionCategory
    operands: tuple[str, ...] = field(default_factory=tuple)
    comment: Optional[str] = None


@dataclass(frozen=True)
class KernelMetadata:
    """Metadata extracted from AMDGCN ISA kernel directives.

    These values come from .amdhsa_* directives in the assembly.

    Attributes:
        kernel_name: Name from .amdhsa_kernel directive
        architecture: Target architecture (e.g., "gfx90a", "gfx942")
        vgpr_count: Vector GPR allocation from .amdhsa_next_free_vgpr
        sgpr_count: Scalar GPR allocation from .amdhsa_next_free_sgpr
        agpr_count: Accumulator GPR count (for MFMA, MI100+)
        lds_size: LDS allocation in bytes from .amdhsa_group_segment_fixed_size
        scratch_size: Private scratch memory from .amdhsa_private_segment_fixed_size
        wavefront_size: Wavefront size (32 or 64)
        workgroup_size: Maximum workgroup size hint
        kernel_code_entry_offset: Offset to kernel code
        code_start_line: First line of kernel code (1-indexed, inclusive)
        code_end_line: Last line of kernel code (1-indexed, inclusive)
    """

    kernel_name: str
    architecture: str
    vgpr_count: int
    sgpr_count: int
    agpr_count: int = 0
    lds_size: int = 0
    scratch_size: int = 0
    wavefront_size: int = 64
    workgroup_size: Optional[int] = None
    kernel_code_entry_offset: int = 0
    code_start_line: Optional[int] = None
    code_end_line: Optional[int] = None


@dataclass(frozen=True)
class ISAParseResult:
    """Result of parsing an AMDGCN ISA file.

    Attributes:
        success: Whether parsing succeeded
        error: Error message if parsing failed
        kernels: List of kernel metadata (multiple kernels per file possible)
        instructions: List of all instructions in the file
        raw_text: Original source text
        file_path: Path to the source file (if applicable)
    """

    success: bool
    error: Optional[str] = None
    kernels: tuple[KernelMetadata, ...] = field(default_factory=tuple)
    instructions: tuple[InstructionInfo, ...] = field(default_factory=tuple)
    raw_text: str = ""
    file_path: Optional[str] = None


@dataclass(frozen=True)
class SpillInfo:
    """Information about a register spill operation.

    Attributes:
        instruction: The spill instruction
        register_type: "vgpr" or "sgpr"
        is_store: True for spill store, False for spill load
    """

    instruction: InstructionInfo
    register_type: str  # "vgpr" or "sgpr"
    is_store: bool


@dataclass(frozen=True)
class InstructionMix:
    """Breakdown of instructions by category.

    Attributes:
        valu_count: Vector ALU instruction count
        salu_count: Scalar ALU instruction count
        vmem_count: Vector memory instruction count
        smem_count: Scalar memory instruction count
        lds_count: LDS operation count
        mfma_count: Matrix FMA instruction count
        control_count: Control flow instruction count
        sync_count: Synchronization instruction count
        spill_count: Spill operation count
        other_count: Other instruction count
        total_count: Total instruction count
    """

    valu_count: int = 0
    salu_count: int = 0
    vmem_count: int = 0
    smem_count: int = 0
    lds_count: int = 0
    mfma_count: int = 0
    control_count: int = 0
    sync_count: int = 0
    spill_count: int = 0
    other_count: int = 0

    @property
    def total_count(self) -> int:
        """Total instruction count."""
        return (
            self.valu_count
            + self.salu_count
            + self.vmem_count
            + self.smem_count
            + self.lds_count
            + self.mfma_count
            + self.control_count
            + self.sync_count
            + self.spill_count
            + self.other_count
        )

    @property
    def compute_count(self) -> int:
        """Total compute instructions (VALU + MFMA)."""
        return self.valu_count + self.mfma_count

    @property
    def memory_count(self) -> int:
        """Total memory instructions (VMEM + SMEM + LDS)."""
        return self.vmem_count + self.smem_count + self.lds_count
