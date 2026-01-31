"""Linux Landlock sandbox implementation.

Uses Landlock LSM for filesystem restrictions.
Requires Linux kernel 5.13+ with CONFIG_SECURITY_LANDLOCK=y.

Implementation based on OpenAI Codex CLI (MIT License):
https://github.com/openai/codex/blob/main/codex-rs/linux-sandbox/src/landlock.rs
"""

import ctypes
import ctypes.util
import os
import subprocess
from pathlib import Path

import trio

from wafer_core.sandbox.executor import SandboxError, SandboxResult, SandboxUnavailableError
from wafer_core.sandbox.policy import SandboxPolicy

# ── Landlock Constants ───────────────────────────────────────────────────────
# From linux/landlock.h

LANDLOCK_CREATE_RULESET_VERSION = 1 << 0

# Access rights for files (ABI v1+)
LANDLOCK_ACCESS_FS_EXECUTE = 1 << 0
LANDLOCK_ACCESS_FS_WRITE_FILE = 1 << 1
LANDLOCK_ACCESS_FS_READ_FILE = 1 << 2
LANDLOCK_ACCESS_FS_READ_DIR = 1 << 3
LANDLOCK_ACCESS_FS_REMOVE_DIR = 1 << 4
LANDLOCK_ACCESS_FS_REMOVE_FILE = 1 << 5
LANDLOCK_ACCESS_FS_MAKE_CHAR = 1 << 6
LANDLOCK_ACCESS_FS_MAKE_DIR = 1 << 7
LANDLOCK_ACCESS_FS_MAKE_REG = 1 << 8
LANDLOCK_ACCESS_FS_MAKE_SOCK = 1 << 9
LANDLOCK_ACCESS_FS_MAKE_FIFO = 1 << 10
LANDLOCK_ACCESS_FS_MAKE_BLOCK = 1 << 11
LANDLOCK_ACCESS_FS_MAKE_SYM = 1 << 12

# Additional access rights (ABI v2+)
LANDLOCK_ACCESS_FS_REFER = 1 << 13

# Additional access rights (ABI v3+)
LANDLOCK_ACCESS_FS_TRUNCATE = 1 << 14

# All read access rights
LANDLOCK_ACCESS_FS_READ = (
    LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR
)

# All write access rights (v1)
LANDLOCK_ACCESS_FS_WRITE = (
    LANDLOCK_ACCESS_FS_WRITE_FILE
    | LANDLOCK_ACCESS_FS_REMOVE_DIR
    | LANDLOCK_ACCESS_FS_REMOVE_FILE
    | LANDLOCK_ACCESS_FS_MAKE_CHAR
    | LANDLOCK_ACCESS_FS_MAKE_DIR
    | LANDLOCK_ACCESS_FS_MAKE_REG
    | LANDLOCK_ACCESS_FS_MAKE_SOCK
    | LANDLOCK_ACCESS_FS_MAKE_FIFO
    | LANDLOCK_ACCESS_FS_MAKE_BLOCK
    | LANDLOCK_ACCESS_FS_MAKE_SYM
)

# Syscall numbers (x86_64)
SYS_landlock_create_ruleset = 444
SYS_landlock_add_rule = 445
SYS_landlock_restrict_self = 446

# Landlock rule types
LANDLOCK_RULE_PATH_BENEATH = 1

# prctl constants
PR_SET_NO_NEW_PRIVS = 38


# ── Landlock Structures ──────────────────────────────────────────────────────


class LandlockRulesetAttr(ctypes.Structure):
    _fields_ = [
        ("handled_access_fs", ctypes.c_uint64),
    ]


class LandlockPathBeneathAttr(ctypes.Structure):
    _fields_ = [
        ("allowed_access", ctypes.c_uint64),
        ("parent_fd", ctypes.c_int32),
    ]


# ── Seccomp Constants ────────────────────────────────────────────────────────
# Network syscalls to block

