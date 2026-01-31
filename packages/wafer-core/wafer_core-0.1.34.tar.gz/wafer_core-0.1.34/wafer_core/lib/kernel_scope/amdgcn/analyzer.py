"""AMDGCN ISA Analyzer.

Analyzes parsed AMDGCN ISA to compute performance metrics including:
- Register pressure (VGPR/SGPR usage)
- Register spills
- MFMA density
- Instruction mix
- Wave occupancy limits

Design: Wafer-436 - AMD Kernel Scope
"""

from dataclasses import dataclass, field
from typing import Optional

from wafer_core.lib.kernel_scope.amdgcn.types import (
    ISAParseResult,
    KernelMetadata,
    InstructionInfo,
    InstructionCategory,
    InstructionMix,
    SpillInfo,
)
from wafer_core.lib.kernel_scope.amdgcn.instruction_db import (
    is_packed_instruction,
    is_fma_instruction,
    is_full_stall,
    is_barrier,
    get_spill_type,
)
from wafer_core.lib.kernel_scope.targets import get_target_specs


@dataclass(frozen=True)
class ISAAnalysis:
    """Complete analysis results for a kernel.

    Attributes:
        kernel_name: Name of the analyzed kernel
        architecture: Target GPU architecture
        vgpr_count: Vector GPR allocation
        sgpr_count: Scalar GPR allocation
        agpr_count: Accumulator GPR count
        lds_size: LDS allocation in bytes
        scratch_size: Private scratch memory in bytes
        instruction_mix: Breakdown by instruction category
        spill_count: Total spill operations
        vgpr_spill_count: VGPR spill operations
        sgpr_spill_count: SGPR spill operations
        mfma_count: Number of MFMA instructions
        mfma_density_pct: MFMA as percentage of compute ops
        packed_ops_count: Number of packed instructions
        fma_count: Number of FMA instructions
        barrier_count: Number of barrier instructions
        full_stall_count: Number of full stall waitcnts
        global_load_count: Number of global load operations
        global_store_count: Number of global store operations
        lds_ops_count: Number of LDS operations
        max_waves_vgpr: Max waves limited by VGPR
        max_waves_sgpr: Max waves limited by SGPR
        max_waves_lds: Max waves limited by LDS
        theoretical_occupancy: Theoretical max wavefronts per CU
        spill_instructions: List of spill instruction details
        warnings: List of performance warnings
    """

    kernel_name: str
    architecture: str

    # Register usage
    vgpr_count: int
    sgpr_count: int
    agpr_count: int = 0

    # Memory allocation
    lds_size: int = 0
    scratch_size: int = 0

    # Instruction analysis
    instruction_mix: InstructionMix = field(default_factory=InstructionMix)
    spill_count: int = 0
    vgpr_spill_count: int = 0
    sgpr_spill_count: int = 0
    mfma_count: int = 0
    mfma_density_pct: float = 0.0
    packed_ops_count: int = 0
    fma_count: int = 0
    barrier_count: int = 0
    full_stall_count: int = 0
    global_load_count: int = 0
    global_store_count: int = 0
    lds_ops_count: int = 0

    # Occupancy
    max_waves_vgpr: int = 0
    max_waves_sgpr: int = 0
    max_waves_lds: int = 0
    theoretical_occupancy: int = 0

    # Detailed info
    spill_instructions: tuple[SpillInfo, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)


