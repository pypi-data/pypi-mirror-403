"""
Converter Sandbox - Process Isolation for Converter Execution

Provides sandboxed execution of converters with:
- Process isolation (subprocess-based)
- Resource limits (CPU, memory, time)
- Filesystem restrictions
- Capability-based permissions

Architecture Decision:
- Uses subprocess (not multiprocessing) for stronger isolation
- Converters run in separate Python process with restricted permissions
- IPC via pipes (stdin/stdout) with JSON messages
- Clean process lifecycle management with proper cleanup

See ARCHITECTURE_REVIEW.md Stage 1.2 for design rationale.
"""

import ast
import asyncio
import json
import logging
import os
import platform
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable, TypeVar, Union

# Unix-only resource module (for process limits)
if platform.system() != "Windows":
    import resource as unix_resource
else:
    unix_resource = None  # type: ignore

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration & Types
# =============================================================================

class SandboxCapability(Enum):
    """Capabilities that can be granted to sandboxed converters."""
    
    # File system access
    READ_INPUT = "read_input"          # Read from input file only
    READ_DROP_FOLDER = "read_drop"     # Read from drop folder (for multi-file converters)
    WRITE_OUTPUT = "write_output"      # Write to designated output location
    WRITE_TEMP = "write_temp"          # Write to temp directory
    
    # Network access (dangerous - rarely needed)
    NETWORK_LOCAL = "network_local"    # Access localhost only
    NETWORK_WATS = "network_wats"      # Access WATS API only (via proxy)
    
    # Logging
    LOG_INFO = "log_info"              # Basic logging
    LOG_DEBUG = "log_debug"            # Debug logging (verbose)
    
    # System
    READ_ENV_SAFE = "read_env_safe"    # Read safe environment variables


# Default capabilities for converters (minimal permissions)
DEFAULT_CAPABILITIES: Set[SandboxCapability] = {
    SandboxCapability.READ_INPUT,
    SandboxCapability.WRITE_OUTPUT,
    SandboxCapability.WRITE_TEMP,
    SandboxCapability.LOG_INFO,
}


@dataclass
class ResourceLimits:
    """Resource limits for sandboxed converter execution."""
    
    # Time limits
    timeout_seconds: float = 300.0      # 5 minutes default
    cpu_time_seconds: float = 120.0     # 2 minutes CPU time
    
    # Memory limits
    memory_mb: int = 512                # 512 MB memory limit
    
    # File limits
    max_output_size_mb: int = 100       # 100 MB max output
    max_open_files: int = 50            # Max open file descriptors
    
    # Process limits
    max_processes: int = 1              # No fork bombs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "timeout_seconds": self.timeout_seconds,
            "cpu_time_seconds": self.cpu_time_seconds,
            "memory_mb": self.memory_mb,
            "max_output_size_mb": self.max_output_size_mb,
            "max_open_files": self.max_open_files,
            "max_processes": self.max_processes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResourceLimits":
        """Create from dict."""
        return cls(
            timeout_seconds=data.get("timeout_seconds", 300.0),
            cpu_time_seconds=data.get("cpu_time_seconds", 120.0),
            memory_mb=data.get("memory_mb", 512),
            max_output_size_mb=data.get("max_output_size_mb", 100),
            max_open_files=data.get("max_open_files", 50),
            max_processes=data.get("max_processes", 1),
        )


