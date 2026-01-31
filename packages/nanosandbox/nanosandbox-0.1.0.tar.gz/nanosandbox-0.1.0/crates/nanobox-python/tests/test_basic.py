"""Basic tests for nanobox Python bindings."""

import pytest
import tempfile
import os
import sys
from nanobox import Sandbox, Permission, MB, GB, SeccompProfile


def is_linux():
    return sys.platform == "linux"


def is_macos():
    return sys.platform == "darwin"


def is_windows():
    return sys.platform == "win32"


class TestBasicExecution:
    """Cross-platform basic execution tests."""

    def test_echo(self):
        sandbox = Sandbox.builder().working_dir("/tmp" if not is_windows() else "C:\\Windows\\Temp").build()
        if is_windows():
            result = sandbox.run("cmd", ["/c", "echo", "hello", "world"])
        else:
            result = sandbox.run("echo", ["hello", "world"])
        assert result.exit_code == 0
        assert "hello" in result.stdout

    def test_exit_code(self):
        sandbox = Sandbox.builder().working_dir("/tmp" if not is_windows() else "C:\\Windows\\Temp").build()
        if is_windows():
            result = sandbox.run("cmd", ["/c", "exit", "42"])
        else:
            result = sandbox.run("sh", ["-c", "exit 42"])
        assert result.exit_code == 42

    def test_stderr(self):
        sandbox = Sandbox.builder().working_dir("/tmp" if not is_windows() else "C:\\Windows\\Temp").build()
        if is_windows():
            result = sandbox.run("cmd", ["/c", "echo error 1>&2"])
        else:
            result = sandbox.run("sh", ["-c", "echo error >&2"])
        assert "error" in result.stderr

    def test_success_method(self):
        sandbox = Sandbox.builder().working_dir("/tmp" if not is_windows() else "C:\\Windows\\Temp").build()
        if is_windows():
            result = sandbox.run("cmd", ["/c", "echo ok"])
            assert result.success()
            result = sandbox.run("cmd", ["/c", "exit 1"])
            assert not result.success()
        else:
            result = sandbox.run("true", [])
            assert result.success()
            result = sandbox.run("false", [])
            assert not result.success()


class TestResourceLimits:
    """Resource limits tests."""

    def test_timeout(self):
        """Timeout test - all platforms supported."""
        sandbox = (Sandbox.builder()
            .working_dir("/tmp" if not is_windows() else "C:\\Windows\\Temp")
            .wall_time_limit(1.0)
            .build())

        if is_windows():
            result = sandbox.run("timeout", ["/t", "10"])
        else:
            result = sandbox.run("sleep", ["10"])
        assert result.killed_by_timeout


class TestEnvironment:
    """Environment variable tests."""

    def test_env_vars(self):
        sandbox = (Sandbox.builder()
            .working_dir("/tmp" if not is_windows() else "C:\\Windows\\Temp")
            .env("MY_VAR", "my_value")
            .build())

        if is_windows():
            result = sandbox.run("cmd", ["/c", "echo %MY_VAR%"])
        else:
            result = sandbox.run("sh", ["-c", "echo $MY_VAR"])
        assert "my_value" in result.stdout


class TestPlatformInfo:
    """Platform info tests."""

    def test_platform_detection(self):
        platform = Sandbox.platform()
        assert platform in ["linux", "macos", "windows"]

        if is_linux():
            assert platform == "linux"
        elif is_macos():
            assert platform == "macos"
        elif is_windows():
            assert platform == "windows"

    def test_is_supported(self):
        assert Sandbox.is_supported()


class TestExecutionResult:
    """ExecutionResult tests."""

    def test_repr(self):
        sandbox = Sandbox.builder().working_dir("/tmp" if not is_windows() else "C:\\Windows\\Temp").build()
        if is_windows():
            result = sandbox.run("cmd", ["/c", "echo ok"])
        else:
            result = sandbox.run("echo", ["ok"])
        repr_str = repr(result)
        assert "ExecutionResult" in repr_str

    def test_failure_reason(self):
        sandbox = Sandbox.builder().working_dir("/tmp" if not is_windows() else "C:\\Windows\\Temp").build()
        if is_windows():
            result = sandbox.run("cmd", ["/c", "exit 42"])
        else:
            result = sandbox.run("sh", ["-c", "exit 42"])
        reason = result.failure_reason()
        assert reason is not None
        assert "42" in reason


class TestConstants:
    """Test size constants."""

    def test_size_constants(self):
        from nanobox import KB, MB, GB
        assert KB == 1024
        assert MB == 1024 * 1024
        assert GB == 1024 * 1024 * 1024
