"""GPUMode simplified tool environment - single write_kernel tool.

Minimal tool interface for kernel optimization:
- One tool: write_kernel(filepath, code) - writes AND auto-submits
- Reference files injected into initial context
- Future-proof for beam search and agentic workflows

Tiger Style:
- Simplest thing that works
- Single responsibility (one tool)
- Composition over inheritance
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from wafer_core.rollouts.dtypes import (
    AgentState,
    Message,
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)
from wafer_core.utils.exceptions import RemoteDeploymentError
from wafer_core.utils.kernel_utils.deployment import DeploymentState
from wafer_core.tools import WRITE_KERNEL_TOOL, exec_write_kernel
from wafer_core.tools.write_kernel_tool import KernelSubmission, WriteKernelState
from wafer_core.utils.remote_execution import setup_remote_deployment

logger = logging.getLogger(__name__)


# ── Configuration ─────────────────────────────────────────────────────────────

BENCHMARK_NAME = "gpumode"
DEFAULT_GPU_ID = 0


@dataclass
class GPUModeSimpleEnvironment:
    """Simplified GPUMode environment with single write_kernel tool.

    NO INHERITANCE - uses composition with pure utility functions.

    Design:
    - Single tool: write_kernel(filepath, code) - auto-submits for testing
    - Reference files injected into initial prompt (no need to read)
    - Submission history stored in environment state
    - Future-proof for beam search (workspace persists across calls)

    Modes:
    - Legacy mode: Provide ssh_target, ssh_key, gpu_ids (single target deployment)
    - Targets mode: Provide available_targets (pluggable target routing)
      When using targets mode, ssh_target/ssh_key/gpu_ids are optional (not used)
    """

    sample_data: dict
    ssh_target: str | None = None
    ssh_key: str = "~/.ssh/id_ed25519"
    gpu_ids: list[int] = field(default_factory=lambda: [DEFAULT_GPU_ID])
    profile_on_success: bool = False
    ncu_on_success: bool = False
    artifacts_dir: Path | None = None
    available_targets: list | None = None
    workspace_dir: Path | None = field(default=None, repr=False, compare=False)
    _deployment_state: DeploymentState | None = field(default=None, repr=False, compare=False)
    _initialized: bool = False
    _deployment_state_cache: dict = field(default_factory=dict, repr=False, compare=False)
    submissions: list[KernelSubmission] = field(default_factory=list, repr=False)
    best_submission: KernelSubmission | None = field(default=None, repr=False)

    @property
    def gpu_id(self) -> int:
        """Get the first GPU ID for single-GPU operations."""
        return self.gpu_ids[0] if self.gpu_ids else DEFAULT_GPU_ID

    @property
    def problem_id(self) -> str:
        """Extract problem ID from sample_data."""
        return self.sample_data["problem_id"]

    @property
    def problem_description(self) -> str:
        """Extract problem description from sample_data."""
        return self.sample_data.get("problem_description", "")

    @property
    def test_suite(self) -> str:
        """Get test suite name from sample_data or use default."""
        return self.sample_data.get("test_suite", f"{BENCHMARK_NAME}_correctness")

    @property
    def benchmark_suite(self) -> str:
        """Get benchmark suite name."""
        return f"{BENCHMARK_NAME}_benchmark"

    @property
    def reference_backend(self) -> str:
        """Get reference backend name from sample_data or use default."""
        return self.sample_data.get("reference_backend", "reference")

    @property
    def language(self) -> str:
        """Extract language from sample_data, defaulting to 'pytorch'."""
        return self.sample_data.get("language", "pytorch")

    def __post_init__(self) -> None:
        """Validate configuration.

        In targets mode (available_targets provided), ssh_target is optional.
        In legacy mode (no available_targets), ssh_target is required.
        """
        assert self.sample_data, "sample_data cannot be empty"
        assert "problem_id" in self.sample_data, "sample_data must contain problem_id"

        # Validate mode: either use targets OR legacy SSH (not neither)
        if self.available_targets is None:
            # Legacy mode: require SSH configuration
            assert self.ssh_target, (
                "ssh_target required in legacy mode (or provide available_targets for targets mode)"
            )
            assert "@" in self.ssh_target, (
                f"ssh_target missing '@' (must be user@host:port): {self.ssh_target}"
            )
            assert ":" in self.ssh_target, (
                f"ssh_target missing ':' (must be user@host:port): {self.ssh_target}"
            )
        else:
            # Targets mode: ssh_target optional (targets contain their own SSH config)
            assert len(self.available_targets) > 0, (
                "available_targets cannot be empty (or provide ssh_target for legacy mode)"
            )

    def get_tools(self) -> list[Tool]:
        """Return tools available to agent.

        Simplified environment provides only write_kernel.
        """
        return [WRITE_KERNEL_TOOL]

    async def on_assistant_message(self, message: Message, state: AgentState) -> AgentState:
        """Hook called when assistant sends a message (no-op for this environment)."""
        return state

    async def serialize(self) -> dict:
        """Serialize environment state for checkpointing."""
        from dataclasses import asdict

        from wafer_core.utils.environment_serialization import serialize_environment_checkpoint

        # Serialize available_targets to JSON-safe dicts
        serialized_targets = None
        if self.available_targets is not None:
            serialized_targets = [asdict(target) for target in self.available_targets]

        return serialize_environment_checkpoint(
            sample_data=self.sample_data,
            ssh_target=self.ssh_target,  # Can be None for Modal-only
            ssh_key=self.ssh_key,
            gpu_ids=self.gpu_ids,
            deployment_state=self._deployment_state,
            workspace_dir=str(self.workspace_dir) if self.workspace_dir else None,
            additional_data={
                "_initialized": self._initialized,
                "artifacts_dir": str(self.artifacts_dir) if self.artifacts_dir else None,
                "profile_on_success": self.profile_on_success,
                "ncu_on_success": self.ncu_on_success,
                # Serialize available_targets as JSON-safe dicts
                "available_targets": serialized_targets,
                # Serialize submission tracking (required for serialize/deserialize cycle in agent loop)
                "submissions": [asdict(s) for s in self.submissions],
                "best_submission": asdict(self.best_submission) if self.best_submission else None,
            },
        )

    async def exec_tool(
        self,
        tool_call: ToolCall,
        current_state: AgentState,
        run_config: Any,
        checkpoint_store: Any = None,
        cancel_scope: Any = None,
    ) -> ToolResult:
        """Execute a tool call."""
        # Setup workspace on first tool use
        if not self._initialized:
            await self.setup_remote_environment()

        # Route to write_kernel handler
        if tool_call.name == "write_kernel":
            return await self._write_kernel(
                tool_call.args["filepath"], tool_call.args["code"], current_state
            )
        else:
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=f"Unknown tool: {tool_call.name}",
            )

    def requires_confirmation(self, tool_call: ToolCall) -> bool:
        """Whether this tool requires user confirmation."""
        return False

    async def setup_remote_environment(self) -> None:
        """Setup remote environment (one-time deployment).

        Uses pure function from wafer_core.utils.remote_execution.
        """
        if self._initialized:
            logger.debug("   Remote environment already initialized, skipping setup")
            return

        # Log processing info (only once, on first setup)
        logger.info(f"processing sample: {BENCHMARK_NAME} problem {self.problem_id}")

        # Create local workspace directory (per-sample isolation)
        import tempfile

        workspace_root = Path(tempfile.mkdtemp(prefix="kernel_workspace_"))
        self.workspace_dir = workspace_root

        assert self.workspace_dir is not None
        assert self.workspace_dir.exists()

        logger.debug(f"created local workspace: {self.workspace_dir}")

        # Write reference files to workspace (for workspace persistence)
        reference_code = self.sample_data.get("reference_code")
        if reference_code:
            (self.workspace_dir / "reference_kernel.py").write_text(reference_code)
            logger.debug("wrote reference_kernel.py to workspace")

        task_py = self.sample_data.get("task_py")
        if task_py:
            (self.workspace_dir / "task.py").write_text(task_py)
            logger.debug("wrote task.py to workspace")

        # ONLY setup SSH deployment if using legacy mode (no available_targets)
        if self.available_targets is None:
            # Type assertion: In legacy mode, ssh_target must be set (validated in __post_init__)
            assert self.ssh_target is not None, "ssh_target required in legacy mode"
            logger.debug(f"ssh: {self.ssh_target}, gpu: {self.gpu_id}")

            # Use pure function for remote deployment
            state, err = await setup_remote_deployment(
                ssh_target=self.ssh_target,
                ssh_key=self.ssh_key,
                gpu_id=self.gpu_id,
                benchmark_name=BENCHMARK_NAME,
            )

            if err:
                raise RemoteDeploymentError(err)

            self._deployment_state = state
        else:
            # Targets mode: deployment happens lazily per-target in run_operation_on_target()
            logger.debug(f"using pluggable targets: {[t.name for t in self.available_targets]}")

        self._initialized = True

    async def _write_kernel(
        self, filepath: str, code: str, current_state: AgentState
    ) -> ToolResult:
        """Write kernel file to workspace and automatically submit for testing.

        This is the single tool that combines write + submit.
        Thin wrapper that extracts state, calls pure function, and updates environment.
        """
        # workspace_dir must be set during setup_remote_environment (programmer error if None)
        assert self.workspace_dir is not None, (
            "workspace_dir not initialized - call setup_remote_environment first"
        )

        # Create tool call from parameters
        tool_call = ToolCall(
            id="",  # Will be set by caller
            name="write_kernel",
            args={"filepath": filepath, "code": code},
        )

        # Extract current state into WriteKernelState
        write_state = WriteKernelState(
            workspace_dir=self.workspace_dir,
            submissions=tuple(self.submissions),  # Convert to tuple for immutability
            best_submission=self.best_submission,
            deployment_state=self._deployment_state,
            deployment_state_cache=self._deployment_state_cache.copy(),
            language=self.language,
            problem_id=self.problem_id,
            sample_data=self.sample_data,
            test_suite=self.test_suite,
            reference_backend=self.reference_backend,
            benchmark_suite=self.benchmark_suite,
            profile_on_success=self.profile_on_success,
            ncu_on_success=self.ncu_on_success,
            artifacts_dir=self.artifacts_dir,
            available_targets=self.available_targets,
        )

        # Call pure function
        output = await exec_write_kernel(tool_call, write_state)

        # Update environment state from pure function output
        self.submissions = list(output.updated_submissions)
        self.best_submission = output.updated_best
        if output.updated_deployment_state is not None:
            self._deployment_state = output.updated_deployment_state
        self._deployment_state_cache = output.updated_deployment_state_cache

        # Return tool result
        return output.tool_result

    async def on_tool_call(self, tool_name: str, tool_args: dict, state: AgentState) -> ToolResult:
        """Handle tool calls from agent (deprecated - use exec_tool instead)."""
        # For backwards compatibility with older rollouts versions
        from wafer_core.rollouts.dtypes import ToolCall

        tool_call = ToolCall(id="", name=tool_name, args=tool_args)

        return await self.exec_tool(tool_call, state, None, None)

    @staticmethod
    async def deserialize(data: dict) -> "GPUModeSimpleEnvironment":
        """Deserialize environment from checkpoint.

        Uses pure function from wafer_core.utils.environment_serialization.
        """
        from wafer_core.utils.environment_serialization import deserialize_environment_checkpoint
        from wafer_core.utils.kernel_utils.targets import BaremetalTarget, ModalTarget, VMTarget

        checkpoint = deserialize_environment_checkpoint(data)

        # Reconstruct available_targets from serialized dicts
        available_targets = None
        if checkpoint.get("available_targets") is not None:
            available_targets = []
            for target_dict in checkpoint["available_targets"]:
                # Determine target type by checking for unique fields
                if "modal_app_name" in target_dict:
                    available_targets.append(ModalTarget(**target_dict))
                elif "ncu_available" in target_dict and target_dict["ncu_available"]:
                    # Baremetal typically has NCU support
                    available_targets.append(BaremetalTarget(**target_dict))
                else:
                    # VM or baremetal without NCU
                    available_targets.append(VMTarget(**target_dict))

        env = GPUModeSimpleEnvironment(
            sample_data=checkpoint["sample_data"],
            ssh_target=checkpoint["ssh_target"],
            ssh_key=checkpoint.get("ssh_key", "~/.ssh/id_ed25519"),
            gpu_ids=checkpoint.get("gpu_ids", [checkpoint.get("gpu_id", DEFAULT_GPU_ID)]),
            profile_on_success=checkpoint.get("profile_on_success", False),
            ncu_on_success=checkpoint.get("ncu_on_success", False),
            artifacts_dir=Path(checkpoint["artifacts_dir"])
            if checkpoint.get("artifacts_dir")
            else None,
            # Restore available_targets with reconstructed objects
            available_targets=available_targets,
        )

        # Restore workspace_dir and initialization state
        if checkpoint.get("workspace_dir"):
            env.workspace_dir = Path(checkpoint["workspace_dir"])
        env._initialized = checkpoint.get("_initialized", False)

        # Restore deployment state if it exists (deserialization helper reconstructs it)
        if checkpoint.get("deployment_state"):
            env._deployment_state = checkpoint["deployment_state"]

        # Restore submission tracking
        # KernelSubmission imported from tools.write_kernel_tool
        if checkpoint.get("submissions"):
            env.submissions = [KernelSubmission(**s) for s in checkpoint["submissions"]]
        if checkpoint.get("best_submission"):
            env.best_submission = KernelSubmission(**checkpoint["best_submission"])

        return env


async def create_environment(sample_data: dict, config: Any) -> GPUModeSimpleEnvironment:
    """Factory function to create environment for a sample.

    This is called by the evaluation framework for each sample in the dataset.

    Args:
        sample_data: Dataset sample with problem description, test suite, etc.
        config: Evaluation config with SSH target and other settings

    Returns:
        Fresh GPUModeSimpleEnvironment instance
    """
    # Extract gpu_ids from config
    if hasattr(config, "environment_config"):
        gpu_ids = config.environment_config.get("gpu_ids", [config.gpu_id])
    else:
        gpu_ids = [config.gpu_id]

    # Extract available_targets from config (Phase 4)
    available_targets = None
    if hasattr(config, "environment") and hasattr(config.environment, "available_targets"):
        available_targets = config.environment.available_targets

    return GPUModeSimpleEnvironment(
        sample_data=sample_data,
        ssh_target=config.ssh_target,
        gpu_ids=gpu_ids,
        artifacts_dir=getattr(config, "artifacts_dir", None),
        available_targets=available_targets,
    )
