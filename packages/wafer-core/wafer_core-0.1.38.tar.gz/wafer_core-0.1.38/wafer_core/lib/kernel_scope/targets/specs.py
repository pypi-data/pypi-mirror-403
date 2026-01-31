"""GPU target specifications.

Hardware constants for AMD GPU architectures used for occupancy calculations
and resource limit analysis.

Sources:
- AMD CDNA3 ISA Reference Manual
- AMD ROCm Documentation
- rocprof-compute SOC definitions
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TargetSpecs:
    """Hardware specifications for a GPU target.

    Attributes:
        name: Architecture name (e.g., "gfx90a")
        series: GPU series (e.g., "MI200", "MI300")
        vgprs_per_cu: Total VGPRs per Compute Unit
        sgprs_per_cu: Total SGPRs per Compute Unit
        lds_per_cu: LDS size per CU in bytes
        max_waves_per_cu: Maximum wavefronts per CU
        vgpr_granularity: VGPR allocation granularity
        sgpr_granularity: SGPR allocation granularity
        wavefront_size: Wavefront size (typically 64 for AMD)
        l2_banks: Number of L2 cache banks
        lds_banks_per_cu: LDS banks per CU
    """

    name: str
    series: str
    vgprs_per_cu: int
    sgprs_per_cu: int
    lds_per_cu: int
    max_waves_per_cu: int
    vgpr_granularity: int
    sgpr_granularity: int
    wavefront_size: int = 64
    l2_banks: int = 32
    lds_banks_per_cu: int = 32


# GFX908 - MI100
_GFX908_SPECS = TargetSpecs(
    name="gfx908",
    series="MI100",
    vgprs_per_cu=512,
    sgprs_per_cu=800,
    lds_per_cu=65536,  # 64 KB
    max_waves_per_cu=10,
    vgpr_granularity=8,
    sgpr_granularity=16,
    l2_banks=32,
    lds_banks_per_cu=32,
)

# GFX90A - MI200 series (MI210, MI250, MI250X)
_GFX90A_SPECS = TargetSpecs(
    name="gfx90a",
    series="MI200",
    vgprs_per_cu=512,
    sgprs_per_cu=800,
    lds_per_cu=65536,  # 64 KB
    max_waves_per_cu=10,
    vgpr_granularity=8,
    sgpr_granularity=16,
    l2_banks=32,
    lds_banks_per_cu=32,
)

# GFX940 - MI300A A0
_GFX940_SPECS = TargetSpecs(
    name="gfx940",
    series="MI300",
    vgprs_per_cu=512,
    sgprs_per_cu=800,
    lds_per_cu=65536,  # 64 KB
    max_waves_per_cu=10,
    vgpr_granularity=8,
    sgpr_granularity=16,
    l2_banks=32,
    lds_banks_per_cu=32,
)

# GFX941 - MI300X A0
_GFX941_SPECS = TargetSpecs(
    name="gfx941",
    series="MI300",
    vgprs_per_cu=512,
    sgprs_per_cu=800,
    lds_per_cu=65536,  # 64 KB
    max_waves_per_cu=10,
    vgpr_granularity=8,
    sgpr_granularity=16,
    l2_banks=32,
    lds_banks_per_cu=32,
)

# GFX942 - MI300A/X A1, MI325X
_GFX942_SPECS = TargetSpecs(
    name="gfx942",
    series="MI300",
    vgprs_per_cu=512,
    sgprs_per_cu=800,
    lds_per_cu=65536,  # 64 KB
    max_waves_per_cu=10,
    vgpr_granularity=8,
    sgpr_granularity=16,
    l2_banks=32,
    lds_banks_per_cu=32,
)

# GFX950 - MI350 series
_GFX950_SPECS = TargetSpecs(
    name="gfx950",
    series="MI350",
    vgprs_per_cu=512,
    sgprs_per_cu=800,
    lds_per_cu=65536,  # 64 KB
    max_waves_per_cu=10,
    vgpr_granularity=8,
    sgpr_granularity=16,
    l2_banks=32,
    lds_banks_per_cu=32,
)

# Default/unknown specs (conservative values)
_DEFAULT_SPECS = TargetSpecs(
    name="unknown",
    series="unknown",
    vgprs_per_cu=512,
    sgprs_per_cu=800,
    lds_per_cu=65536,
    max_waves_per_cu=10,
    vgpr_granularity=8,
    sgpr_granularity=16,
)


# Map of architecture names to specs
_TARGET_MAP: dict[str, TargetSpecs] = {
    "gfx908": _GFX908_SPECS,
    "gfx90a": _GFX90A_SPECS,
    "gfx940": _GFX940_SPECS,
    "gfx941": _GFX941_SPECS,
    "gfx942": _GFX942_SPECS,
    "gfx950": _GFX950_SPECS,
}

# Supported target list
SUPPORTED_TARGETS = list(_TARGET_MAP.keys())


def get_target_specs(architecture: str) -> TargetSpecs:
    """Get hardware specifications for a target architecture.

    Args:
        architecture: Architecture name (e.g., "gfx90a", "gfx942")

    Returns:
        TargetSpecs for the architecture, or default specs if unknown

    Example:
        >>> specs = get_target_specs("gfx90a")
        >>> print(f"VGPRs per CU: {specs.vgprs_per_cu}")
        VGPRs per CU: 512
    """
    # Normalize architecture name
    arch_lower = architecture.lower().strip()

    # Try exact match
    if arch_lower in _TARGET_MAP:
        return _TARGET_MAP[arch_lower]

    # Try to extract gfx* from longer strings
    if "gfx" in arch_lower:
        for target in _TARGET_MAP:
            if target in arch_lower:
                return _TARGET_MAP[target]

    return _DEFAULT_SPECS
