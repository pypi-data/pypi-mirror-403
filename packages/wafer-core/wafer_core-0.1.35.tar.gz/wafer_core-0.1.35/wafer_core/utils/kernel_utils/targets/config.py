"""Target configuration for pluggable execution targets.

Tiger Style:
- Frozen dataclasses for immutable config
- Explicit over implicit
- No classes with methods (pure data)

Types of targets:
- BaremetalTarget: Physical GPU server (SSH access, NCU support)
- VMTarget: Virtual machine with GPU (SSH access, no NCU)
- ModalTarget: Serverless execution
- RunPodTarget: Auto-provisioned RunPod GPU (provisions -> SSH -> cleanup)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from wafer_core.utils.kernel_utils.deployment import DeploymentConfig


# TODO: Split BaremetalTarget into BaremetalTarget (persistent servers like Vultr,
# never auto-removed) and SSHTarget (ephemeral SSH endpoints from providers like
# RunPod/DO, safe to auto-clean when unreachable). Currently the pool bridge creates
# ephemeral pod endpoints as type="baremetal", losing provenance. SSHTarget should
# subclass BaremetalTarget so existing isinstance() checks still work. The `provider`
# field is a stopgap until this split happens.
@dataclass(frozen=True)
class BaremetalTarget:
    """Configuration for baremetal GPU server.

    Baremetal servers typically have:
    - Full privileged access (can run NCU profiling)
    - Consistent hardware (good for benchmarks)
    - SSH access via wafer_core.ssh

    Example (venv execution):
        target = BaremetalTarget(
            name="vultr-baremetal",
            ssh_target="chiraag@45.76.244.62:22",
            ssh_key="~/.ssh/id_ed25519",
            gpu_ids=[6, 7],  # Multiple GPUs for failover
            ncu_available=True,
        )

    Example (Docker execution - Modal-like):
        target = BaremetalTarget(
            name="vultr-docker",
            ssh_target="chiraag@45.76.244.62:22",
            ssh_key="~/.ssh/id_ed25519",
            gpu_ids=[6, 7],
            docker_image="nvcr.io/nvidia/cutlass:4.3-devel",
            pip_packages=["triton", "ninja", "nvidia-cutlass-dsl==4.3.0.dev0"],
            torch_package="torch>=2.8.0",
            torch_index_url="https://download.pytorch.org/whl/nightly/cu128",
        )
    """

    name: str
    ssh_target: str  # Format: user@host:port
    ssh_key: str  # Path to SSH private key
    gpu_ids: list[int]  # List of GPU IDs to try (in order)
    gpu_type: str = "B200"
    compute_capability: str = "10.0"
    ncu_available: bool = True  # Baremetal typically has NCU
    provider: str | None = (
        None  # Source provider ("runpod", "digitalocean") — enables auto-cleanup when instance is gone
    )

    # Docker execution config (Modal-like). If docker_image is set, run in container.
    docker_image: str | None = (
        None  # Docker image to use (e.g., "nvcr.io/nvidia/cutlass:4.3-devel")
    )
    pip_packages: tuple[str, ...] = ()  # Packages to install via uv pip install
    torch_package: str | None = None  # Torch package spec (e.g., "torch>=2.8.0")
    torch_index_url: str | None = None  # Custom index for torch (e.g., PyTorch nightly)

    def __post_init__(self) -> None:
        """Validate configuration."""
        assert len(self.gpu_ids) > 0, "Must specify at least one GPU ID"
        assert ":" in self.ssh_target, (
            f"ssh_target must include port (user@host:port), got: {self.ssh_target}"
        )
        # If torch_index_url is set, torch_package must also be set
        if self.torch_index_url:
            assert self.torch_package, "torch_package must be set when torch_index_url is provided"


@dataclass(frozen=True)
class VMTarget:
    """Configuration for VM with GPU.

    VMs typically have:
    - Limited privileged access (no NCU profiling)
    - Less consistent hardware than baremetal
    - SSH access via wafer_core.ssh
    - Good for cheap/fast correctness checks

    Example (venv execution):
        target = VMTarget(
            name="lambda-vm",
            ssh_target="ubuntu@150.136.217.70:22",
            ssh_key="~/.ssh/lambda-mac",
            gpu_ids=[7],
            ncu_available=False,
        )

    Example (Docker execution - Modal-like):
        target = VMTarget(
            name="lambda-docker",
            ssh_target="ubuntu@150.136.217.70:22",
            ssh_key="~/.ssh/lambda-mac",
            gpu_ids=[7],
            docker_image="nvcr.io/nvidia/pytorch:24.01-py3",
            pip_packages=["triton", "ninja"],
        )
    """

    name: str
    ssh_target: str  # Format: user@host:port
    ssh_key: str  # Path to SSH private key
    gpu_ids: list[int]  # List of GPU IDs to try (in order)
    gpu_type: str = "B200"
    compute_capability: str = "10.0"
    ncu_available: bool = False  # VMs typically don't have NCU

    # Docker execution config (Modal-like). If docker_image is set, run in container.
    docker_image: str | None = (
        None  # Docker image to use (e.g., "nvcr.io/nvidia/pytorch:24.01-py3")
    )
    pip_packages: tuple[str, ...] = ()  # Packages to install via uv pip install
    torch_package: str | None = None  # Torch package spec (e.g., "torch>=2.8.0")
    torch_index_url: str | None = None  # Custom index for torch (e.g., PyTorch nightly)

    def __post_init__(self) -> None:
        """Validate configuration."""
        assert len(self.gpu_ids) > 0, "Must specify at least one GPU ID"
        assert ":" in self.ssh_target, (
            f"ssh_target must include port (user@host:port), got: {self.ssh_target}"
        )
        # If torch_index_url is set, torch_package must also be set
        if self.torch_index_url:
            assert self.torch_package, "torch_package must be set when torch_index_url is provided"


@dataclass(frozen=True)
class ModalTarget:
    """Configuration for Modal serverless execution.

    Modal provides:
    - On-demand GPU instances (no persistent SSH)
    - Fast cold starts (~10-15 seconds)
    - Good for parallel execution
    - No NCU profiling support
    - Pay-per-use (availability determined by plan/credits)

    Example:
        target = ModalTarget(
            name="modal-b200",
            modal_app_name="kernel-eval-b200",
            gpu_type="B200",
            gpu_arch="blackwell",  # Fallback to any Blackwell
            timeout_seconds=600,
        )

    Example with explicit credentials:
        target = ModalTarget(
            name="modal-b200",
            modal_app_name="kernel-eval-b200",
            modal_token_id="ak-xxx",
            modal_token_secret="as-yyy",
            modal_workspace="my-team",
        )
    """

    name: str
    modal_app_name: str  # Modal app identifier (e.g., "kernel-eval-b200")

    # Modal account configuration (optional - uses env vars if not provided)
    modal_token_id: str | None = None  # Modal API token ID (or MODAL_TOKEN_ID env var)
    modal_token_secret: str | None = None  # Modal token secret (or MODAL_TOKEN_SECRET env var)
    modal_workspace: str | None = None  # Optional workspace name (or MODAL_WORKSPACE env var)

    # GPU requirements
    gpu_type: str = "B200"  # Preferred GPU type
    gpu_arch: str | None = None  # Fallback: any GPU in this arch (e.g., "blackwell")
    compute_capability: str = "10.0"

    # Modal-specific settings
    timeout_seconds: int = 600  # Max execution time
    cpu_count: int = 4  # CPUs for kernel compilation
    memory_gb: int = 16  # Memory for compilation/execution

    # Modal doesn't support NCU profiling (no privileged access)
    ncu_available: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        import os

        assert self.modal_app_name, "modal_app_name cannot be empty"
        assert self.timeout_seconds > 0, "timeout_seconds must be positive"
        assert self.cpu_count > 0, "cpu_count must be positive"
        assert self.memory_gb > 0, "memory_gb must be positive"

        # Fail fast: Check if Modal credentials are available
        # Priority order:
        # 1. Explicit credentials in config
        # 2. Environment variables
        # 3. Modal's default auth (~/.modal.toml or modal.token_flow)

        has_explicit = self.modal_token_id and self.modal_token_secret
        has_env = os.getenv("MODAL_TOKEN_ID") and os.getenv("MODAL_TOKEN_SECRET")

        # Check if Modal has default credentials configured (~/.modal.toml)
        # Don't import modal here to avoid trio/asyncio conflicts
        has_modal_auth = os.path.exists(os.path.expanduser("~/.modal.toml"))

        assert has_explicit or has_env or has_modal_auth, (
            f"ModalTarget '{self.name}' requires credentials. "
            "Either:\n"
            "  1. Run: modal token new (sets up default auth)\n"
            "  2. Set environment variables: MODAL_TOKEN_ID and MODAL_TOKEN_SECRET\n"
            "  3. Pass credentials explicitly: ModalTarget(modal_token_id='...', modal_token_secret='...')\n"
            "\n"
            "Get credentials from: https://modal.com/settings"
        )


@dataclass(frozen=True)
class WorkspaceTarget:
    """Configuration for wafer-api managed workspace.

    Workspaces provide:
    - API-managed GPU access (no SSH keys needed)
    - Persistent environment across execs
    - Automatic GPU scheduling
    - File sync via API

    Example:
        target = WorkspaceTarget(
            name="my-workspace",
            workspace_id="ws-abc123",  # From `wafer workspaces create`
        )

    The workspace must already exist. Create with:
        wafer workspaces create my-workspace --gpu-type B200
    """

    name: str
    workspace_id: str  # Workspace ID from wafer-api

    # Optional overrides (usually inherited from workspace)
    gpu_type: str = "B200"
    compute_capability: str = "10.0"
    timeout_seconds: int = 600

    # Workspaces don't support NCU (no privileged access)
    ncu_available: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        assert self.name, "name cannot be empty"
        assert self.workspace_id, "workspace_id cannot be empty"
        assert self.timeout_seconds > 0, "timeout_seconds must be positive"


# RunPod GPU type ID constant
AMD_MI300X_GPU_ID = "AMD Instinct MI300X OAM"


@dataclass(frozen=True)
class RunPodTarget:
    """Configuration for auto-provisioned RunPod GPU.

    RunPod provides on-demand GPU instances via their API. This target type
    automatically provisions a pod, runs evaluation via SSH, then cleans up.

    Lifecycle:
    1. Check state file for existing pod matching this target
    2. If exists and running (API check), reuse it
    3. If not, provision new pod and save to state file
    4. Run evaluation via SSH (same as VMTarget path)
    5. If keep_alive=False, terminate pod and remove from state file

    State is stored in ~/.wafer/runpod_state.json

    Example:
        target = RunPodTarget(
            name="runpod-mi300x",
            ssh_key="~/.ssh/id_ed25519",
        )

    Example with custom config:
        target = RunPodTarget(
            name="runpod-mi300x-custom",
            ssh_key="~/.ssh/id_ed25519",
            gpu_type_id="AMD Instinct MI300X OAM",
            gpu_count=1,
            image="rocm/pytorch:rocm7.0.2_ubuntu24.04_py3.12_pytorch_release_2.7.1",
            keep_alive=True,  # Don't terminate after eval
        )

    API key from WAFER_RUNPOD_API_KEY environment variable.
    """

    name: str
    ssh_key: str  # Path to SSH private key (must be registered with RunPod)

    # RunPod instance configuration
    gpu_type_id: str = AMD_MI300X_GPU_ID  # RunPod GPU type identifier
    gpu_count: int = 1
    container_disk_gb: int = 50
    # TODO: Consider creating a custom Docker image with HipKittens pre-installed
    # to avoid needing `wafer config targets install <target> hipkittens`.
    # HipKittens repo: https://github.com/HazyResearch/hipkittens
    # CK (Composable Kernel) is already included in ROCm 7.0.
    #
    # WARNING: PyTorch's hipify can corrupt /opt/rocm/include/thrust/ headers.
    # If you see "cuda/__cccl_config not found" errors, run:
    #   apt-get install --reinstall -y rocthrust
    # See docker/rocm7-runpod/README.md for details.
    image: str = "rocm/pytorch:rocm7.0.2_ubuntu24.04_py3.12_pytorch_release_2.7.1"
    template_id: str | None = None  # RunPod template ID for custom pod configuration

    # RunPod template ID — required for non-RunPod images that need custom
    # dockerArgs (e.g. to install and start sshd). When set, takes priority
    # over `image` in the deploy mutation.
    template_id: str | None = None

    # Timeouts
    provision_timeout: int = 900  # 15 min for SSH to be ready
    eval_timeout: int = 600  # 10 min for evaluation

    # Lifecycle
    keep_alive: bool = False  # If True, don't terminate pod after eval

    # GPU metadata (for wafer evaluate compatibility)
    gpu_type: str = "MI300X"  # Display name
    compute_capability: str = "9.4"  # gfx942 for MI300X
    gpu_ids: tuple[int, ...] = (0,)  # Default to GPU 0

    # RunPod doesn't support NCU (no privileged access)
    ncu_available: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        from wafer_core.auth import get_api_key

        assert self.name, "name cannot be empty"
        assert self.ssh_key, "ssh_key cannot be empty"
        assert self.gpu_count > 0, "gpu_count must be positive"
        assert self.provision_timeout > 0, "provision_timeout must be positive"
        assert self.eval_timeout > 0, "eval_timeout must be positive"

        # Check for API key (env var or ~/.wafer/auth.json)
        api_key = get_api_key("runpod")
        if not api_key:
            raise ValueError(
                "RunPod API key not found.\n"
                "Set WAFER_RUNPOD_API_KEY environment variable, or run:\n"
                "  wafer auth login runpod\n"
                "Get your API key from: https://runpod.io/console/user/settings"
            )


@dataclass(frozen=True)
class LocalTarget:
    """Configuration for local GPU (no SSH).

    Use this when running wafer on the same machine as the GPU.
    No SSH connection needed - commands run directly.

    Example:
        target = LocalTarget(
            name="local",
            gpu_ids=[0],
            gpu_type="RTX 5090",
        )

    The target is auto-configured by `wafer config targets init local`.
    """

    name: str
    gpu_ids: list[int]  # List of GPU IDs to use

    # GPU metadata
    gpu_type: str = "H100"  # Display name (e.g., "H100", "RTX 5090", "MI300X")
    compute_capability: str = "9.0"
    vendor: str = "nvidia"  # "nvidia" or "amd"
    driver_version: str = ""  # CUDA or ROCm version

    # PyTorch requirements (auto-detected)
    torch_package: str | None = None  # e.g., "torch==2.5.1+cu124"
    torch_index_url: str | None = None  # e.g., "https://download.pytorch.org/whl/cu124"

    # Local targets can have NCU if running with proper permissions
    ncu_available: bool = True

    def __post_init__(self) -> None:
        """Validate configuration."""
        assert self.name, "name cannot be empty"
        assert len(self.gpu_ids) > 0, "Must specify at least one GPU ID"
        assert self.vendor in ("nvidia", "amd"), (
            f"vendor must be 'nvidia' or 'amd', got: {self.vendor}"
        )


@dataclass(frozen=True)
class DigitalOceanTarget:
    """Configuration for auto-provisioned DigitalOcean AMD GPU.

    DigitalOcean AMD Developer Cloud provides MI300X GPUs. This target type
    automatically provisions a droplet, bootstraps Python/PyTorch, runs
    evaluation via SSH, then cleans up.

    Lifecycle:
    1. Check state file for existing droplet matching this target
    2. If exists and running (API check), reuse it
    3. If not, provision new droplet and save to state file
    4. Bootstrap Python environment with uv (installs PyTorch+ROCm)
    5. Run evaluation via SSH (same as VMTarget path)
    6. If keep_alive=False, terminate droplet and remove from state file

    State is stored in ~/.wafer/digitalocean_state.json

    Example:
        target = DigitalOceanTarget(
            name="do-mi300x",
            ssh_key="~/.ssh/id_ed25519",
        )

    Example with custom config:
        target = DigitalOceanTarget(
            name="do-mi300x-custom",
            ssh_key="~/.ssh/id_ed25519",
            region="atl1",
            size_slug="gpu-mi300x1-192gb-devcloud",
            keep_alive=True,  # Don't terminate after eval
        )

    API key from WAFER_AMD_DIGITALOCEAN_API_KEY environment variable.
    """

    name: str
    ssh_key: str  # Path to SSH private key (must be registered with DO)

    # DigitalOcean instance configuration
    region: str = "atl1"  # Atlanta (AMD GPUs available here)
    size_slug: str = "gpu-mi300x1-192gb-devcloud"  # Single MI300X GPU
    image: str = "amd-pytorchrocm7"  # PyTorch (ROCm7) marketplace image

    # Timeouts
    provision_timeout: int = 600  # 10 min for droplet to be ready
    eval_timeout: int = 600  # 10 min for evaluation

    # Lifecycle
    keep_alive: bool = False  # If True, don't terminate droplet after eval

    # GPU metadata (for wafer evaluate compatibility)
    gpu_type: str = "MI300X"  # Display name
    compute_capability: str = "9.4"  # gfx942 for MI300X
    gpu_ids: tuple[int, ...] = (0,)  # Default to GPU 0

    # DigitalOcean doesn't support NCU (no privileged access)
    ncu_available: bool = False

    def __post_init__(self) -> None:
        """Validate configuration."""
        from wafer_core.auth import get_api_key

        assert self.name, "name cannot be empty"
        assert self.ssh_key, "ssh_key cannot be empty"
        assert self.provision_timeout > 0, "provision_timeout must be positive"
        assert self.eval_timeout > 0, "eval_timeout must be positive"

        # Check for API key (env var or ~/.wafer/auth.json)
        api_key = get_api_key("digitalocean")
        if not api_key:
            raise ValueError(
                "DigitalOcean API key not found.\n"
                "Set WAFER_AMD_DIGITALOCEAN_API_KEY environment variable, or run:\n"
                "  wafer auth login digitalocean\n"
                "Get your API key from: https://cloud.digitalocean.com/account/api/tokens"
            )


# Union type for target configs
TargetConfig = (
    BaremetalTarget
    | VMTarget
    | ModalTarget
    | WorkspaceTarget
    | RunPodTarget
    | DigitalOceanTarget
    | LocalTarget
)


# Type guard functions for pattern matching
def is_baremetal_target(target: TargetConfig) -> bool:
    """Check if target is baremetal."""
    return isinstance(target, BaremetalTarget)


def is_vm_target(target: TargetConfig) -> bool:
    """Check if target is VM."""
    return isinstance(target, VMTarget)


def is_modal_target(target: TargetConfig) -> bool:
    """Check if target is Modal."""
    return isinstance(target, ModalTarget)


def is_workspace_target(target: TargetConfig) -> bool:
    """Check if target is workspace."""
    return isinstance(target, WorkspaceTarget)


def is_runpod_target(target: TargetConfig) -> bool:
    """Check if target is RunPod."""
    return isinstance(target, RunPodTarget)


def is_digitalocean_target(target: TargetConfig) -> bool:
    """Check if target is DigitalOcean."""
    return isinstance(target, DigitalOceanTarget)


def is_local_target(target: TargetConfig) -> bool:
    """Check if target is local (no SSH)."""
    return isinstance(target, LocalTarget)


def target_to_deployment_config(target: TargetConfig, gpu_id: int) -> DeploymentConfig:
    """Convert target to DeploymentConfig with specific GPU.

    Tiger Style: Pure function instead of method on frozen dataclass.

    Args:
        target: Target configuration (VM or Baremetal)
        gpu_id: Specific GPU ID to use (must be from target.gpu_ids)

    Returns:
        DeploymentConfig ready for setup_deployment()

    Example:
        >>> target = BaremetalTarget(
        ...     name="vultr",
        ...     ssh_target="user@host:22",
        ...     ssh_key="~/.ssh/key",
        ...     gpu_ids=[6, 7],
        ... )
        >>> config = target_to_deployment_config(target, gpu_id=7)
        >>> config.gpu_id
        7
    """
    from wafer_core.utils.kernel_utils.deployment import DeploymentConfig

    # Type narrowing: Only SSH-based targets supported (not Modal)
    assert not isinstance(target, ModalTarget), (
        f"target_to_deployment_config only supports SSH targets, got {type(target).__name__}"
    )

    return DeploymentConfig(
        ssh_target=target.ssh_target,
        ssh_key=target.ssh_key,
        gpu_id=gpu_id,
    )
