import os
from functools import lru_cache
from pathlib import Path
import sys


# Container detection file paths
_CONTAINER_ENV_FILES = [
    "/.dockerenv",  # Docker classic, some Podman
    "/.containerenv",  # Podman
    "/run/.containerenv",  # Podman alternative location
]

# Cgroup file paths to check
_CGROUP_FILES = ["/proc/self/cgroup", "/proc/1/cgroup"]

# Keywords to search for in cgroup files
_CGROUP_KEYWORDS = (
    "docker",
    "kubepods",
    "kubelet",
    "containerd",
    "podman",
    "libpod",
    "cri-o",
    "lxc",
    "garden",
)

# Keywords to search for in mountinfo
_MOUNTINFO_KEYWORDS = ("docker", "kubelet", "containerd", "podman")

# Environment variables that indicate container execution
_CONTAINER_ENV_VARS = (
    "KUBERNETES_SERVICE_HOST",  # Kubernetes
    "KUBERNETES_PORT",  # Kubernetes
    "container",  # systemd-based containers
    "DOCKER_CONTAINER",  # Sometimes set
    "PODMAN_CONTAINER",  # Podman
    "ECS_CONTAINER_METADATA_URI",  # AWS ECS
)


def _check_container_files() -> bool:
    """Check for container-specific environment files."""
    return any(Path(f).exists() for f in _CONTAINER_ENV_FILES)


def _check_cgroup_files() -> bool:
    """Check cgroup files for container indicators."""
    for cgroup_file in _CGROUP_FILES:
        try:
            with open(cgroup_file, "rt") as f:
                content = f.read().lower()
                if any(keyword in content for keyword in _CGROUP_KEYWORDS):
                    return True
        except (FileNotFoundError, PermissionError, OSError):
            continue
    return False


def _check_mountinfo() -> bool:
    """Check mountinfo for container filesystem patterns."""
    try:
        with open("/proc/self/mountinfo", "rt") as f:
            content = f.read()
            if any(keyword in content for keyword in _MOUNTINFO_KEYWORDS):
                return True
    except (FileNotFoundError, PermissionError, OSError):
        pass
    return False


def _check_environment_variables() -> bool:
    """Check environment variables for container indicators."""
    return any(var in os.environ for var in _CONTAINER_ENV_VARS)


@lru_cache(maxsize=1)
def _is_inside_container_cached() -> bool:
    """
    Internal cached implementation of container detection.
    
    Returns:
        True if running inside a container, False otherwise.
    """
    if not sys.platform.startswith("linux"):
        return False

    # Check detection methods in order
    if _check_container_files():
        return True

    if _check_cgroup_files():
        return True

    if _check_mountinfo():
        return True

    if _check_environment_variables():
        return True

    return False


def is_inside_container(force_refresh: bool = False) -> bool:
    """
    Return True if the current process is running inside a container.
    
    Detects multiple container types including Docker, Podman, Kubernetes,
    containerd, LXC, and others.
    
    Linux-only detection. Returns False on macOS and Windows.
    
    Args:
        force_refresh: If True, bypass the cache and perform a fresh check.
                       Defaults to False.
    
    Returns:
        True if running inside a container, False otherwise.
    
    Examples:
        >>> is_inside_container()  # Uses cache
        False
        >>> is_inside_container(force_refresh=True)  # Bypasses cache
        False
    """
    if force_refresh:
        _is_inside_container_cached.cache_clear()
    return _is_inside_container_cached()
