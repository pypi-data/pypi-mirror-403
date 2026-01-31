"""Path utilities for step and measurement paths.

WATS uses the pilcrow character (¶) as a path separator internally,
but users are familiar with and some endpoints return forward slash (/).
These utilities provide seamless conversion between formats.

Usage:
    from pywats import StepPath, MeasurementPath
    
    # Create paths - both formats work
    path1 = StepPath("Main/Setup/Initialize")
    path2 = StepPath("Main¶Setup¶Initialize")  # Same result
    
    # Use in filters
    filter = WATSFilter(measurement_paths=str(MeasurementPath("Main/Tests/Voltage")))
"""
from typing import Optional, List, Union

# The pilcrow character used as path separator in WATS API
PILCROW = "¶"
SLASH = "/"


def normalize_path(path: str) -> str:
    """
    Normalize a path by converting slashes to pilcrows.
    
    This is the format expected by WATS API endpoints.
    
    Args:
        path: Path string using either / or ¶ as separator
        
    Returns:
        Path with ¶ separators (API format)
        
    Example:
        >>> normalize_path("Main/Setup/Test")
        'Main¶Setup¶Test'
        >>> normalize_path("Main¶Setup¶Test")
        'Main¶Setup¶Test'
    """
    return path.replace(SLASH, PILCROW)


def display_path(path: str) -> str:
    """
    Convert a path to display format (slashes).
    
    This is the format users see in the WATS GUI.
    
    Args:
        path: Path string using either / or ¶ as separator
        
    Returns:
        Path with / separators (display format)
        
    Example:
        >>> display_path("Main¶Setup¶Test")
        'Main/Setup/Test'
    """
    return path.replace(PILCROW, SLASH)


class StepPath:
    """
    Represents a test step path in WATS.
    
    Handles automatic conversion between display format (/) and API format (¶).
    Users can input paths in either format - the class handles conversion.
    
    Path format:
        "Group/SubGroup/StepName" or "Group¶SubGroup¶StepName"
    
    Example:
        >>> path = StepPath("Main/Setup/Initialize")
        >>> str(path)  # For API calls
        'Main¶Setup¶Initialize'
        >>> path.display  # For user display
        'Main/Setup/Initialize'
        >>> path.parts
        ['Main', 'Setup', 'Initialize']
    """
    
    def __init__(self, path: str):
        """
        Create a StepPath from a string.
        
        Args:
            path: Path using / or ¶ as separator
        """
        self._path = normalize_path(path)
    
    @property
    def api_format(self) -> str:
        """Path in API format (with ¶ separators)."""
        return self._path
    
    @property
    def display(self) -> str:
        """Path in display format (with / separators)."""
        return display_path(self._path)
    
    @property
    def parts(self) -> List[str]:
        """Path components as a list."""
        return self._path.split(PILCROW)
    
    @property
    def name(self) -> str:
        """The final component (step name)."""
        parts = self.parts
        return parts[-1] if parts else ""
    
    @property
    def parent(self) -> Optional["StepPath"]:
        """Parent path, or None if at root."""
        parts = self.parts
        if len(parts) <= 1:
            return None
        return StepPath(PILCROW.join(parts[:-1]))
    
    def __str__(self) -> str:
        """String representation uses API format for direct use in API calls."""
        return self._path
    
    def __repr__(self) -> str:
        return f"StepPath({self.display!r})"
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, StepPath):
            return self._path == other._path
        if isinstance(other, str):
            return self._path == normalize_path(other)
        return False
    
    def __hash__(self) -> int:
        return hash(self._path)
    
    def __truediv__(self, other: str) -> "StepPath":
        """
        Append a path component using / operator.
        
        Example:
            >>> path = StepPath("Main") / "Setup" / "Test"
            >>> path.display
            'Main/Setup/Test'
        """
        return StepPath(f"{self._path}{PILCROW}{other}")
    
    @classmethod
    def from_parts(cls, *parts: str) -> "StepPath":
        """
        Create a path from individual components.
        
        Example:
            >>> path = StepPath.from_parts("Main", "Setup", "Test")
            >>> path.display
            'Main/Setup/Test'
        """
        return cls(PILCROW.join(parts))


class MeasurementPath(StepPath):
    """
    Represents a measurement path in WATS.
    
    Extends StepPath with measurement-specific semantics.
    A measurement path includes the step path plus the measurement name.
    
    Path format:
        "Group/StepName/MeasurementName" or "Group/StepName//MeasurementName"
        (double separator indicates step-to-measurement boundary in some APIs)
    
    Example:
        >>> path = MeasurementPath("Main/Voltage Test/Output")
        >>> str(path)  # For API calls
        'Main¶Voltage Test¶Output'
        >>> path.step_path.display
        'Main/Voltage Test'
        >>> path.measurement_name
        'Output'
    """
    
    @property
    def measurement_name(self) -> str:
        """The measurement name (final component)."""
        return self.name
    
    @property
    def step_path(self) -> StepPath:
        """The step path portion (without measurement name)."""
        parent = self.parent
        return parent if parent else StepPath("")


def normalize_paths(paths: Union[str, List[str], StepPath, List[StepPath]]) -> str:
    """
    Normalize one or more paths for API requests.
    
    Multiple paths are joined with semicolon (;) as per WATS API.
    
    Args:
        paths: Single path or list of paths (string or StepPath)
        
    Returns:
        Semicolon-separated paths in API format
        
    Example:
        >>> normalize_paths("Main/Test1")
        'Main¶Test1'
        >>> normalize_paths(["Main/Test1", "Main/Test2"])
        'Main¶Test1;Main¶Test2'
    """
    if isinstance(paths, (StepPath, str)):
        return str(StepPath(paths) if isinstance(paths, str) else paths)
    
    # List of paths
    return ";".join(
        str(StepPath(p) if isinstance(p, str) else p) 
        for p in paths
    )
