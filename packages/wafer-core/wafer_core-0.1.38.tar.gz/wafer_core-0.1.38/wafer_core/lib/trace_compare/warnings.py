"""Warning detection and reporting for trace analysis.

Detects issues with trace data quality and provides actionable suggestions.
"""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TraceWarning:
    """A warning about trace data quality or analysis limitations."""

    code: str  # e.g., "NO_PHASE_ANNOTATIONS", "NO_PYTHON_STACKS"
    severity: Literal["info", "warning", "error"]
    message: str
    suggestion: str


def detect_warnings(
    events: list[dict],
    kernel_names: list[str],
    phases: list[dict] | None = None,
    layers_detected: int = 0,
    total_kernels: int = 0,
) -> list[TraceWarning]:
    """Detect warnings from trace data.
    
    Args:
        events: All trace events
        kernel_names: List of all kernel names
        phases: Optional list of phase events (for checking phase annotations)
        layers_detected: Number of layers detected
        total_kernels: Total number of kernels
        
    Returns:
        List of warnings
    """
    warnings: list[TraceWarning] = []
    
    # Check for phase annotations
    has_phase_annotations = any(
        ev.get("cat") == "user_annotation" and ev.get("name", "").startswith("execute_context")
        for ev in events
    )
    
    if not has_phase_annotations:
        warnings.append(
            TraceWarning(
                code="NO_PHASE_ANNOTATIONS",
                severity="warning",
                message="No vLLM phase annotations found. Phase analysis (prefill/decode) will be unavailable.",
                suggestion="Ensure you're using vLLM v1.0+ with profiling enabled. Re-profile with torch.profiler.profile() to capture phase markers.",
            )
        )
    
    # Check for Python stack traces
    has_python_stacks = any(
        ev.get("cat") == "python_function"
        for ev in events
    )
    
    if not has_python_stacks:
        warnings.append(
            TraceWarning(
                code="NO_PYTHON_STACKS",
                severity="info",
                message="No Python stack traces available. CPU→kernel mapping will be limited.",
                suggestion="Re-profile with with_stack=True: torch.profiler.profile(with_stack=True) for better CPU operator identification.",
            )
        )
    
    # Check for high percentage of unknown kernels
    if total_kernels > 0:
        unknown_count = sum(1 for name in kernel_names if "unknown" in name.lower() or name == "Other")
        unknown_percentage = (unknown_count / total_kernels) * 100
        
        if unknown_percentage > 20:
            warnings.append(
                TraceWarning(
                    code="HIGH_UNKNOWN_KERNELS",
                    severity="warning",
                    message=f"{unknown_percentage:.1f}% of kernels are classified as 'Unknown'. Kernel registry may be outdated.",
                    suggestion="Update kernel pattern registry or report unrecognized kernel patterns for support.",
                )
            )
    
    # Check for layer detection failure
    if layers_detected == 0 and total_kernels > 100:
        warnings.append(
            TraceWarning(
                code="LAYER_DETECTION_FAILED",
                severity="warning",
                message="No transformer layers detected. Layer-wise analysis unavailable.",
                suggestion="This may indicate a non-transformer model (e.g., SSM/Mamba) or insufficient correlation data. Check model architecture.",
            )
        )
    
    return warnings