# Socket syscalls
SYS_socket = 41
SYS_connect = 42
SYS_accept = 43
SYS_sendto = 44
SYS_sendmsg = 46
SYS_sendmmsg = 307
SYS_recvmmsg = 299
SYS_bind = 49
SYS_listen = 50
SYS_getsockname = 51
SYS_getpeername = 52
SYS_socketpair = 53
SYS_setsockopt = 54
SYS_getsockopt = 55
SYS_shutdown = 48
SYS_accept4 = 288

# AF_UNIX constant
AF_UNIX = 1


# ── Helper Functions ─────────────────────────────────────────────────────────

_libc = None


def _get_libc() -> ctypes.CDLL:
    """Get libc for syscall access."""
    global _libc
    if _libc is None:
        libc_name = ctypes.util.find_library("c")
        if not libc_name:
            raise SandboxError("Could not find libc")
        _libc = ctypes.CDLL(libc_name, use_errno=True)
    return _libc


def _syscall(number: int, *args: ctypes.c_void_p) -> int:
    """Make a raw syscall."""
    libc = _get_libc()
    return libc.syscall(number, *args)


def _check_landlock_available() -> bool:
    """Check if Landlock is available on this system."""
    # Check if the Landlock ABI is available
    try:
        ruleset_attr = LandlockRulesetAttr()
        ruleset_attr.handled_access_fs = 0

        result = _syscall(
            SYS_landlock_create_ruleset,
            None,
            0,
            LANDLOCK_CREATE_RULESET_VERSION,
        )

        if result < 0:
            # ENOSYS means Landlock not compiled in kernel
            # EOPNOTSUPP means Landlock disabled at boot
            return False

        # Close the test ruleset
        os.close(result)
        return True

    except Exception:
        return False


def _set_no_new_privs() -> None:
    """Set PR_SET_NO_NEW_PRIVS to prevent privilege escalation."""
    libc = _get_libc()
    result = libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)
    if result != 0:
        errno = ctypes.get_errno()
        raise SandboxError(f"prctl(PR_SET_NO_NEW_PRIVS) failed: errno {errno}")


def _create_landlock_ruleset(handled_access: int) -> int:
    """Create a Landlock ruleset and return its file descriptor."""
    ruleset_attr = LandlockRulesetAttr()
    ruleset_attr.handled_access_fs = handled_access

    fd = _syscall(
        SYS_landlock_create_ruleset,
        ctypes.byref(ruleset_attr),
        ctypes.sizeof(ruleset_attr),
        0,
    )

    if fd < 0:
        errno = ctypes.get_errno()
        raise SandboxError(f"landlock_create_ruleset failed: errno {errno}")

    return fd


def _add_landlock_rule(ruleset_fd: int, path: Path, access: int) -> None:
    """Add a path rule to the Landlock ruleset."""
    # Open the path to get a file descriptor
    try:
        path_fd = os.open(str(path), os.O_PATH | os.O_CLOEXEC)
    except OSError as e:
        raise SandboxError(f"Failed to open path {path}: {e}") from e

    try:
        path_attr = LandlockPathBeneathAttr()
        path_attr.allowed_access = access
        path_attr.parent_fd = path_fd

        result = _syscall(
            SYS_landlock_add_rule,
            ruleset_fd,
            LANDLOCK_RULE_PATH_BENEATH,
            ctypes.byref(path_attr),
            0,
        )

        if result < 0:
            errno = ctypes.get_errno()
            raise SandboxError(f"landlock_add_rule failed for {path}: errno {errno}")

    finally:
        os.close(path_fd)


def _enforce_landlock_ruleset(ruleset_fd: int) -> None:
    """Enforce the Landlock ruleset on the current process."""
    result = _syscall(SYS_landlock_restrict_self, ruleset_fd, 0)

    if result < 0:
        errno = ctypes.get_errno()
        raise SandboxError(f"landlock_restrict_self failed: errno {errno}")


