"""Architecture detection from kernel patterns.

Detects model architecture type (Transformer, SSM, Hybrid) from kernel names
to enable architecture-specific layer segmentation.
"""

from enum import Enum
from typing import Literal


class ArchitectureType(Enum):
    """Model architecture types."""

    TRANSFORMER = "transformer"
    SSM = "ssm"
    HYBRID = "hybrid"
    UNKNOWN = "unknown"


def detect_architecture(kernel_names: list[str]) -> tuple[ArchitectureType, list[str]]:
    """Detect model architecture from kernel patterns.
    
    Args:
        kernel_names: List of all kernel names from trace
        
    Returns:
        Tuple of (architecture_type, detected_markers)
        detected_markers: List of kernel names that indicate the architecture
    """
    kernel_names_lower = [name.lower() for name in kernel_names]
    
    attention_patterns = [
        "fmha",
        "attention",
        "flash",
        "sdpa",
    ]
    
    ssm_patterns = [
        "selective_scan",
        "mamba",
        "ssd",
        "causal_conv",
    ]
    
    has_attention = any(
        any(pattern in name for pattern in attention_patterns)
        for name in kernel_names_lower
    )
    
    has_ssm = any(
        any(pattern in name for pattern in ssm_patterns)
        for name in kernel_names_lower
    )
    
    markers: list[str] = []
    if has_attention:
        attention_markers = [
            name for name in kernel_names
            if any(pattern in name.lower() for pattern in attention_patterns)
        ]
        markers.extend(attention_markers[:5])
    
    if has_ssm:
        ssm_markers = [
            name for name in kernel_names
            if any(pattern in name.lower() for pattern in ssm_patterns)
        ]
        markers.extend(ssm_markers[:5])
    if has_attention and not has_ssm:
        return ArchitectureType.TRANSFORMER, markers
    elif has_ssm and not has_attention:
        return ArchitectureType.SSM, markers
    elif has_attention and has_ssm:
        return ArchitectureType.HYBRID, markers
    else:
        return ArchitectureType.UNKNOWN, []
