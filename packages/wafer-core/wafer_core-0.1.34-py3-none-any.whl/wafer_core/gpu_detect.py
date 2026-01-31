"""GPU detection and torch version selection.

Detects GPU vendor (NVIDIA/AMD) and driver version, then selects
compatible PyTorch packages.

Usage:
    # Local detection
    gpu_info = detect_local_gpu()

    # Remote detection via SSH
    gpu_info = await detect_remote_gpu(ssh_client)

    # Get torch requirements for detected GPU
    torch_reqs = get_torch_requirements(gpu_info)
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wafer_core.async_ssh import AsyncSSHClient


@dataclass(frozen=True)
class GPUInfo:
    """Detected GPU information."""

    vendor: str  # "nvidia" or "amd"
    gpu_name: str  # e.g., "NVIDIA H100", "AMD Instinct MI300X"
    driver_version: str  # CUDA version for NVIDIA, ROCm version for AMD
    gpu_count: int = 1


@dataclass(frozen=True)
class TorchRequirements:
    """PyTorch installation requirements for a GPU."""

    packages: tuple[str, ...]  # e.g., ("torch==2.5.1+cu124", "torchvision==0.20.1+cu124")
    index_url: str  # e.g., "https://download.pytorch.org/whl/cu124"


# CUDA version -> PyTorch requirements
# Maps CUDA driver version to compatible torch wheels
CUDA_TORCH_VERSIONS: dict[str, TorchRequirements] = {
    "12.1": TorchRequirements(
        packages=(
            "torch==2.3.1+cu121",
            "torchvision==0.18.1+cu121",
            "torchaudio==2.3.1+cu121",
        ),
        index_url="https://download.pytorch.org/whl/cu121",
    ),
    "12.4": TorchRequirements(
        packages=(
            "torch==2.5.1+cu124",
            "torchvision==0.20.1+cu124",
            "torchaudio==2.5.1+cu124",
        ),
        index_url="https://download.pytorch.org/whl/cu124",
    ),
    "12.6": TorchRequirements(
        packages=(
            "torch==2.5.1+cu124",  # cu124 works with 12.6
            "torchvision==0.20.1+cu124",
            "torchaudio==2.5.1+cu124",
        ),
        index_url="https://download.pytorch.org/whl/cu124",
    ),
    "12.8": TorchRequirements(
        packages=(
            "torch>=2.6.0",  # Nightly for newer CUDA
            "torchvision",
            "torchaudio",
        ),
        index_url="https://download.pytorch.org/whl/nightly/cu128",
    ),
}

# ROCm version -> PyTorch requirements
ROCM_TORCH_VERSIONS: dict[str, TorchRequirements] = {
    "6.1": TorchRequirements(
        packages=(
            "torch==2.4.0+rocm6.1",
            "torchvision==0.19.0+rocm6.1",
            "torchaudio==2.4.0+rocm6.1",
        ),
        index_url="https://download.pytorch.org/whl/rocm6.1",
    ),
    "6.2": TorchRequirements(
        packages=(
            "torch==2.5.1+rocm6.2",
            "torchvision==0.20.1+rocm6.2",
            "torchaudio==2.5.1+rocm6.2",
        ),
        index_url="https://download.pytorch.org/whl/rocm6.2",
    ),
    "6.4": TorchRequirements(
        packages=(
            "torch==2.8.0+rocm6.4",
            "torchvision==0.21.0+rocm6.4",
            "torchaudio==2.8.0+rocm6.4",
        ),
        index_url="https://download.pytorch.org/whl/rocm6.4",
    ),
}

# Default fallbacks
DEFAULT_CUDA_VERSION = "12.4"
DEFAULT_ROCM_VERSION = "6.4"


def _parse_nvidia_smi(output: str) -> GPUInfo | None:
    """Parse nvidia-smi output to extract GPU info.

    Expected format from: nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
    Example: "NVIDIA H100 80GB HBM3, 550.54.15"
    """
    lines = [line.strip() for line in output.strip().split("\n") if line.strip()]
    if not lines:
        return None

    # Parse first GPU line
    first_line = lines[0]
    if "," not in first_line:
        return None

    parts = first_line.split(",")
    if len(parts) < 2:
        return None

    gpu_name = parts[0].strip()
    driver_version = parts[1].strip()

    # Extract CUDA version from driver version
    # Driver 550.x supports CUDA 12.4, 535.x supports CUDA 12.2, etc.
    # We'll use nvidia-smi's reported CUDA version instead
    cuda_version = _get_cuda_version_from_driver(driver_version)

    return GPUInfo(
        vendor="nvidia",
        gpu_name=gpu_name,
        driver_version=cuda_version,
        gpu_count=len(lines),
    )


def _get_cuda_version_from_driver(driver_version: str) -> str:
    """Map NVIDIA driver version to CUDA version.

    This is approximate - nvidia-smi --query also reports CUDA version directly.
    """
    try:
        major = int(driver_version.split(".")[0])
    except (ValueError, IndexError):
        return DEFAULT_CUDA_VERSION

    # Driver version -> CUDA version mapping (approximate)
    if major >= 560:
        return "12.8"
    elif major >= 550:
        return "12.4"
    elif major >= 535:
        return "12.2"
    elif major >= 525:
        return "12.1"
    else:
        return "12.1"


def _parse_nvidia_smi_cuda_version(output: str) -> str | None:
    """Parse CUDA version from nvidia-smi output.

    Looks for "CUDA Version: X.Y" in the output.
    """
    match = re.search(r"CUDA Version:\s*(\d+\.\d+)", output)
    if match:
        return match.group(1)
    return None


def _parse_rocm_smi(output: str) -> GPUInfo | None:
    """Parse rocm-smi output to extract GPU info.

    Expected format from: rocm-smi --showproductname
    """
    lines = [line.strip() for line in output.strip().split("\n") if line.strip()]

    gpu_name = None
    gpu_count = 0

    for line in lines:
        # Look for GPU product name lines
        if "GPU" in line and ":" in line:
            gpu_count += 1
            # Extract name after colon
            parts = line.split(":", 1)
            if len(parts) > 1:
                gpu_name = parts[1].strip()

    if not gpu_name:
        # Fallback: look for any MI300 mention
        for line in lines:
            if "MI300" in line:
                gpu_name = "AMD Instinct MI300X"
                gpu_count = max(gpu_count, 1)
                break

    if not gpu_name:
        return None

    return GPUInfo(
        vendor="amd",
        gpu_name=gpu_name,
        driver_version="unknown",  # Will be filled by rocm version check
        gpu_count=max(gpu_count, 1),
    )


def _parse_rocm_version(output: str) -> str | None:
    """Parse ROCm version from /opt/rocm/.info/version or rocm-smi.

    Looks for version strings like "6.4.0" or "6.4.3".
    """
    # Try to find version pattern
    match = re.search(r"(\d+\.\d+)(?:\.\d+)?", output)
    if match:
        return match.group(1)  # Return major.minor only
    return None


def detect_local_gpu() -> GPUInfo | None:
    """Detect GPU on local machine.

    Tries nvidia-smi first (NVIDIA), then rocm-smi (AMD).

    Returns:
        GPUInfo if GPU detected, None otherwise
    """
    # Try NVIDIA first
    try:
        # Get GPU name and driver version
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            gpu_info = _parse_nvidia_smi(result.stdout)
            if gpu_info:
                # Also get CUDA version directly
                cuda_result = subprocess.run(
                    ["nvidia-smi"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if cuda_result.returncode == 0:
                    cuda_ver = _parse_nvidia_smi_cuda_version(cuda_result.stdout)
                    if cuda_ver:
                        return GPUInfo(
                            vendor=gpu_info.vendor,
                            gpu_name=gpu_info.gpu_name,
                            driver_version=cuda_ver,
                            gpu_count=gpu_info.gpu_count,
                        )
                return gpu_info
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try AMD
    try:
        result = subprocess.run(
            ["rocm-smi", "--showproductname"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            gpu_info = _parse_rocm_smi(result.stdout)
            if gpu_info:
                # Get ROCm version
                try:
                    ver_result = subprocess.run(
                        ["cat", "/opt/rocm/.info/version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if ver_result.returncode == 0:
                        rocm_ver = _parse_rocm_version(ver_result.stdout)
                        if rocm_ver:
                            return GPUInfo(
                                vendor=gpu_info.vendor,
                                gpu_name=gpu_info.gpu_name,
                                driver_version=rocm_ver,
                                gpu_count=gpu_info.gpu_count,
                            )
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    pass
                return gpu_info
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return None


async def detect_remote_gpu(client: AsyncSSHClient) -> GPUInfo | None:
    """Detect GPU on remote machine via SSH.

    Args:
        client: Connected AsyncSSHClient

    Returns:
        GPUInfo if GPU detected, None otherwise
    """
    # Try NVIDIA first
    result = await client.exec(
        "nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null"
    )
    if result.exit_code == 0 and result.stdout.strip():
        gpu_info = _parse_nvidia_smi(result.stdout)
        if gpu_info:
            # Get CUDA version
            cuda_result = await client.exec("nvidia-smi 2>/dev/null")
            if cuda_result.exit_code == 0:
                cuda_ver = _parse_nvidia_smi_cuda_version(cuda_result.stdout)
                if cuda_ver:
                    return GPUInfo(
                        vendor=gpu_info.vendor,
                        gpu_name=gpu_info.gpu_name,
                        driver_version=cuda_ver,
                        gpu_count=gpu_info.gpu_count,
                    )
            return gpu_info

    # Try AMD
    result = await client.exec("rocm-smi --showproductname 2>/dev/null")
    if result.exit_code == 0 and result.stdout.strip():
        gpu_info = _parse_rocm_smi(result.stdout)
        if gpu_info:
            # Get ROCm version
            ver_result = await client.exec("cat /opt/rocm/.info/version 2>/dev/null")
            if ver_result.exit_code == 0:
                rocm_ver = _parse_rocm_version(ver_result.stdout)
                if rocm_ver:
                    return GPUInfo(
                        vendor=gpu_info.vendor,
                        gpu_name=gpu_info.gpu_name,
                        driver_version=rocm_ver,
                        gpu_count=gpu_info.gpu_count,
                    )
            return gpu_info

    return None


def get_torch_requirements(gpu_info: GPUInfo) -> TorchRequirements:
    """Get PyTorch requirements for detected GPU.

    Args:
        gpu_info: Detected GPU information

    Returns:
        TorchRequirements with packages and index URL
    """
    if gpu_info.vendor == "nvidia":
        # Find best matching CUDA version
        cuda_ver = gpu_info.driver_version
        if cuda_ver in CUDA_TORCH_VERSIONS:
            return CUDA_TORCH_VERSIONS[cuda_ver]

        # Try major.minor match
        major_minor = ".".join(cuda_ver.split(".")[:2])
        if major_minor in CUDA_TORCH_VERSIONS:
            return CUDA_TORCH_VERSIONS[major_minor]

        # Fallback to default
        return CUDA_TORCH_VERSIONS[DEFAULT_CUDA_VERSION]

    elif gpu_info.vendor == "amd":
        # Find best matching ROCm version
        rocm_ver = gpu_info.driver_version
        if rocm_ver in ROCM_TORCH_VERSIONS:
            return ROCM_TORCH_VERSIONS[rocm_ver]

        # Try major.minor match
        major_minor = ".".join(rocm_ver.split(".")[:2])
        if major_minor in ROCM_TORCH_VERSIONS:
            return ROCM_TORCH_VERSIONS[major_minor]

        # Fallback to default
        return ROCM_TORCH_VERSIONS[DEFAULT_ROCM_VERSION]

    # Unknown vendor - use CUDA default
    return CUDA_TORCH_VERSIONS[DEFAULT_CUDA_VERSION]


def get_compute_capability(gpu_info: GPUInfo) -> str:
    """Get compute capability string for GPU.

    Args:
        gpu_info: Detected GPU information

    Returns:
        Compute capability string (e.g., "9.0" for H100, "10.0" for B200)
    """
    gpu_name_lower = gpu_info.gpu_name.lower()

    # NVIDIA GPUs
    if "b200" in gpu_name_lower or "b100" in gpu_name_lower:
        return "10.0"  # Blackwell
    elif "h100" in gpu_name_lower or "h200" in gpu_name_lower:
        return "9.0"  # Hopper
    elif "a100" in gpu_name_lower:
        return "8.0"  # Ampere
    elif "4090" in gpu_name_lower or "4080" in gpu_name_lower:
        return "8.9"  # Ada Lovelace
    elif "5090" in gpu_name_lower or "5080" in gpu_name_lower:
        return "10.0"  # Blackwell consumer
    elif "3090" in gpu_name_lower or "3080" in gpu_name_lower:
        return "8.6"  # Ampere consumer
    elif "v100" in gpu_name_lower:
        return "7.0"  # Volta

    # AMD GPUs
    elif "mi300" in gpu_name_lower:
        return "9.4"  # gfx942
    elif "mi250" in gpu_name_lower:
        return "9.0"  # gfx90a
    elif "mi100" in gpu_name_lower:
        return "9.0"  # gfx908

    # Default
    return "8.0"
