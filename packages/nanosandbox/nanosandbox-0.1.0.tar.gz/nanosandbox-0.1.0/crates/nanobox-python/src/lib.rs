//! Python bindings for nanosandbox
//!
//! Provides cross-platform sandbox functionality for Python.

use pyo3::prelude::*;
use pyo3::exceptions::{PyRuntimeError, PyValueError};
use std::time::Duration;

/// Mount permission
#[pyclass(eq, eq_int)]
#[derive(Clone, PartialEq)]
pub enum Permission {
    #[pyo3(name = "READ_ONLY")]
    ReadOnly,
    #[pyo3(name = "READ_WRITE")]
    ReadWrite,
}

impl From<Permission> for nanosandbox::Permission {
    fn from(p: Permission) -> Self {
        match p {
            Permission::ReadOnly => nanosandbox::Permission::ReadOnly,
            Permission::ReadWrite => nanosandbox::Permission::ReadWrite,
        }
    }
}

/// Security profile (cross-platform)
/// - Linux: Maps to Seccomp-BPF
/// - macOS: Maps to SBPL rules
/// - Windows: Maps to Restricted Token
#[pyclass(eq, eq_int)]
#[derive(Clone, PartialEq)]
pub enum SeccompProfile {
    #[pyo3(name = "STRICT")]
    Strict,
    #[pyo3(name = "STANDARD")]
    Standard,
    #[pyo3(name = "PERMISSIVE")]
    Permissive,
    #[pyo3(name = "DISABLED")]
    Disabled,
}

impl From<SeccompProfile> for nanosandbox::SeccompProfile {
    fn from(p: SeccompProfile) -> Self {
        match p {
            SeccompProfile::Strict => nanosandbox::SeccompProfile::Strict,
            SeccompProfile::Standard => nanosandbox::SeccompProfile::Standard,
            SeccompProfile::Permissive => nanosandbox::SeccompProfile::Permissive,
            SeccompProfile::Disabled => nanosandbox::SeccompProfile::Disabled,
        }
    }
}

/// Sandbox Builder - use method chaining to configure, then call build()
#[pyclass]
pub struct SandboxBuilder {
    inner: Option<nanosandbox::SandboxBuilder>,
}

#[pymethods]
impl SandboxBuilder {
    #[new]
    fn new() -> Self {
        Self {
            inner: Some(nanosandbox::Sandbox::builder()),
        }
    }

    /// Mount a file or directory
    fn mount(&mut self, source: String, target: String, permission: Permission) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.mount(source, target, permission.into())),
        })
    }

    /// Mount tmpfs
    fn tmpfs(&mut self, path: String, size_bytes: u64) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.tmpfs(path, size_bytes)),
        })
    }

    /// Set working directory
    fn working_dir(&mut self, path: String) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.working_dir(path)),
        })
    }

    /// Memory limit in bytes
    fn memory_limit(&mut self, bytes: u64) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.memory_limit(bytes)),
        })
    }

    /// CPU limit
    fn cpu_limit(&mut self, cpus: f64) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.cpu_limit(cpus)),
        })
    }

    /// Wall clock time limit in seconds
    fn wall_time_limit(&mut self, seconds: f64) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.wall_time_limit(Duration::from_secs_f64(seconds))),
        })
    }

    /// Maximum number of processes
    fn max_pids(&mut self, n: u32) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.max_pids(n)),
        })
    }

    /// Disable network access
    fn no_network(&mut self) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.no_network()),
        })
    }

    /// Allow network access only to specified domains
    fn allow_network(&mut self, domains: Vec<String>) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        let refs: Vec<&str> = domains.iter().map(|s| s.as_str()).collect();
        Ok(Self {
            inner: Some(inner.allow_network(&refs)),
        })
    }

    /// Set security profile
    fn seccomp_profile(&mut self, profile: SeccompProfile) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.seccomp_profile(profile.into())),
        })
    }

    /// Set environment variable
    fn env(&mut self, key: String, value: String) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.env(key, value)),
        })
    }

    /// Set hostname
    fn hostname(&mut self, name: String) -> PyResult<Self> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;
        Ok(Self {
            inner: Some(inner.hostname(name)),
        })
    }

    /// Build the Sandbox
    fn build(&mut self) -> PyResult<Sandbox> {
        let inner = self.inner.take()
            .ok_or_else(|| PyValueError::new_err("Builder already consumed"))?;

        let sandbox = inner.build()
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;

        Ok(Sandbox { inner: sandbox })
    }
}

/// Sandbox
#[pyclass]
pub struct Sandbox {
    inner: nanosandbox::Sandbox,
}

#[pymethods]
impl Sandbox {
    /// Get a new Builder
    #[staticmethod]
    fn builder() -> SandboxBuilder {
        SandboxBuilder::new()
    }

    /// Data analysis preset
    #[staticmethod]
    fn data_analysis(input_dir: String, output_dir: String) -> SandboxBuilder {
        SandboxBuilder {
            inner: Some(nanosandbox::Sandbox::data_analysis(input_dir, output_dir)),
        }
    }