def analyze_isa(
    parse_result: ISAParseResult,
    kernel_index: int = 0,
) -> ISAAnalysis:
    """Analyze parsed ISA for a specific kernel.

    Args:
        parse_result: Result from parse_isa_file or parse_isa_text
        kernel_index: Which kernel to analyze (if multiple in file)

    Returns:
        ISAAnalysis with computed metrics

    Raises:
        ValueError: If parse_result is not successful or kernel_index is invalid

    Example:
        >>> from wafer_core.lib.kernel_scope import parse_isa_file, analyze_isa
        >>> parse_result = parse_isa_file("kernel.s")
        >>> analysis = analyze_isa(parse_result)
        >>> print(f"MFMA density: {analysis.mfma_density_pct:.1f}%")
    """
    if not parse_result.success:
        raise ValueError(f"Cannot analyze failed parse result: {parse_result.error}")

    if not parse_result.kernels:
        raise ValueError("No kernels found in parse result")

    if kernel_index >= len(parse_result.kernels):
        raise ValueError(
            f"Kernel index {kernel_index} out of range "
            f"(found {len(parse_result.kernels)} kernels)"
        )

    kernel = parse_result.kernels[kernel_index]

    # Filter instructions to only those belonging to this kernel
    instructions = _filter_instructions_for_kernel(parse_result.instructions, kernel)

    # Compute instruction mix
    instruction_mix = _compute_instruction_mix(instructions)

    # Analyze spills
    spill_instructions, vgpr_spills, sgpr_spills = _analyze_spills(instructions)
    spill_count = len(spill_instructions)

    # Count specific instructions
    mfma_count = instruction_mix.mfma_count
    packed_count = sum(1 for i in instructions if is_packed_instruction(i.mnemonic))
    fma_count = sum(1 for i in instructions if is_fma_instruction(i.mnemonic))
    barrier_count = sum(1 for i in instructions if is_barrier(i.mnemonic))
    full_stall_count = sum(1 for i in instructions if is_full_stall(i.raw_text))

    # Count memory operations
    global_loads = sum(
        1 for i in instructions
        if i.category == InstructionCategory.VMEM and "load" in i.mnemonic.lower()
    )
    global_stores = sum(
        1 for i in instructions
        if i.category == InstructionCategory.VMEM and "store" in i.mnemonic.lower()
    )
    lds_ops = instruction_mix.lds_count

    # Compute MFMA density
    compute_ops = instruction_mix.compute_count
    mfma_density = (mfma_count / compute_ops * 100) if compute_ops > 0 else 0.0

    # Compute occupancy limits
    specs = get_target_specs(kernel.architecture)
    max_waves_vgpr = _compute_max_waves_vgpr(kernel.vgpr_count, specs)
    max_waves_sgpr = _compute_max_waves_sgpr(kernel.sgpr_count, specs)
    max_waves_lds = _compute_max_waves_lds(kernel.lds_size, specs)

    theoretical_occupancy = min(
        max_waves_vgpr,
        max_waves_sgpr,
        max_waves_lds,
        specs.max_waves_per_cu,
    )

    # Generate warnings
    warnings = _generate_warnings(
        kernel=kernel,
        spill_count=spill_count,
        mfma_density=mfma_density,
        full_stall_count=full_stall_count,
        theoretical_occupancy=theoretical_occupancy,
        specs=specs,
    )

    return ISAAnalysis(
        kernel_name=kernel.kernel_name,
        architecture=kernel.architecture,
        vgpr_count=kernel.vgpr_count,
        sgpr_count=kernel.sgpr_count,
        agpr_count=kernel.agpr_count,
        lds_size=kernel.lds_size,
        scratch_size=kernel.scratch_size,
        instruction_mix=instruction_mix,
        spill_count=spill_count,
        vgpr_spill_count=vgpr_spills,
        sgpr_spill_count=sgpr_spills,
        mfma_count=mfma_count,
        mfma_density_pct=mfma_density,
        packed_ops_count=packed_count,
        fma_count=fma_count,
        barrier_count=barrier_count,
        full_stall_count=full_stall_count,
        global_load_count=global_loads,
        global_store_count=global_stores,
        lds_ops_count=lds_ops,
        max_waves_vgpr=max_waves_vgpr,
        max_waves_sgpr=max_waves_sgpr,
        max_waves_lds=max_waves_lds,
        theoretical_occupancy=theoretical_occupancy,
        spill_instructions=tuple(spill_instructions),
        warnings=tuple(warnings),
    )


def _filter_instructions_for_kernel(
    instructions: tuple[InstructionInfo, ...],
    kernel: KernelMetadata,
) -> tuple[InstructionInfo, ...]:
    """Filter instructions to only those belonging to a specific kernel.

    Uses the kernel's code_start_line and code_end_line to determine
    which instructions belong to this kernel.

    If no line range info is available (for backward compatibility),
    returns all instructions.
    """
    # If no line range info, return all instructions (single-kernel file assumption)
    if kernel.code_start_line is None or kernel.code_end_line is None:
        return instructions

    start = kernel.code_start_line
    end = kernel.code_end_line

    return tuple(
        instr for instr in instructions
        if start <= instr.line_number <= end
    )


def _compute_instruction_mix(instructions: tuple[InstructionInfo, ...]) -> InstructionMix:
    """Compute instruction mix from parsed instructions."""
    counts = {cat: 0 for cat in InstructionCategory}

    for instr in instructions:
        counts[instr.category] += 1

    return InstructionMix(
        valu_count=counts[InstructionCategory.VALU],
        salu_count=counts[InstructionCategory.SALU],
        vmem_count=counts[InstructionCategory.VMEM],
        smem_count=counts[InstructionCategory.SMEM],
        lds_count=counts[InstructionCategory.LDS],
        mfma_count=counts[InstructionCategory.MFMA],
        control_count=counts[InstructionCategory.CONTROL],
        sync_count=counts[InstructionCategory.SYNC],
        spill_count=counts[InstructionCategory.SPILL],
        other_count=counts[InstructionCategory.OTHER] + counts[InstructionCategory.EXPORT],
    )