def apply_landlock_policy(policy: SandboxPolicy) -> None:
    """Apply Landlock filesystem restrictions.

    - Read access to entire filesystem
    - Write access only to specified writable_roots
    - Always allow /dev/null writes
    """
    if not _check_landlock_available():
        raise SandboxUnavailableError(
            "Landlock not available. Requires Linux 5.13+ with CONFIG_SECURITY_LANDLOCK=y"
        )

    # Prevent privilege escalation
    _set_no_new_privs()

    # Create ruleset handling all filesystem access
    all_access = LANDLOCK_ACCESS_FS_READ | LANDLOCK_ACCESS_FS_WRITE
    ruleset_fd = _create_landlock_ruleset(all_access)

    try:
        # Allow read access to root (entire filesystem)
        _add_landlock_rule(ruleset_fd, Path("/"), LANDLOCK_ACCESS_FS_READ)

        # Allow read+write to /dev/null
        _add_landlock_rule(
            ruleset_fd,
            Path("/dev/null"),
            LANDLOCK_ACCESS_FS_READ | LANDLOCK_ACCESS_FS_WRITE_FILE,
        )

        # Allow read+write to writable roots
        # TODO(sandbox): Landlock doesn't support excluding subdirectories from
        # a writable parent. SandboxPolicy.read_only_paths marks .git and .codex
        # as read-only, but we can't enforce that here. Options:
        # 1. Use seccomp to filter open() calls to these paths
        # 2. Move .git/.codex outside the writable root before sandbox
        # 3. Accept that agents can write to .git (current behavior)
        for root in policy.get_all_writable_roots():
            if root.exists():
                _add_landlock_rule(
                    ruleset_fd,
                    root,
                    LANDLOCK_ACCESS_FS_READ | LANDLOCK_ACCESS_FS_WRITE,
                )

        # Allow /tmp for temporary files
        tmp = Path("/tmp")
        if tmp.exists():
            _add_landlock_rule(
                ruleset_fd,
                tmp,
                LANDLOCK_ACCESS_FS_READ | LANDLOCK_ACCESS_FS_WRITE,
            )

        # Enforce the ruleset
        _enforce_landlock_ruleset(ruleset_fd)

    finally:
        os.close(ruleset_fd)


# ── Seccomp Network Blocking ─────────────────────────────────────────────────
#
# TODO(sandbox): Implement seccomp-bpf network isolation.
#
# Reference: https://github.com/openai/codex/blob/main/codex-rs/linux-sandbox/src/landlock.rs
# (see install_network_seccomp_filter_on_current_thread function)
#
# The Codex implementation blocks these syscalls except for AF_UNIX:
# - connect, accept, accept4, bind, listen
# - sendto, sendmsg, sendmmsg, recvmmsg
# - getsockname, getpeername, shutdown
# - getsockopt, setsockopt, ptrace
# - socket/socketpair (only AF_UNIX allowed)
#
# Implementation options:
# 1. Use the `seccomp` Python package (pip install seccomp)
# 2. Build BPF bytecode manually with ctypes
# 3. Create a small Rust binary like Codex does
#
# For now, we rely on Landlock filesystem restrictions as the primary
# security boundary. Network access via loopback is still possible but
# external network access is limited by the application architecture
# (wafer evaluate uses SSH to remote targets).


def apply_network_restrictions(policy: SandboxPolicy) -> None:
    """Apply network restrictions (placeholder for full seccomp implementation).

    WARNING: Network blocking is not currently enforced on Linux.
    The sandbox relies on Landlock filesystem restrictions as the primary
    security boundary. Full network isolation requires seccomp-bpf filtering.
    """
    if policy.network_access:
        return  # Network allowed, nothing to do

    # TODO(sandbox): Implement seccomp-bpf filtering for network syscalls.
    # See comment block above for implementation details.
    #
    # For now, log a warning that network restrictions are not enforced.
    # This is a known limitation until seccomp-bpf support is added.
    import logging

    logger = logging.getLogger(__name__)
    logger.warning(
        "Network blocking requested but not enforced on Linux. "
        "Sandbox relies on filesystem restrictions only. "
        "See TODO(sandbox) for seccomp-bpf implementation."
    )


