"""SSH probe: detect software labels on a live target.

Runs a Python script on the target via SSH that reports installed
software versions. Returns a flat dict[str, str] of labels.

Only called at provision time or manually via `wafer targets probe`.
Results are cached in target_state.json — probe is never implicit.

Uses subprocess ssh (not asyncssh) to match existing codebase patterns.
"""

from __future__ import annotations

import json
import logging
import subprocess

logger = logging.getLogger(__name__)

# Probe script runs on the target machine via SSH.
# Prints a JSON dict to stdout. Must work with stock Python 3.10+.
_PROBE_SCRIPT = r"""
import json, shutil, subprocess, sys

def probe():
    result = {}

    # Python version
    result["python_version"] = ".".join(map(str, sys.version_info[:2]))

    # ROCm version from filesystem
    try:
        with open("/opt/rocm/.info/version") as f:
            result["rocm_version"] = f.read().strip().split("-")[0]
    except Exception:
        pass

    # CUDA version from nvcc
    nvcc = shutil.which("nvcc")
    if nvcc:
        try:
            out = subprocess.check_output([nvcc, "--version"], text=True)
            for line in out.split("\n"):
                if "release" in line.lower():
                    parts = line.split("release")
                    if len(parts) > 1:
                        result["cuda_version"] = parts[1].split(",")[0].strip()
                    break
        except Exception:
            pass

    # PyTorch version
    try:
        import torch
        result["pytorch_version"] = torch.__version__.split("+")[0]
    except ImportError:
        pass

    # Triton version
    try:
        import triton
        result["triton_version"] = triton.__version__
    except ImportError:
        pass

    print(json.dumps(result))

probe()
"""


def probe_target_labels(
    host: str,
    port: int,
    username: str,
    ssh_key_path: str | None = None,
    timeout: int = 60,
) -> dict[str, str]:
    """SSH into a target and probe installed software. Returns labels dict.

    Raises on SSH failure — caller decides how to handle.
    """
    ssh_args = [
        "ssh",
        "-p", str(port),
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        "-o", "ConnectTimeout=10",
    ]
    if ssh_key_path:
        ssh_args.extend(["-i", ssh_key_path])

    ssh_args.append(f"{username}@{host}")
    ssh_args.append("python3")

    result = subprocess.run(
        ssh_args,
        input=_PROBE_SCRIPT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"Probe failed (exit {result.returncode}): {stderr}")

    stdout = result.stdout.strip()
    labels = json.loads(stdout)
    assert isinstance(labels, dict), f"Probe returned {type(labels).__name__}, expected dict"

    return {str(k): str(v) for k, v in labels.items()}