def _analyze_spills(
    instructions: tuple[InstructionInfo, ...]
) -> tuple[list[SpillInfo], int, int]:
    """Analyze spill operations.

    Returns:
        Tuple of (spill_info_list, vgpr_spill_count, sgpr_spill_count)
    """
    spill_infos = []
    vgpr_spills = 0
    sgpr_spills = 0

    for instr in instructions:
        if instr.category != InstructionCategory.SPILL:
            continue

        spill_type = get_spill_type(instr.mnemonic)
        is_store = spill_type == "store"

        # Determine register type from operands or mnemonic
        # VGPR spills typically use scratch_store/load_dword with v registers
        # SGPR spills use s_store/load or buffer ops
        reg_type = "vgpr"  # Default assumption for scratch_ ops

        spill_infos.append(SpillInfo(
            instruction=instr,
            register_type=reg_type,
            is_store=is_store,
        ))

        if reg_type == "vgpr":
            vgpr_spills += 1
        else:
            sgpr_spills += 1

    return spill_infos, vgpr_spills, sgpr_spills


def _compute_max_waves_vgpr(vgpr_count: int, specs) -> int:
    """Compute maximum waves based on VGPR usage.

    Formula: floor(total_vgprs / ceil(vgpr_count / granularity) * granularity)
    """
    if vgpr_count == 0:
        return specs.max_waves_per_cu

    granularity = specs.vgpr_granularity
    total_vgprs = specs.vgprs_per_cu

    # Round up to granularity
    vgprs_allocated = ((vgpr_count + granularity - 1) // granularity) * granularity

    if vgprs_allocated == 0:
        return specs.max_waves_per_cu

    return total_vgprs // vgprs_allocated


def _compute_max_waves_sgpr(sgpr_count: int, specs) -> int:
    """Compute maximum waves based on SGPR usage."""
    if sgpr_count == 0:
        return specs.max_waves_per_cu

    granularity = specs.sgpr_granularity
    total_sgprs = specs.sgprs_per_cu

    # Round up to granularity
    sgprs_allocated = ((sgpr_count + granularity - 1) // granularity) * granularity

    if sgprs_allocated == 0:
        return specs.max_waves_per_cu

    return total_sgprs // sgprs_allocated


def _compute_max_waves_lds(lds_size: int, specs) -> int:
    """Compute maximum waves based on LDS usage."""
    if lds_size == 0:
        return specs.max_waves_per_cu

    total_lds = specs.lds_per_cu

    # Each workgroup gets its LDS allocation
    # Assuming 1 wave per workgroup for simplicity
    # More accurate would require workgroup size info
    return max(1, total_lds // lds_size)


def _generate_warnings(
    kernel: KernelMetadata,
    spill_count: int,
    mfma_density: float,
    full_stall_count: int,
    theoretical_occupancy: int,
    specs,
) -> list[str]:
    """Generate performance warnings based on analysis."""
    warnings = []

    # Spill warning (critical)
    if spill_count > 0:
        warnings.append(
            f"CRITICAL: {spill_count} register spill operations detected. "
            "Spills severely impact performance by using slow scratch memory."
        )

    # Scratch memory warning
    if kernel.scratch_size > 0:
        warnings.append(
            f"WARNING: Kernel allocates {kernel.scratch_size} bytes of scratch memory. "
            "Non-zero scratch usually indicates register spills."
        )

    # Low MFMA density for AI workloads
    if mfma_density < 20.0 and mfma_density > 0:
        warnings.append(
            f"WARNING: Low MFMA density ({mfma_density:.1f}%). "
            "For AI/ML workloads, MFMA should dominate compute ops. "
            "Consider increasing tile sizes or reducing overhead."
        )

    # Full stall warning
    if full_stall_count > 0:
        warnings.append(
            f"WARNING: {full_stall_count} full stall(s) detected (waitcnt 0). "
            "Full stalls wait for all memory operations and reduce throughput."
        )

    # Low occupancy warning
    if theoretical_occupancy < 4:
        warnings.append(
            f"WARNING: Low theoretical occupancy ({theoretical_occupancy} waves/CU). "
            "Consider reducing register pressure or LDS usage."
        )

    # High VGPR usage
    vgpr_threshold = specs.vgprs_per_cu // 4  # 25% threshold
    if kernel.vgpr_count > vgpr_threshold:
        warnings.append(
            f"INFO: High VGPR usage ({kernel.vgpr_count}). "
            f"Each wave uses {kernel.vgpr_count} of {specs.vgprs_per_cu} available VGPRs."
        )

    return warnings
