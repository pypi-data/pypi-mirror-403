"""Custom exception hierarchy for gpuci."""


class GPUCIError(Exception):
    """Base exception for gpuci."""

    pass


class ConfigError(GPUCIError):
    """Configuration file errors."""

    pass


class ProviderError(GPUCIError):
    """Provider connection/execution errors."""

    def __init__(self, provider_name: str, message: str):
        self.provider_name = provider_name
        super().__init__(f"[{provider_name}] {message}")


class CompilationError(GPUCIError):
    """Remote CUDA compilation failures."""

    def __init__(self, target_name: str, stderr: str):
        self.target_name = target_name
        self.stderr = stderr
        super().__init__(f"Compilation failed on {target_name}: {stderr[:500]}")


class ExecutionError(GPUCIError):
    """Remote kernel execution failures."""

    def __init__(self, target_name: str, message: str):
        self.target_name = target_name
        super().__init__(f"Execution failed on {target_name}: {message}")


class ConnectionError(GPUCIError):
    """SSH/provider connection failures."""

    def __init__(self, target_name: str, message: str):
        self.target_name = target_name
        super().__init__(f"Connection failed to {target_name}: {message}")


class TimeoutError(GPUCIError):
    """Operation timed out."""

    def __init__(self, target_name: str, timeout_seconds: int, operation: str = "operation"):
        self.target_name = target_name
        self.timeout_seconds = timeout_seconds
        super().__init__(f"{operation.capitalize()} timed out on {target_name} after {timeout_seconds}s")
