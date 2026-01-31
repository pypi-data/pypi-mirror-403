"""Types for ISA analysis tool."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ISAAnalysisResult:
    """Result of ISA analysis for AMD GPU code object."""

    kernel_name: str
    architecture: str  # e.g., "gfx942"

    # Register usage
    vgpr_count: int
    sgpr_count: int
    agpr_count: int
    vgpr_spill_count: int
    sgpr_spill_count: int

    # Memory
    lds_bytes: int
    global_loads: int
    global_stores: int
    lds_ops: int

    # Instructions
    mfma_count: int
    fma_count: int
    packed_ops_count: int
    waitcnt_full_stalls: int  # vmcnt(0) or lgkmcnt(0)
    barriers: int

    # Raw data
    isa_text: str
    metadata_yaml: str
    annotated_isa_text: str
