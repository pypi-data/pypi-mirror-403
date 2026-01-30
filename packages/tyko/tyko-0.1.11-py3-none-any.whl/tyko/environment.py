"""Utilities for capturing environment information."""

import os
import platform
import subprocess
import sys
from pathlib import Path


def _detect_gpus_nvidia_smi() -> tuple[int, list[str]] | None:
    """Detect NVIDIA GPUs using nvidia-smi (no dependencies required)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            gpu_names = [name.strip() for name in result.stdout.strip().split("\n") if name.strip()]
            return len(gpu_names), gpu_names
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _detect_gpus_proc() -> tuple[int, list[str] | None] | None:
    """Detect NVIDIA GPUs via /proc filesystem (Linux only).

    Returns:
        None if no GPUs detected, otherwise (count, names) where names may be None
        if GPU count was detected but names could not be read.
    """
    nvidia_path = Path("/proc/driver/nvidia/gpus")
    if nvidia_path.exists():
        gpu_dirs = list(nvidia_path.iterdir())
        gpu_names: list[str] = []
        for gpu_dir in gpu_dirs:
            info_file = gpu_dir / "information"
            if info_file.exists():
                try:
                    content = info_file.read_text()
                    for line in content.split("\n"):
                        if line.startswith("Model:"):
                            gpu_names.append(line.split(":", 1)[1].strip())
                            break
                except OSError:
                    pass
        if gpu_dirs:
            return len(gpu_dirs), gpu_names if gpu_names else None
    return None


def _detect_gpus() -> dict[str, object]:
    """Detect GPUs without requiring ML frameworks."""
    # Try nvidia-smi first (works on Linux, Windows, macOS with NVIDIA drivers)
    nvidia_smi_result = _detect_gpus_nvidia_smi()
    if nvidia_smi_result:
        gpu_count, gpu_names = nvidia_smi_result
        return {"gpu_count": gpu_count, "gpu_names": gpu_names}

    # Fallback to /proc on Linux
    proc_result = _detect_gpus_proc()
    if proc_result:
        gpu_count, gpu_names_or_none = proc_result
        info: dict[str, object] = {"gpu_count": gpu_count}
        if gpu_names_or_none:
            info["gpu_names"] = gpu_names_or_none
        return info

    return {}


def _get_git_info() -> dict[str, object]:
    """Capture git repository information if in a git repo."""
    git_info: dict[str, object] = {}

    try:
        # Check if we're in a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return {}

        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            git_info["git_commit"] = result.stdout.strip()

        # Get branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            git_info["git_branch"] = result.stdout.strip()

        # Check for uncommitted changes (dirty state)
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            git_info["git_dirty"] = bool(result.stdout.strip())

        # Get remote URL (useful for identifying the repo)
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            git_info["git_remote"] = result.stdout.strip()

    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    return git_info


def capture_environment() -> dict[str, object]:
    """Capture current environment information.

    Returns a dictionary with:
    - python_version: Python version string
    - platform: Operating system platform
    - cpu_count: Number of CPU cores
    - ram_gb: Total RAM in GB (if available)
    - gpu_count: Number of GPUs (if detectable)
    - gpu_names: List of GPU names (if detectable)
    - git_commit: Current git commit hash (if in a repo)
    - git_branch: Current git branch name (if in a repo)
    - git_dirty: Whether there are uncommitted changes (if in a repo)
    - git_remote: Remote origin URL (if in a repo)
    - command: The command line used to invoke the script
    - executable: Path to the Python executable

    Returns:
        Dictionary containing environment information
    """
    env_info: dict[str, object] = {
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "executable": sys.executable,
        "command": sys.argv,
    }

    # Try to get RAM size
    try:
        import psutil  # type: ignore[import-untyped]

        env_info["ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
    except ImportError:
        pass

    # Detect GPUs without requiring ML frameworks
    env_info.update(_detect_gpus())

    # Capture git info
    env_info.update(_get_git_info())

    return env_info