@dataclass
class SandboxConfig:
    """Configuration for the converter sandbox."""
    
    # Capabilities granted to converter
    capabilities: Set[SandboxCapability] = field(default_factory=lambda: DEFAULT_CAPABILITIES.copy())
    
    # Resource limits
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)
    
    # Allowed paths (for filesystem access)
    allowed_read_paths: List[Path] = field(default_factory=list)
    allowed_write_paths: List[Path] = field(default_factory=list)
    
    # Allowed imports (whitelist)
    allowed_imports: Optional[Set[str]] = None  # None = all standard library allowed
    
    # Blocked imports (blacklist - always applied)
    blocked_imports: Set[str] = field(default_factory=lambda: {
        "os.system", "os.popen", "os.spawn", "os.exec",
        "subprocess", "multiprocessing",
        "ctypes", "cffi",
        "socket",  # Unless NETWORK capability granted
        "__import__", "importlib",
        "builtins.__import__",
        "code", "codeop",  # Interactive code execution
        "pty", "tty",  # Terminal manipulation
    })
    
    # Environment variables to pass through
    safe_env_vars: Set[str] = field(default_factory=lambda: {
        "PATH", "PYTHONPATH", "HOME", "USER", "TEMP", "TMP",
        "LANG", "LC_ALL", "LC_CTYPE",
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for IPC."""
        return {
            "capabilities": [c.value for c in self.capabilities],
            "resource_limits": self.resource_limits.to_dict(),
            "allowed_read_paths": [str(p) for p in self.allowed_read_paths],
            "allowed_write_paths": [str(p) for p in self.allowed_write_paths],
            "allowed_imports": list(self.allowed_imports) if self.allowed_imports else None,
            "blocked_imports": list(self.blocked_imports),
            "safe_env_vars": list(self.safe_env_vars),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SandboxConfig":
        """Create from dict."""
        return cls(
            capabilities={SandboxCapability(c) for c in data.get("capabilities", [])},
            resource_limits=ResourceLimits.from_dict(data.get("resource_limits", {})),
            allowed_read_paths=[Path(p) for p in data.get("allowed_read_paths", [])],
            allowed_write_paths=[Path(p) for p in data.get("allowed_write_paths", [])],
            allowed_imports=set(data["allowed_imports"]) if data.get("allowed_imports") else None,
            blocked_imports=set(data.get("blocked_imports", [])),
            safe_env_vars=set(data.get("safe_env_vars", [])),
        )


# =============================================================================
# Sandbox IPC Protocol
# =============================================================================

class SandboxMessageType(Enum):
    """Message types for sandbox IPC."""
    
    # Host -> Sandbox
    INIT = "init"               # Initialize sandbox with config
    CONVERT = "convert"         # Run conversion
    SHUTDOWN = "shutdown"       # Clean shutdown
    
    # Sandbox -> Host
    READY = "ready"             # Sandbox initialized
    RESULT = "result"           # Conversion result
    LOG = "log"                 # Log message
    ERROR = "error"             # Error occurred
    HEARTBEAT = "heartbeat"     # Keep-alive


@dataclass
class SandboxMessage:
    """Message for sandbox IPC."""
    
    type: SandboxMessageType
    payload: Dict[str, Any] = field(default_factory=dict)
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps({
            "type": self.type.value,
            "payload": self.payload,
        })
    
    @classmethod
    def from_json(cls, data: str) -> "SandboxMessage":
        """Deserialize from JSON string."""
        parsed = json.loads(data)
        return cls(
            type=SandboxMessageType(parsed["type"]),
            payload=parsed.get("payload", {}),
        )


# =============================================================================
# Sandbox Process Manager
# =============================================================================

class SandboxError(Exception):
    """Base exception for sandbox errors."""
    pass


class SandboxTimeoutError(SandboxError):
    """Converter execution timed out."""
    pass


class SandboxResourceError(SandboxError):
    """Converter exceeded resource limits."""
    pass


class SandboxSecurityError(SandboxError):
    """Security violation in sandbox."""
    pass


class SandboxProcess:
    """
    Manages a sandboxed converter process.
    
    Lifecycle:
    1. Create SandboxProcess with config
    2. Call start() to launch subprocess
    3. Call convert() to run conversion
    4. Call stop() to clean up
    
    The subprocess runs a restricted Python environment with:
    - Resource limits (memory, CPU, time)
    - Filesystem restrictions
    - Import restrictions
    - No network access (by default)
    """
    
    def __init__(
        self,
        config: SandboxConfig,
        converter_path: Path,
        converter_class: str,
    ) -> None:
        """
        Initialize sandbox process.
        
        Args:
            config: Sandbox configuration
            converter_path: Path to converter module
            converter_class: Name of converter class to instantiate
        """
        self.config = config
        self.converter_path = converter_path
        self.converter_class = converter_class
        
        self._process: Optional[subprocess.Popen] = None
        self._stdin: Optional[asyncio.StreamWriter] = None
        self._stdout: Optional[asyncio.StreamReader] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._started = False
        self._temp_dir: Optional[Path] = None
    
    @property
    def is_running(self) -> bool:
        """Check if sandbox process is running."""
        return self._process is not None and self._process.poll() is None
    
    async def start(self) -> None:
        """Start the sandbox subprocess."""
        if self._started:
            raise SandboxError("Sandbox already started")
        
        # Create temp directory for sandbox
        self._temp_dir = Path(tempfile.mkdtemp(prefix="pywats_sandbox_"))
        
        # Build subprocess command
        python_exe = sys.executable
        sandbox_runner = Path(__file__).parent / "sandbox_runner.py"
        
        # Create restricted environment
        env = self._create_restricted_env()
        
        # Platform-specific subprocess settings
        kwargs: Dict[str, Any] = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "env": env,
            "cwd": str(self._temp_dir),
        }
        
        # On Unix, set up preexec_fn for resource limits
        if platform.system() != "Windows":
            kwargs["preexec_fn"] = self._setup_unix_limits
        
        # On Windows, use CREATE_NO_WINDOW and job objects
        if platform.system() == "Windows":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        
        try:
            # Start subprocess
            self._process = subprocess.Popen(
                [python_exe, str(sandbox_runner)],
                **kwargs
            )
            
            # Wrap streams for async I/O
            loop = asyncio.get_running_loop()
            
            # Create async readers/writers
            self._stdout = asyncio.StreamReader()
            stdout_protocol = asyncio.StreamReaderProtocol(self._stdout)
            await loop.connect_read_pipe(lambda: stdout_protocol, self._process.stdout)
            
            stdin_transport, stdin_protocol = await loop.connect_write_pipe(
                asyncio.streams.FlowControlMixin,
                self._process.stdin
            )
            self._stdin = asyncio.StreamWriter(stdin_transport, stdin_protocol, None, loop)
            
            # Start stderr reader task
            self._stderr_task = asyncio.create_task(self._read_stderr())
            
            # Send init message
            init_msg = SandboxMessage(
                type=SandboxMessageType.INIT,
                payload={
                    "config": self.config.to_dict(),
                    "converter_path": str(self.converter_path),
                    "converter_class": self.converter_class,
                    "temp_dir": str(self._temp_dir),
                }
            )
            await self._send_message(init_msg)
            
            # Wait for ready
            response = await self._receive_message(timeout=30.0)
            if response.type != SandboxMessageType.READY:
                raise SandboxError(f"Unexpected response: {response.type}")
            
            self._started = True
            logger.info(f"Sandbox started for {self.converter_class}")
            
        except Exception as e:
            await self.stop()
            raise SandboxError(f"Failed to start sandbox: {e}") from e
    
    async def convert(
        self,
        input_path: Path,
        output_path: Path,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run conversion in sandbox.
        
        Args:
            input_path: Path to input file
            output_path: Path for output
            args: Converter arguments
        
        Returns:
            Conversion result dict
        
        Raises:
            SandboxTimeoutError: If conversion times out
            SandboxError: If conversion fails
        """
        if not self.is_running:
            raise SandboxError("Sandbox not running")
        
        # Send convert message
        msg = SandboxMessage(
            type=SandboxMessageType.CONVERT,
            payload={
                "input_path": str(input_path),
                "output_path": str(output_path),
                "args": args,
            }
        )
        await self._send_message(msg)
        
        # Wait for result with timeout
        timeout = self.config.resource_limits.timeout_seconds
        try:
            response = await self._receive_message(timeout=timeout)
        except asyncio.TimeoutError:
            # Kill the process on timeout
            await self._kill_process()
            raise SandboxTimeoutError(
                f"Conversion timed out after {timeout} seconds"
            )
        
        if response.type == SandboxMessageType.ERROR:
            error = response.payload.get("error", "Unknown error")
            raise SandboxError(f"Conversion failed: {error}")
        
        if response.type != SandboxMessageType.RESULT:
            raise SandboxError(f"Unexpected response: {response.type}")
        
        return response.payload
    
    async def stop(self) -> None:
        """Stop the sandbox process."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        
        if self._stderr_task:
            self._stderr_task.cancel()
            self._stderr_task = None
        
        if self._process and self._process.poll() is None:
            # Try graceful shutdown first
            try:
                shutdown_msg = SandboxMessage(type=SandboxMessageType.SHUTDOWN)
                await self._send_message(shutdown_msg)
                
                # Wait briefly for clean exit
                await asyncio.wait_for(
                    asyncio.to_thread(self._process.wait),
                    timeout=5.0
                )
            except (asyncio.TimeoutError, Exception):
                # Force kill
                await self._kill_process()
        
        # Clean up temp directory
        if self._temp_dir and self._temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self._temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean temp dir: {e}")
        
        self._process = None
        self._stdin = None
        self._stdout = None
        self._started = False
        
        logger.info(f"Sandbox stopped for {self.converter_class}")
    
    async def _send_message(self, msg: SandboxMessage) -> None:
        """Send message to sandbox process."""
        if self._stdin is None:
            raise SandboxError("Stdin not available")
        
        data = msg.to_json() + "\n"
        self._stdin.write(data.encode())
        await self._stdin.drain()
    
    async def _receive_message(self, timeout: float = 30.0) -> SandboxMessage:
        """Receive message from sandbox process."""
        if self._stdout is None:
            raise SandboxError("Stdout not available")
        
        try:
            line = await asyncio.wait_for(
                self._stdout.readline(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise
        
        if not line:
            # EOF - process likely crashed
            exit_code = self._process.poll() if self._process else None
            raise SandboxError(f"Sandbox process exited unexpectedly (code={exit_code})")
        
        return SandboxMessage.from_json(line.decode().strip())
    
    async def _read_stderr(self) -> None:
        """Read and log stderr from sandbox."""
        try:
            while self._process and self._process.poll() is None:
                if self._process.stderr:
                    line = await asyncio.to_thread(
                        self._process.stderr.readline
                    )
                    if line:
                        logger.warning(f"[Sandbox stderr] {line.decode().strip()}")
        except Exception:
            pass  # Ignore errors during shutdown
    
    async def _kill_process(self) -> None:
        """Force kill the sandbox process."""
        if self._process and self._process.poll() is None:
            if platform.system() == "Windows":
                self._process.kill()
            else:
                # Send SIGKILL on Unix
                os.kill(self._process.pid, signal.SIGKILL)
            
            try:
                await asyncio.wait_for(
                    asyncio.to_thread(self._process.wait),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.error("Process did not terminate after SIGKILL")
    
    def _create_restricted_env(self) -> Dict[str, str]:
        """Create a restricted environment for the subprocess."""
        env = {}
        
        # Only pass through safe environment variables
        for var in self.config.safe_env_vars:
            if var in os.environ:
                env[var] = os.environ[var]
        
        # Add sandbox-specific variables
        env["PYWATS_SANDBOX"] = "1"
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        
        return env
    
    def _setup_unix_limits(self) -> None:
        """
        Set up resource limits on Unix.
        
        Called in preexec_fn (runs in forked child before exec).
        """
        limits = self.config.resource_limits
        
        try:
            # CPU time limit
            unix_resource.setrlimit(
                unix_resource.RLIMIT_CPU,
                (int(limits.cpu_time_seconds), int(limits.cpu_time_seconds) + 10)
            )
            
            # Memory limit (address space)
            mem_bytes = limits.memory_mb * 1024 * 1024
            unix_resource.setrlimit(
                unix_resource.RLIMIT_AS,
                (mem_bytes, mem_bytes)
            )
            
            # Max open files
            unix_resource.setrlimit(
                unix_resource.RLIMIT_NOFILE,
                (limits.max_open_files, limits.max_open_files)
            )
            
            # Max processes (prevent fork bombs)
            unix_resource.setrlimit(
                unix_resource.RLIMIT_NPROC,
                (limits.max_processes, limits.max_processes)
            )
            
            # Create new session (isolation)
            os.setsid()
            
        except Exception as e:
            # Log but don't fail - some limits may require root
            print(f"Warning: Could not set resource limits: {e}", file=sys.stderr)


# =============================================================================
# Converter Validation (Static Analysis)
# =============================================================================

class ConverterValidator:
    """
    Static analysis validator for converter code.
    
    Checks for:
    - Dangerous imports
    - Dangerous function calls
    - Code patterns that could indicate security issues
    """
    
    # Dangerous patterns to detect
    DANGEROUS_CALLS = {
        "eval", "exec", "compile",
        "open",  # Will be replaced with safe version
        "__import__", "importlib.import_module",
        "os.system", "os.popen", "os.spawn",
        "subprocess.call", "subprocess.run", "subprocess.Popen",
        "socket.socket",
        "ctypes.CDLL", "ctypes.cdll",
    }
    
    DANGEROUS_IMPORTS = {
        "subprocess", "multiprocessing",
        "ctypes", "cffi",
        "socket",
        "os.system",
        "code", "codeop",
        "pty", "tty",
    }
    
    def __init__(self, config: SandboxConfig) -> None:
        self.config = config
    
    def validate_source(self, source: str) -> tuple[bool, List[str]]:
        """
        Validate converter source code.
        
        Args:
            source: Python source code
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues: List[str] = []
        
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]
        
        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.config.blocked_imports:
                        issues.append(f"Blocked import: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    full_name = f"{module}.{alias.name}" if module else alias.name
                    if full_name in self.config.blocked_imports or module in self.config.blocked_imports:
                        issues.append(f"Blocked import: {full_name}")
            
            # Check for dangerous calls
            elif isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name in self.DANGEROUS_CALLS:
                    issues.append(f"Dangerous call: {call_name}")
        
        return len(issues) == 0, issues
    
    def _get_call_name(self, node: ast.Call) -> str:
        """Extract function name from Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return ".".join(reversed(parts))
        return ""
    
    def validate_file(self, path: Path) -> tuple[bool, List[str]]:
        """Validate a converter file."""
        try:
            source = path.read_text(encoding="utf-8")
            return self.validate_source(source)
        except Exception as e:
            return False, [f"Could not read file: {e}"]


# =============================================================================
# High-Level Sandbox Runner (for AsyncConverterPool integration)
# =============================================================================

class ConverterSandbox:
    """
    High-level interface for sandboxed converter execution.
    
    Manages sandbox processes and provides a simple API for the converter pool.
    
    Usage:
        sandbox = ConverterSandbox()
        
        result = await sandbox.run_converter(
            converter_path=Path("my_converter.py"),
            converter_class="MyConverter",
            input_path=Path("input.csv"),
            args={...}
        )
    """
    
    def __init__(
        self,
        default_config: Optional[SandboxConfig] = None,
    ) -> None:
        """
        Initialize converter sandbox.
        
        Args:
            default_config: Default sandbox configuration
        """
        self.default_config = default_config or SandboxConfig()
        self.validator = ConverterValidator(self.default_config)
        
        # Process pool for reuse (keyed by converter path)
        self._processes: Dict[str, SandboxProcess] = {}
        self._lock = asyncio.Lock()
    
    async def run_converter(
        self,
        converter_path: Path,
        converter_class: str,
        input_path: Path,
        output_path: Optional[Path] = None,
        args: Optional[Dict[str, Any]] = None,
        config: Optional[SandboxConfig] = None,
    ) -> Dict[str, Any]:
        """
        Run a converter in a sandbox.
        
        Args:
            converter_path: Path to converter module
            converter_class: Name of converter class
            input_path: Path to input file
            output_path: Path for output (auto-generated if not provided)
            args: Converter arguments
            config: Custom sandbox config (uses default if not provided)
        
        Returns:
            Conversion result dict
        
        Raises:
            SandboxSecurityError: If converter fails validation
            SandboxTimeoutError: If conversion times out
            SandboxError: If conversion fails
        """
        config = config or self.default_config
        args = args or {}
        
        # Validate converter before running
        is_valid, issues = self.validator.validate_file(converter_path)
        if not is_valid:
            raise SandboxSecurityError(
                f"Converter validation failed: {'; '.join(issues)}"
            )
        
        # Generate output path if not provided
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_output.json"
        
        # Get or create sandbox process
        process = await self._get_process(converter_path, converter_class, config)
        
        try:
            # Run conversion
            result = await process.convert(
                input_path=input_path,
                output_path=output_path,
                args=args,
            )
            return result
            
        except SandboxTimeoutError:
            # Remove process from pool on timeout
            await self._remove_process(converter_path)
            raise
        
        except SandboxError:
            # Remove process from pool on error
            await self._remove_process(converter_path)
            raise
    
    async def validate_converter(
        self,
        converter_path: Path,
    ) -> tuple[bool, List[str]]:
        """
        Validate a converter without running it.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        return self.validator.validate_file(converter_path)
    
    async def shutdown(self) -> None:
        """Shutdown all sandbox processes."""
        async with self._lock:
            for process in self._processes.values():
                try:
                    await process.stop()
                except Exception as e:
                    logger.warning(f"Error stopping sandbox: {e}")
            self._processes.clear()
    
    async def _get_process(
        self,
        converter_path: Path,
        converter_class: str,
        config: SandboxConfig,
    ) -> SandboxProcess:
        """Get or create a sandbox process."""
        key = str(converter_path)
        
        async with self._lock:
            if key in self._processes:
                process = self._processes[key]
                if process.is_running:
                    return process
                # Process died, remove it
                del self._processes[key]
            
            # Create new process
            process = SandboxProcess(
                config=config,
                converter_path=converter_path,
                converter_class=converter_class,
            )
            await process.start()
            self._processes[key] = process
            return process
    
    async def _remove_process(self, converter_path: Path) -> None:
        """Remove a process from the pool."""
        key = str(converter_path)
        
        async with self._lock:
            if key in self._processes:
                process = self._processes.pop(key)
                try:
                    await process.stop()
                except Exception:
                    pass


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "SandboxCapability",
    "ResourceLimits",
    "SandboxConfig",
    "SandboxMessageType",
    "SandboxMessage",
    "SandboxError",
    "SandboxTimeoutError",
    "SandboxResourceError",
    "SandboxSecurityError",
    "SandboxProcess",
    "ConverterValidator",
    "ConverterSandbox",
    "DEFAULT_CAPABILITIES",
]