    /// Code judge preset
    #[staticmethod]
    fn code_judge(code_dir: String) -> SandboxBuilder {
        SandboxBuilder {
            inner: Some(nanosandbox::Sandbox::code_judge(code_dir)),
        }
    }

    /// Agent executor preset
    #[staticmethod]
    fn agent_executor(workspace: String) -> SandboxBuilder {
        SandboxBuilder {
            inner: Some(nanosandbox::Sandbox::agent_executor(workspace)),
        }
    }

    /// Interactive preset
    #[staticmethod]
    fn interactive(workspace: String) -> SandboxBuilder {
        SandboxBuilder {
            inner: Some(nanosandbox::Sandbox::interactive(workspace)),
        }
    }

    /// Run a command
    fn run(&self, cmd: String, args: Vec<String>) -> PyResult<ExecutionResult> {
        let args_ref: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
        let result = self.inner.run(&cmd, &args_ref)
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
        Ok(result.into())
    }

    /// Run a command with stdin input
    fn run_with_input(&self, cmd: String, args: Vec<String>, stdin: Vec<u8>) -> PyResult<ExecutionResult> {
        let args_ref: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
        let result = self.inner.run_with_input(&cmd, &args_ref, Some(&stdin))
            .map_err(|e| PyRuntimeError::new_err(e.to_string()))?;
        Ok(result.into())
    }

    /// Get sandbox ID
    fn id(&self) -> String {
        self.inner.id().to_string()
    }

    /// Get current platform
    #[staticmethod]
    fn platform() -> String {
        #[cfg(target_os = "linux")]
        return "linux".to_string();
        #[cfg(target_os = "macos")]
        return "macos".to_string();
        #[cfg(target_os = "windows")]
        return "windows".to_string();
        #[cfg(not(any(target_os = "linux", target_os = "macos", target_os = "windows")))]
        return "unknown".to_string();
    }

    /// Check if platform is supported
    #[staticmethod]
    fn is_supported() -> bool {
        nanosandbox::is_platform_supported()
    }
}

/// Execution result
#[pyclass]
#[derive(Clone)]
pub struct ExecutionResult {
    #[pyo3(get)]
    pub stdout: String,
    #[pyo3(get)]
    pub stderr: String,
    #[pyo3(get)]
    pub exit_code: i32,
    #[pyo3(get)]
    pub wall_time_seconds: f64,
    #[pyo3(get)]
    pub cpu_time_seconds: Option<f64>,
    #[pyo3(get)]
    pub peak_memory_bytes: Option<u64>,
    #[pyo3(get)]
    pub killed_by_timeout: bool,
    #[pyo3(get)]
    pub killed_by_oom: bool,
    #[pyo3(get)]
    pub signal: Option<i32>,
}

#[pymethods]
impl ExecutionResult {
    /// Check if execution was successful
    fn success(&self) -> bool {
        self.exit_code == 0
            && !self.killed_by_timeout
            && !self.killed_by_oom
            && self.signal.is_none()
    }

    /// Get failure reason if any
    fn failure_reason(&self) -> Option<String> {
        if self.killed_by_timeout {
            Some("Execution timed out".into())
        } else if self.killed_by_oom {
            Some("Out of memory".into())
        } else if self.signal.is_some() {
            Some(format!("Killed by signal {}", self.signal.unwrap()))
        } else if self.exit_code != 0 {
            Some(format!("Exit code {}", self.exit_code))
        } else {
            None
        }
    }

    fn __repr__(&self) -> String {
        if self.success() {
            format!("ExecutionResult(success, {:.2}s)", self.wall_time_seconds)
        } else {
            format!("ExecutionResult(failed: {})", self.failure_reason().unwrap_or_default())
        }
    }
}

impl From<nanosandbox::ExecutionResult> for ExecutionResult {
    fn from(r: nanosandbox::ExecutionResult) -> Self {
        Self {
            stdout: r.stdout,
            stderr: r.stderr,
            exit_code: r.exit_code,
            wall_time_seconds: r.duration.as_secs_f64(),
            cpu_time_seconds: r.cpu_time.map(|d| d.as_secs_f64()),
            peak_memory_bytes: r.peak_memory,
            killed_by_timeout: r.killed_by_timeout,
            killed_by_oom: r.killed_by_oom,
            signal: r.signal,
        }
    }
}

/// Python module
#[pymodule]
fn _nanosandbox(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Permission>()?;
    m.add_class::<SeccompProfile>()?;
    m.add_class::<SandboxBuilder>()?;
    m.add_class::<Sandbox>()?;
    m.add_class::<ExecutionResult>()?;

    // Constants
    m.add("KB", 1024u64)?;
    m.add("MB", 1024u64 * 1024)?;
    m.add("GB", 1024u64 * 1024 * 1024)?;

    Ok(())
}
