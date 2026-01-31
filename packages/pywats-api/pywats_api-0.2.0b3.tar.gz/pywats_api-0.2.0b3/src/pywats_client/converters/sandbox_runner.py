#!/usr/bin/env python3
"""
Sandbox Runner - Isolated Converter Execution Process

This script runs inside the sandbox subprocess and:
1. Receives configuration from parent process
2. Sets up restricted execution environment
3. Loads and runs the converter
4. Returns results to parent

IMPORTANT: This runs with restricted permissions.
"""

import ast
import builtins
import importlib.util
import io
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Set up basic logging
logging.basicConfig(
    level=logging.WARNING,
    format="[sandbox] %(levelname)s: %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


# =============================================================================
# Message Protocol (matching sandbox.py)
# =============================================================================

class MessageType:
    INIT = "init"
    CONVERT = "convert"
    SHUTDOWN = "shutdown"
    READY = "ready"
    RESULT = "result"
    LOG = "log"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


def send_message(msg_type: str, payload: Dict[str, Any] = None) -> None:
    """Send message to parent process via stdout."""
    payload = payload or {}
    msg = json.dumps({"type": msg_type, "payload": payload})
    print(msg, flush=True)


def receive_message() -> Dict[str, Any]:
    """Receive message from parent process via stdin."""
    line = sys.stdin.readline()
    if not line:
        raise EOFError("Parent closed connection")
    return json.loads(line.strip())


def send_error(error: str) -> None:
    """Send error message to parent."""
    send_message(MessageType.ERROR, {"error": error})


def send_log(level: str, message: str) -> None:
    """Send log message to parent."""
    send_message(MessageType.LOG, {"level": level, "message": message})


# =============================================================================
# Restricted Builtins
# =============================================================================

# Functions that are blocked entirely
BLOCKED_BUILTINS = {
    "eval", "exec", "compile",
    "__import__",
    "open",  # Will provide safe_open instead
    "input",  # No interactive input in sandbox
    "breakpoint",  # No debugging
}

# Original open for our use
_original_open = builtins.open


class SafeFileHandler:
    """
    Safe file operations with path restrictions.
    
    Only allows access to explicitly permitted paths.
    """
    
    def __init__(
        self,
        allowed_read_paths: List[Path],
        allowed_write_paths: List[Path],
        temp_dir: Path,
    ) -> None:
        self.allowed_read_paths = [p.resolve() for p in allowed_read_paths]
        self.allowed_write_paths = [p.resolve() for p in allowed_write_paths]
        self.temp_dir = temp_dir.resolve()
    
    def _is_path_allowed(self, path: Path, for_write: bool) -> bool:
        """Check if path access is allowed."""
        resolved = path.resolve()
        
        # Temp dir is always allowed
        if self._is_under_path(resolved, self.temp_dir):
            return True
        
        # Check against allowed paths
        allowed_list = self.allowed_write_paths if for_write else self.allowed_read_paths
        return any(self._is_under_path(resolved, allowed) for allowed in allowed_list)
    
    def _is_under_path(self, path: Path, parent: Path) -> bool:
        """Check if path is under parent directory."""
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False
    
    def safe_open(
        self,
        file: str | Path,
        mode: str = "r",
        *args,
        **kwargs
    ):
        """
        Safe open function with path restrictions.
        
        Raises PermissionError for disallowed paths.
        """
        path = Path(file)
        is_write = any(c in mode for c in "waxb+")
        
        if not self._is_path_allowed(path, is_write):
            action = "write to" if is_write else "read from"
            raise PermissionError(f"Sandbox: Not allowed to {action} {path}")
        
        return _original_open(file, mode, *args, **kwargs)


# =============================================================================
# Restricted Import System
# =============================================================================

class RestrictedImporter:
    """
    Custom import hook that blocks dangerous imports.
    """
    
    def __init__(self, blocked_imports: Set[str]) -> None:
        self.blocked_imports = blocked_imports
    
    def find_module(self, fullname: str, path=None):
        """Check if import is allowed."""
        # Check if module or any parent is blocked
        parts = fullname.split(".")
        for i in range(len(parts)):
            check_name = ".".join(parts[:i+1])
            if check_name in self.blocked_imports:
                return self  # Return self to block import
        return None  # Allow normal import
    
    def load_module(self, fullname: str):
        """Raise error for blocked imports."""
        raise ImportError(f"Sandbox: Import of '{fullname}' is not allowed")


# =============================================================================
# Converter Loading
# =============================================================================

def load_converter(
    converter_path: Path,
    converter_class: str,
    safe_builtins: dict,
) -> Any:
    """
    Load a converter class from file.
    
    Args:
        converter_path: Path to converter module
        converter_class: Name of class to instantiate
        safe_builtins: Restricted builtins dict
    
    Returns:
        Converter instance
    """
    # Read source
    source = converter_path.read_text(encoding="utf-8")
    
    # Compile
    code = compile(source, str(converter_path), "exec")
    
    # Create module namespace with restricted builtins
    module_dict = {
        "__builtins__": safe_builtins,
        "__name__": converter_path.stem,
        "__file__": str(converter_path),
    }
    
    # Execute module
    exec(code, module_dict)
    
    # Get converter class
    if converter_class not in module_dict:
        raise ValueError(f"Converter class '{converter_class}' not found in {converter_path}")
    
    klass = module_dict[converter_class]
    
    # Instantiate
    return klass()


# =============================================================================
# Main Sandbox Loop
# =============================================================================

class SandboxRunner:
    """Main sandbox execution environment."""
    
    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}
        self.converter: Any = None
        self.file_handler: Optional[SafeFileHandler] = None
        self.safe_builtins: dict = {}
        self.temp_dir: Optional[Path] = None
        self.running = True
    
    def setup(self, config: Dict[str, Any]) -> None:
        """Set up sandbox environment from config."""
        self.config = config
        
        # Get paths
        self.temp_dir = Path(config.get("temp_dir", "/tmp/sandbox"))
        converter_path = Path(config["converter_path"])
        converter_class = config["converter_class"]
        sandbox_config = config.get("config", {})
        
        # Set up file handler
        allowed_read = [Path(p) for p in sandbox_config.get("allowed_read_paths", [])]
        allowed_write = [Path(p) for p in sandbox_config.get("allowed_write_paths", [])]
        
        # Always allow reading converter file and input path
        allowed_read.append(converter_path.parent)
        
        self.file_handler = SafeFileHandler(
            allowed_read_paths=allowed_read,
            allowed_write_paths=allowed_write,
            temp_dir=self.temp_dir,
        )
        
        # Set up restricted builtins
        self.safe_builtins = self._create_safe_builtins()
        
        # Set up import restrictions
        blocked_imports = set(sandbox_config.get("blocked_imports", []))
        importer = RestrictedImporter(blocked_imports)
        sys.meta_path.insert(0, importer)
        
        # Load converter
        self.converter = load_converter(
            converter_path,
            converter_class,
            self.safe_builtins,
        )
    
    def _create_safe_builtins(self) -> dict:
        """Create restricted builtins dict."""
        safe = {}
        
        # Copy all safe builtins
        for name in dir(builtins):
            if not name.startswith("_") and name not in BLOCKED_BUILTINS:
                safe[name] = getattr(builtins, name)
        
        # Add safe open
        safe["open"] = self.file_handler.safe_open
        
        # Add safe print (goes to parent via log message)
        def safe_print(*args, **kwargs):
            message = " ".join(str(a) for a in args)
            send_log("INFO", message)
        safe["print"] = safe_print
        
        return safe
    
    def run_conversion(
        self,
        input_path: Path,
        output_path: Path,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run the converter."""
        if self.converter is None:
            raise RuntimeError("Converter not loaded")
        
        # Add input path to allowed reads
        if self.file_handler:
            self.file_handler.allowed_read_paths.append(input_path.resolve())
            self.file_handler.allowed_write_paths.append(output_path.parent.resolve())
        
        # Call converter's convert method
        # Adapting to the actual ConverterBase API
        from dataclasses import dataclass
        from pathlib import Path as PathType
        
        # Create minimal FileInfo
        @dataclass
        class FileInfo:
            path: PathType
            name: str
            stem: str
            extension: str
            size: int
            
            def __init__(self, path: PathType):
                self.path = path
                self.name = path.name
                self.stem = path.stem
                self.extension = path.suffix
                self.size = path.stat().st_size if path.exists() else 0
        
        # Create minimal ConverterArguments
        @dataclass
        class ConverterArguments:
            file_info: FileInfo
            drop_folder: PathType
            done_folder: PathType
            error_folder: PathType
            api_client: Any = None
            user_settings: Dict[str, Any] = None
            
            def __post_init__(self):
                if self.user_settings is None:
                    self.user_settings = {}
        
        file_info = FileInfo(input_path)
        converter_args = ConverterArguments(
            file_info=file_info,
            drop_folder=input_path.parent,
            done_folder=output_path.parent / "done",
            error_folder=output_path.parent / "error",
            user_settings=args.get("user_settings", {}),
        )
        
        # Call convert_file method
        result = self.converter.convert_file(input_path, converter_args)
        
        # Convert result to dict
        return {
            "status": result.status.value if hasattr(result.status, "value") else str(result.status),
            "report": result.report,
            "error": result.error,
            "post_action": result.post_action.value if hasattr(result, "post_action") and result.post_action else None,
            "metadata": result.metadata if hasattr(result, "metadata") else {},
        }
    
    def run(self) -> None:
        """Main message loop."""
        try:
            while self.running:
                try:
                    msg = receive_message()
                except EOFError:
                    break
                
                msg_type = msg.get("type")
                payload = msg.get("payload", {})
                
                if msg_type == MessageType.INIT:
                    try:
                        self.setup(payload)
                        send_message(MessageType.READY)
                    except Exception as e:
                        send_error(f"Init failed: {e}\n{traceback.format_exc()}")
                
                elif msg_type == MessageType.CONVERT:
                    try:
                        input_path = Path(payload["input_path"])
                        output_path = Path(payload["output_path"])
                        args = payload.get("args", {})
                        
                        result = self.run_conversion(input_path, output_path, args)
                        send_message(MessageType.RESULT, result)
                        
                    except PermissionError as e:
                        send_error(f"Permission denied: {e}")
                    except Exception as e:
                        send_error(f"Conversion failed: {e}\n{traceback.format_exc()}")
                
                elif msg_type == MessageType.SHUTDOWN:
                    self.running = False
                    break
                
                else:
                    send_error(f"Unknown message type: {msg_type}")
        
        except Exception as e:
            logger.error(f"Sandbox error: {e}", exc_info=True)
            send_error(f"Sandbox error: {e}")
        
        finally:
            logger.info("Sandbox shutting down")


# =============================================================================
# Entry Point
# =============================================================================

def main():
    """Main entry point for sandbox runner."""
    # Verify we're running in sandbox
    if os.environ.get("PYWATS_SANDBOX") != "1":
        print("ERROR: This script should only run inside the sandbox", file=sys.stderr)
        sys.exit(1)
    
    runner = SandboxRunner()
    runner.run()


if __name__ == "__main__":
    main()
