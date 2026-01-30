"""
SafePath - Secure path resolution for AgentOS.

Ensures all file operations are confined within the sandbox.
"""

from pathlib import Path
from typing import List, Optional


class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass


class SafePath:
    """
    Secure path resolver that prevents sandbox escapes.
    
    All paths are resolved relative to the sandbox root.
    Attempts to escape via '..' or absolute paths are blocked.
    """
    
    def __init__(
        self,
        sandbox_root: Path,
        readonly_paths: Optional[List[Path]] = None
    ):
        """
        Initialize SafePath.
        
        Args:
            sandbox_root: The root directory of the sandbox.
            readonly_paths: List of paths that are read-only.
        """
        self.sandbox_root = Path(sandbox_root).resolve()
        self.readonly_paths = [Path(p).resolve() for p in (readonly_paths or [])]
        
        # Ensure sandbox exists
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
    
    def resolve(self, path: str, cwd: Path = None) -> Path:
        """
        Resolve a path securely within the sandbox.
        
        Args:
            path: The path to resolve (relative or absolute-looking).
            cwd: Current working directory (relative to sandbox).
            
        Returns:
            Absolute Path object within sandbox.
            
        Raises:
            SecurityError: If path attempts to escape sandbox.
        """
        path = str(path).strip()
        
        # Empty path = current directory
        if not path or path == ".":
            if cwd:
                # Convert cwd to string and remove leading slash for Windows compatibility
                cwd_str = str(cwd).lstrip("/")
                return self.sandbox_root / cwd_str
            return self.sandbox_root
        
        # Block obvious escape attempts
        if ".." in path:
            raise SecurityError(
                "Error [PATH_ESCAPE]: Access denied. "
                "Cannot navigate outside your sandbox using '..'"
            )
        
        # Handle "absolute" paths (they're actually relative to sandbox)
        if path.startswith("/"):
            # Remove leading slash, treat as relative to sandbox
            path = path.lstrip("/")
        
        # Build the full path
        if cwd and not path.startswith("/"):
            # Relative to CWD
            base = self.sandbox_root / str(cwd).lstrip("/")
            full_path = (base / path).resolve()
        else:
            full_path = (self.sandbox_root / path).resolve()
        
        # Security check: ensure we're still in sandbox
        try:
            full_path.relative_to(self.sandbox_root)
        except ValueError:
            raise SecurityError(
                f"Error [PATH_ESCAPE]: Access denied. "
                f"Path '{path}' resolves outside sandbox."
            )
        
        return full_path
    
    def is_writable(self, resolved_path: Path) -> bool:
        """
        Check if a path is writable.
        
        Args:
            resolved_path: An already-resolved absolute path.
            
        Returns:
            True if writable, False if read-only.
        """
        resolved = resolved_path.resolve()
        
        for ro_path in self.readonly_paths:
            try:
                resolved.relative_to(ro_path)
                return False  # Path is under a read-only directory
            except ValueError:
                continue
        
        return True
    
    def to_virtual(self, resolved_path: Path) -> str:
        """
        Convert a resolved path back to virtual (sandbox-relative) path.
        
        Args:
            resolved_path: An absolute path within the sandbox.
            
        Returns:
            Virtual path string (e.g., '/memory/facts/user.md').
        """
        try:
            relative = resolved_path.relative_to(self.sandbox_root)
            return "/" + str(relative)
        except ValueError:
            return str(resolved_path)
