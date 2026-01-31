"""
Nanosandbox - Lightweight cross-platform sandbox for secure code execution.

Supported platforms:
- Linux: Full isolation (namespaces + cgroups + seccomp)
- macOS: sandbox-exec based isolation
- Windows: Job Objects based isolation (limited)

Example:
    >>> from nanosandbox import Sandbox, Permission, MB
    >>> sandbox = (Sandbox.builder()
    ...     .mount("/data/input", "/input", Permission.READ_ONLY)
    ...     .memory_limit(512 * MB)
    ...     .build())
    >>> result = sandbox.run("python3", ["-c", "print('hello')"])
    >>> print(result.stdout)
    hello
"""

from ._nanosandbox import (
    Sandbox,
    SandboxBuilder,
    Permission,
    SeccompProfile,
    ExecutionResult,
    KB,
    MB,
    GB,
)

__version__ = "0.1.0"

__all__ = [
    "Sandbox",
    "SandboxBuilder",
    "Permission",
    "SeccompProfile",
    "ExecutionResult",
    "KB",
    "MB",
    "GB",
    "get_platform_capabilities",
]


def get_platform_capabilities():
    """Return capability description for current platform."""
    platform = Sandbox.platform()

    capabilities = {
        "linux": {
            "memory_limit": "hard (cgroups v2)",
            "cpu_limit": "supported (cgroups v2)",
            "max_pids": "supported (cgroups v2)",
            "network_isolation": "full (network namespace)",
            "filesystem_isolation": "full (mount namespace)",
            "security_profile": "seccomp-bpf",
        },
        "macos": {
            "memory_limit": "soft (setrlimit)",
            "cpu_limit": "not supported",
            "max_pids": "not supported",
            "network_isolation": "sbpl rules",
            "filesystem_isolation": "sbpl rules",
            "security_profile": "sbpl",
        },
        "windows": {
            "memory_limit": "hard (job object)",
            "cpu_limit": "supported (job object)",
            "max_pids": "supported (job object)",
            "network_isolation": "not supported",
            "filesystem_isolation": "not supported",
            "security_profile": "restricted token",
        },
    }

    return capabilities.get(platform, {})
