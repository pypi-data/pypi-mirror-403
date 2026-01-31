"""Wave occupancy calculation.

Computes theoretical wavefront occupancy based on resource usage
(VGPR, SGPR, LDS) and hardware limits.

Design: Wafer-436 - AMD Kernel Scope
"""

from dataclasses import dataclass
from typing import Optional

from wafer_core.lib.kernel_scope.targets import get_target_specs, TargetSpecs


@dataclass(frozen=True)
class OccupancyResult:
    """Result of occupancy calculation.

    Attributes:
        waves_per_cu: Theoretical wavefronts per Compute Unit
        limiting_factor: What resource limits occupancy ("vgpr", "sgpr", "lds", "max")
        vgpr_waves: Max waves based on VGPR usage
        sgpr_waves: Max waves based on SGPR usage
        lds_waves: Max waves based on LDS usage
        occupancy_pct: Occupancy as percentage of theoretical max
    """

    waves_per_cu: int
    limiting_factor: str
    vgpr_waves: int
    sgpr_waves: int
    lds_waves: int
    occupancy_pct: float


def compute_occupancy(
    vgpr_count: int,
    sgpr_count: int,
    lds_size: int,
    architecture: str,
    workgroup_size: Optional[int] = None,
) -> OccupancyResult:
    """Compute theoretical wave occupancy.

    Args:
        vgpr_count: VGPRs used per thread
        sgpr_count: SGPRs used per workgroup
        lds_size: LDS bytes per workgroup
        architecture: Target architecture (e.g., "gfx90a")
        workgroup_size: Workgroup size (threads), optional

    Returns:
        OccupancyResult with occupancy details

    Example:
        >>> result = compute_occupancy(
        ...     vgpr_count=128,
        ...     sgpr_count=64,
        ...     lds_size=16384,
        ...     architecture="gfx90a"
        ... )
        >>> print(f"Occupancy: {result.occupancy_pct:.1f}% ({result.limiting_factor})")
    """
    specs = get_target_specs(architecture)

    # Compute max waves from each resource
    vgpr_waves = _max_waves_from_vgpr(vgpr_count, specs)
    sgpr_waves = _max_waves_from_sgpr(sgpr_count, specs)
    lds_waves = _max_waves_from_lds(lds_size, specs, workgroup_size)

    # Determine limiting factor
    waves_per_cu = min(vgpr_waves, sgpr_waves, lds_waves, specs.max_waves_per_cu)

    if waves_per_cu == specs.max_waves_per_cu:
        limiting_factor = "max"
    elif waves_per_cu == vgpr_waves:
        limiting_factor = "vgpr"
    elif waves_per_cu == sgpr_waves:
        limiting_factor = "sgpr"
    else:
        limiting_factor = "lds"

    occupancy_pct = (waves_per_cu / specs.max_waves_per_cu) * 100

    return OccupancyResult(
        waves_per_cu=waves_per_cu,
        limiting_factor=limiting_factor,
        vgpr_waves=vgpr_waves,
        sgpr_waves=sgpr_waves,
        lds_waves=lds_waves,
        occupancy_pct=occupancy_pct,
    )


def _max_waves_from_vgpr(vgpr_count: int, specs: TargetSpecs) -> int:
    """Compute max waves from VGPR usage.

    VGPRs are allocated in blocks (granularity). The formula is:
    max_waves = total_vgprs / (ceil(vgpr_count / granularity) * granularity)
    """
    if vgpr_count <= 0:
        return specs.max_waves_per_cu

    granularity = specs.vgpr_granularity
    total_vgprs = specs.vgprs_per_cu

    # Round up to allocation granularity
    allocated = ((vgpr_count + granularity - 1) // granularity) * granularity

    if allocated == 0:
        return specs.max_waves_per_cu

    return min(total_vgprs // allocated, specs.max_waves_per_cu)


def _max_waves_from_sgpr(sgpr_count: int, specs: TargetSpecs) -> int:
    """Compute max waves from SGPR usage."""
    if sgpr_count <= 0:
        return specs.max_waves_per_cu

    granularity = specs.sgpr_granularity
    total_sgprs = specs.sgprs_per_cu

    # Round up to allocation granularity
    allocated = ((sgpr_count + granularity - 1) // granularity) * granularity

    if allocated == 0:
        return specs.max_waves_per_cu

    return min(total_sgprs // allocated, specs.max_waves_per_cu)


def _max_waves_from_lds(
    lds_size: int,
    specs: TargetSpecs,
    workgroup_size: Optional[int] = None,
) -> int:
    """Compute max waves from LDS usage.

    LDS is shared per workgroup. The calculation depends on:
    - Total LDS per CU
    - LDS per workgroup
    - Number of waves per workgroup
    """
    if lds_size <= 0:
        return specs.max_waves_per_cu

    total_lds = specs.lds_per_cu

    # Simple calculation: max workgroups that fit
    max_workgroups = total_lds // lds_size

    # Assume 1 wave per workgroup if workgroup_size not specified
    # More accurate would be ceil(workgroup_size / wavefront_size)
    waves_per_workgroup = 1
    if workgroup_size and workgroup_size > 0:
        waves_per_workgroup = (
            workgroup_size + specs.wavefront_size - 1
        ) // specs.wavefront_size

    return min(max_workgroups * waves_per_workgroup, specs.max_waves_per_cu)