# ── Main Execution Function ──────────────────────────────────────────────────


async def execute_with_landlock(
    command: str,
    policy: SandboxPolicy,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> SandboxResult:
    """Execute a command under Linux Landlock sandbox.

    The sandbox is applied in a forked child process, so the parent
    process remains unrestricted.

    Args:
        command: Shell command to execute.
        policy: Sandbox policy defining restrictions.
        timeout: Command timeout in seconds.
        env: Optional additional environment variables.

    Returns:
        SandboxResult with execution results.

    Raises:
        SandboxError: If sandbox setup fails.
    """
    if not _check_landlock_available():
        raise SandboxUnavailableError(
            "Landlock not available. Requires Linux 5.13+ with CONFIG_SECURITY_LANDLOCK=y"
        )

    # Build environment
    exec_env = os.environ.copy()
    exec_env["WAFER_SANDBOX"] = "landlock"
    if not policy.network_access:
        exec_env["WAFER_SANDBOX_NETWORK_DISABLED"] = "1"
    if env:
        exec_env.update(env)

    # We need to fork and apply Landlock in the child before exec.
    # Using subprocess with a wrapper script that applies the sandbox.
    #
    # For simplicity, we use a Python subprocess that applies Landlock
    # before executing the command. This is less efficient than a native
    # solution but works for the initial implementation.

    sandbox_script = f"""
import os
import sys
sys.path.insert(0, {repr(str(Path(__file__).parent.parent.parent))})

from wafer_core.sandbox.landlock import apply_landlock_policy, apply_network_restrictions
from wafer_core.sandbox.policy import SandboxPolicy
from pathlib import Path
import subprocess

# Reconstruct policy
policy = SandboxPolicy(
    working_dir=Path({repr(str(policy.working_dir))}),
    writable_roots={repr(tuple(str(p) for p in policy.writable_roots))},
    read_only_paths={repr(tuple(str(p) for p in policy.read_only_paths))},
    network_access={repr(policy.network_access)},
)
# Convert string tuples back to Path tuples
policy = SandboxPolicy(
    working_dir=policy.working_dir,
    writable_roots=tuple(Path(p) for p in policy.writable_roots),
    read_only_paths=tuple(Path(p) for p in policy.read_only_paths),
    network_access=policy.network_access,
)

# Apply sandbox
apply_landlock_policy(policy)
apply_network_restrictions(policy)

# Execute command
result = subprocess.run(
    ["sh", "-c", {repr(command)}],
    capture_output=True,
    text=True,
    cwd={repr(str(policy.working_dir))},
)

# Output in a parseable format
print("---STDOUT---")
print(result.stdout, end="")
print("---STDERR---")
print(result.stderr, end="")
print("---RETURNCODE---")
print(result.returncode)
"""

    def run_sandboxed() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "-c", sandbox_script],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(policy.working_dir),
            env=exec_env,
        )

    try:
        result = await trio.to_thread.run_sync(run_sandboxed)

        # Parse the output
        output = result.stdout
        stdout = ""
        stderr = ""
        returncode = result.returncode

        if "---STDOUT---" in output:
            parts = output.split("---STDOUT---", 1)[1]
            if "---STDERR---" in parts:
                stdout, rest = parts.split("---STDERR---", 1)
                if "---RETURNCODE---" in rest:
                    stderr, rc_str = rest.split("---RETURNCODE---", 1)
                    try:
                        returncode = int(rc_str.strip())
                    except ValueError:
                        pass

        # Check if sandbox denied
        sandbox_denied = returncode != 0 and (
            "Operation not permitted" in stderr or "Operation not permitted" in result.stderr
        )

        return SandboxResult(
            stdout=stdout,
            stderr=stderr or result.stderr,
            returncode=returncode,
            sandbox_denied=sandbox_denied,
        )

    except subprocess.TimeoutExpired:
        return SandboxResult(
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            returncode=-1,
            sandbox_denied=False,
        )
