"""
SafeKernel - The core execution engine for AgentOS.

This module implements the "Smart Shell" that parses and executes
Unix-like commands in a secure, sandboxed environment.
"""

import re
import json
import time
import gzip
import shutil
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from collections import deque

# File locking - use fcntl on Unix, fallback for Windows
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

from topaz_agent_kit.core.agentos.safe_path import SafePath, SecurityError
from topaz_agent_kit.core.agentos.vector_store import VectorStore
from topaz_agent_kit.core.agentos.memory_config import MemoryConfig, PathMapping
from topaz_agent_kit.utils.logger import Logger


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class FileLock:
    """
    Thread-safe file locking with optional OS-level locking.
    
    Uses threading.Lock for cross-thread safety and fcntl.flock
    for cross-process safety on Unix systems.
    """
    _locks: Dict[str, threading.Lock] = {}
    _lock_registry = threading.Lock()
    
    @classmethod
    def get_lock(cls, file_path: Path) -> threading.Lock:
        """Get or create a lock for a specific file path."""
        path_str = str(file_path.resolve())
        with cls._lock_registry:
            if path_str not in cls._locks:
                cls._locks[path_str] = threading.Lock()
            return cls._locks[path_str]
    
    @classmethod
    def cleanup_lock(cls, file_path: Path):
        """Remove a lock from registry (optional, for cleanup)."""
        path_str = str(file_path.resolve())
        with cls._lock_registry:
            cls._locks.pop(path_str, None)


class RateLimiter:
    """
    Sliding window rate limiter.
    
    Tracks command timestamps and rejects requests that exceed
    the configured rate.
    """
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed in the window.
            window_seconds: Time window in seconds.
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps: deque = deque()
        self._lock = threading.Lock()
    
    def check(self) -> bool:
        """
        Check if a request is allowed.
        
        Returns:
            True if allowed, raises RateLimitExceeded if not.
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        with self._lock:
            # Remove timestamps outside the window
            while self.timestamps and self.timestamps[0] < window_start:
                self.timestamps.popleft()
            
            # Check if we're over the limit
            if len(self.timestamps) >= self.max_requests:
                oldest = self.timestamps[0]
                retry_after = int(oldest - window_start) + 1
                raise RateLimitExceeded(
                    f"Error [RATE_LIMITED]: Too many requests. "
                    f"Limit is {self.max_requests} commands per {self.window_seconds} seconds. "
                    f"Retry in {retry_after}s."
                )
            
            # Record this request
            self.timestamps.append(now)
            return True
    
    def get_remaining(self) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        window_start = now - self.window_seconds
        
        with self._lock:
            # Count valid timestamps
            count = sum(1 for t in self.timestamps if t >= window_start)
            return max(0, self.max_requests - count)


@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    output: str
    error_code: Optional[str] = None


class UserRole:
    """User role constants for RBAC."""
    USER = "user"           # Can only access own folder
    MANAGER = "manager"     # Can access team members' folders
    ADMIN = "admin"         # Can access all user folders
    AUDITOR = "auditor"     # Read-only access to everything


class TeamResolver:
    """
    Resolves team membership for RBAC.
    
    Supports three modes:
    - STATIC: Team members passed as a list at initialization
    - FILE: Team hierarchy loaded from a JSON file
    - CALLBACK: External function to resolve team members
    """
    
    MODE_STATIC = "static"
    MODE_FILE = "file"
    MODE_CALLBACK = "callback"
    
    def __init__(
        self,
        mode: str = MODE_STATIC,
        managed_users: Optional[List[str]] = None,
        team_file_path: Optional[Path] = None,
        resolver_callback: Optional[callable] = None
    ):
        """
        Initialize TeamResolver.
        
        Args:
            mode: Resolution mode (static, file, callback).
            managed_users: Static list of managed user IDs.
            team_file_path: Path to teams.json file.
            resolver_callback: Function(user_id, role) -> List[str] of managed users.
        """
        self.mode = mode
        self._managed_users = managed_users or []
        self._team_file_path = team_file_path
        self._resolver_callback = resolver_callback
        self._cache: Dict[str, List[str]] = {}
        self._cache_time: Optional[float] = None
        self._cache_ttl = 300  # 5 minute cache
    
    def get_managed_users(self, user_id: str, team_id: Optional[str] = None) -> List[str]:
        """
        Get list of users this user can manage/access.
        
        Args:
            user_id: The requesting user's ID.
            team_id: Optional team ID for file-based resolution.
            
        Returns:
            List of user IDs this user can access.
        """
        if self.mode == self.MODE_STATIC:
            return self._managed_users
        
        elif self.mode == self.MODE_FILE:
            return self._resolve_from_file(user_id, team_id)
        
        elif self.mode == self.MODE_CALLBACK:
            if self._resolver_callback:
                try:
                    return self._resolver_callback(user_id, team_id)
                except Exception:
                    return []
            return []
        
        return []
    
    def _resolve_from_file(self, user_id: str, team_id: Optional[str]) -> List[str]:
        """Resolve team members from JSON file."""
        if not self._team_file_path or not self._team_file_path.exists():
            return []
        
        # Check cache
        now = time.time()
        if self._cache_time and (now - self._cache_time) < self._cache_ttl:
            cache_key = f"{user_id}:{team_id}"
            if cache_key in self._cache:
                return self._cache[cache_key]
        
        try:
            with open(self._team_file_path, "r", encoding="utf-8") as f:
                teams_data = json.load(f)
            
            # Expected format:
            # {
            #   "teams": {
            #     "engineering": {
            #       "manager": "john_smith",
            #       "members": ["jane_doe", "bob_wilson"]
            #     }
            #   },
            #   "admins": ["admin_user"]
            # }
            
            managed = []
            
            # Check if user is a team manager
            for tid, team_info in teams_data.get("teams", {}).items():
                if team_info.get("manager") == user_id:
                    managed.extend(team_info.get("members", []))
                # If team_id specified, also include if user is in that team
                if team_id and tid == team_id:
                    if user_id in team_info.get("members", []) or team_info.get("manager") == user_id:
                        managed.extend(team_info.get("members", []))
            
            # Remove duplicates and self
            managed = list(set(m for m in managed if m != user_id))
            
            # Cache result
            cache_key = f"{user_id}:{team_id}"
            self._cache[cache_key] = managed
            self._cache_time = now
            
            return managed
            
        except (json.JSONDecodeError, KeyError, TypeError):
            return []


class AccessDeniedError(SecurityError):
    """Raised when user access is denied due to RBAC."""
    pass


class SafeKernel:
    """
    The Safe Kernel - Core execution engine for AgentOS.
    
    Provides a Unix-like shell interface that is:
    - Sandboxed to a specific directory tree
    - Permission-aware (read-only vs read-write)
    - Augmented with semantic search (semgrep)
    - Auto-indexing for memory files
    """
    
    # Commands that are completely blocked
    BLOCKED_COMMANDS = [
        "rm", "rmdir", "mv", "cp", "chmod", "chown", "chgrp",
        "sudo", "su", "curl", "wget", "ssh", "scp", "rsync",
        "kill", "pkill", "killall", "shutdown", "reboot",
        "dd", "mkfs", "mount", "umount", "fdisk",
        "python", "python3", "node", "ruby", "perl", "bash", "sh", "zsh"
    ]
    
    # Maximum limits to prevent resource exhaustion
    MAX_READ_BYTES = 50 * 1024  # 50KB
    MAX_READ_LINES = 100
    MAX_LIST_ITEMS = 100
    MAX_GREP_RESULTS = 50
    MAX_FIND_RESULTS = 100
    MAX_RECURSIVE_DEPTH = 5
    COMMAND_TIMEOUT = 30  # seconds
    
    # Dangerous shell operators to block (checked outside quotes)
    DANGEROUS_OPERATORS = ["&&", "||", ";", "`", "$(", "${"]
    # Pipe is handled separately - only blocked outside quotes
    PIPE_OPERATOR = "|"
    INVALID_FILENAME_CHARS = ["&&", "||", ";", "`", "$", "<", ">", "\n", "\r"]
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = 60  # commands per minute
    DEFAULT_RATE_WINDOW = 60  # seconds
    
    # Audit log rotation
    AUDIT_LOG_MAX_DAYS = 30  # keep logs for 30 days
    AUDIT_LOG_COMPRESS_AFTER_DAYS = 1  # compress logs older than 1 day
    
    def __init__(
        self,
        data_root: str,
        agent_id: str = "default",
        # RBAC parameters
        user_id: Optional[str] = None,
        user_role: str = UserRole.USER,
        team_id: Optional[str] = None,
        # Team resolution options (choose one)
        managed_users: Optional[List[str]] = None,  # Option A: Static list
        team_file_path: Optional[str] = None,        # Option B: JSON file
        team_resolver_callback: Optional[callable] = None,  # Option C: External callback
        # Other options
        vector_store: Optional[VectorStore] = None,
        enable_audit_log: bool = True,
        rate_limit: Optional[int] = None,
        rate_window: Optional[int] = None,
        # Confirmation settings
        require_confirmation: bool = False,
        confirm_operations: Optional[List[str]] = None,  # ["write", "delete", "mkdir"]
        confirm_paths: Optional[List[str]] = None,  # ["/me/"] - paths requiring confirmation
        # Memory configuration
        memory_config: Optional[MemoryConfig] = None,
        pipeline_id: Optional[str] = None,
        project_dir: Optional[Path] = None,
    ):
        """
        Initialize the Safe Kernel.
        
        Args:
            data_root: Root directory for all data.
            agent_id: Agent identifier (required for memory isolation).
            user_id: Current user's identifier (for RBAC).
            user_role: User's role - 'user', 'manager', 'admin', 'auditor'.
            team_id: User's team identifier.
            managed_users: Option A - Static list of user IDs this user can access.
            team_file_path: Option B - Path to teams.json for team hierarchy.
            team_resolver_callback: Option C - Function(user_id, team_id) -> List[str].
            vector_store: Optional VectorStore for semantic search.
            enable_audit_log: Whether to log all commands.
            rate_limit: Max commands per window (default: 60).
            rate_window: Rate limit window in seconds (default: 60).
            require_confirmation: If True, write ops need # CONFIRMED tag.
            confirm_operations: Which ops need confirmation - write, delete, mkdir.
            confirm_paths: Paths that require confirmation (e.g., ["/me/"]).
            memory_config: Optional memory configuration for directories and path mappings.
            pipeline_id: Optional pipeline identifier for shared memory.
            project_dir: Optional project directory for initializing shared memory from config.
        """
        self.logger = Logger("AgentOS.Kernel")
        self.data_root = Path(data_root).resolve()
        # Ensure data_root directory exists
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.agent_id = agent_id
        self.pipeline_id = pipeline_id
        self.project_dir = Path(project_dir) if project_dir else None
        self.enable_audit_log = enable_audit_log
        
        # RBAC settings
        self.user_id = user_id
        self.user_role = user_role
        self.team_id = team_id
        
        # Confirmation settings
        self.require_confirmation = require_confirmation
        self.confirm_operations = confirm_operations or ["write", "delete"]
        self.confirm_paths = confirm_paths  # None means all paths
        
        # Memory configuration
        self.memory_config = memory_config
        
        # Build paths using memory config or defaults
        if memory_config and memory_config.path_mappings:
            # Use configured path mappings
            self._build_paths_from_config()
        else:
            # Use default paths (backward compatibility)
            if self.pipeline_id:
                self.agent_root = self.data_root / self.pipeline_id / "agents" / agent_id
                self.shared_path = self.data_root / self.pipeline_id / "shared"
            else:
                self.agent_root = self.data_root / "default" / "agents" / agent_id
                self.shared_path = self.data_root / "default" / "shared"
            self.global_shared = self.data_root / "global_shared"
        
        # Store path mappings for _resolve_path
        if memory_config and memory_config.path_mappings:
            self.path_mappings = memory_config.path_mappings
        else:
            # Default mappings (create PathMapping objects)
            from topaz_agent_kit.core.agentos.memory_config import PathMapping
            self.path_mappings = {
                "/shared": PathMapping(
                    prefix="/shared",
                    type="pipeline_shared",
                    base=str(self.shared_path.relative_to(self.data_root))
                ),
                "/global": PathMapping(
                    prefix="/global",
                    type="global_shared",
                    base=str(self.global_shared.relative_to(self.data_root))
                ),
                "/memory": PathMapping(
                    prefix="/memory",
                    type="agent_memory",
                    base=str((self.agent_root.relative_to(self.data_root) / "memory"))
                ),
                "/workspace": PathMapping(
                    prefix="/workspace",
                    type="agent_workspace",
                    base=str((self.agent_root.relative_to(self.data_root) / "workspace"))
                )
            }
        
        # Initialize TeamResolver based on provided options
        if team_resolver_callback:
            self.team_resolver = TeamResolver(
                mode=TeamResolver.MODE_CALLBACK,
                resolver_callback=team_resolver_callback
            )
        elif team_file_path:
            self.team_resolver = TeamResolver(
                mode=TeamResolver.MODE_FILE,
                team_file_path=Path(team_file_path)
            )
        else:
            self.team_resolver = TeamResolver(
                mode=TeamResolver.MODE_STATIC,
                managed_users=managed_users or []
            )
        
        # Virtual current working directory (starts at root, or /me/ if user_id set)
        self.cwd = "/"
        
        # Determine read-only paths from memory config
        readonly_paths = []
        if memory_config:
            for dir_config in memory_config.shared_directories:
                if dir_config.readonly:
                    # Resolve shared directory path
                    mapping = self.path_mappings.get("/shared")
                    if mapping:
                        readonly_paths.append(self.data_root / mapping.base)
        else:
            # Default: shared and global are read-only
            readonly_paths = [self.shared_path, self.global_shared]
        
        # Initialize SafePath with read-only paths
        self.safe_path = SafePath(
            sandbox_root=self.agent_root,
            readonly_paths=readonly_paths
        )
        
        # We need to handle shared paths specially - they're outside agent_root
        # but should still be accessible for reading
        self._accessible_readonly_roots = readonly_paths
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=rate_limit or self.DEFAULT_RATE_LIMIT,
            window_seconds=rate_window or self.DEFAULT_RATE_WINDOW
        )
        
        # Vector store for semantic search
        if vector_store:
            self.vector_store = vector_store
        else:
            index_path = self.agent_root / ".index" / "vectors.json"
            self.vector_store = VectorStore(storage_path=index_path)
        
        # Bootstrap directory structure
        self._bootstrap()
        
        # Initialize shared memory from config/memory/shared/pipeline/ if available
        self._initialize_shared_memory_from_config()
        
        # Initialize global memory from config/memory/shared/global/ if available
        self._initialize_global_memory_from_config()
    
    def _build_paths_from_config(self):
        """Build paths from memory configuration."""
        # Find agent_root from /memory or /workspace mapping
        memory_mapping = self.memory_config.path_mappings.get("/memory")
        if memory_mapping:
            # Extract base path (e.g., "{pipeline_id}/agents/{agent_id}/memory")
            # Remove "/memory" suffix to get agent root
            base = memory_mapping.base
            if base.endswith("/memory"):
                base = base[:-7]  # Remove "/memory"
            self.agent_root = self.data_root / base
        else:
            # Fallback to default
            if self.pipeline_id:
                self.agent_root = self.data_root / self.pipeline_id / "agents" / self.agent_id
            else:
                self.agent_root = self.data_root / "default" / "agents" / self.agent_id
        
        # Find shared_path from /shared mapping
        shared_mapping = self.memory_config.path_mappings.get("/shared")
        if shared_mapping:
            self.shared_path = self.data_root / shared_mapping.base
        else:
            # Fallback to default
            if self.pipeline_id:
                self.shared_path = self.data_root / self.pipeline_id / "shared"
            else:
                self.shared_path = self.data_root / "default" / "shared"
        
        # Global shared (always default)
        self.global_shared = self.data_root / "global_shared"
    
    def _bootstrap(self):
        """Create the directory structure on first run."""
        dirs = []
        
        if self.memory_config:
            # Bootstrap from memory config
            # Agent directories
            for dir_config in self.memory_config.directories:
                if dir_config.bootstrap:
                    # Resolve path from virtual path
                    try:
                        resolved = self._resolve_path(dir_config.path)
                        if resolved.is_dir() or not resolved.exists():
                            dirs.append(resolved)
                    except Exception as e:
                        self.logger.warning("Failed to resolve path {} for bootstrap: {}", dir_config.path, e)
            
            # Shared directories
            for dir_config in self.memory_config.shared_directories:
                if dir_config.bootstrap:
                    try:
                        resolved = self._resolve_path(dir_config.path)
                        if resolved.is_dir() or not resolved.exists():
                            dirs.append(resolved)
                    except Exception as e:
                        self.logger.warning("Failed to resolve shared path {} for bootstrap: {}", dir_config.path, e)
            
            # Global directories
            for dir_config in self.memory_config.global_directories:
                if dir_config.bootstrap:
                    try:
                        resolved = self._resolve_path(dir_config.path)
                        if resolved.is_dir() or not resolved.exists():
                            dirs.append(resolved)
                    except Exception as e:
                        self.logger.warning("Failed to resolve global path {} for bootstrap: {}", dir_config.path, e)
            
            # Fallback: Always bootstrap default global_shared directories if no config
            if not self.memory_config.global_directories:
                dirs.extend([
                    self.global_shared / "reference",
                    self.global_shared / "compliance",
                ])
        else:
            # Default bootstrap (backward compatibility)
            # Get today's date for temporal folders
            today = datetime.now().strftime("%Y-%m-%d")
            current_month = datetime.now().strftime("%Y-%m")
            
            dirs = [
                # Workspace
                self.agent_root / "workspace",
                
                # Memory - current (always loaded)
                self.agent_root / "memory" / "current",
                
                # Memory - recent (last 7 days)
                self.agent_root / "memory" / "recent" / today,
                
                # Memory - archive (monthly)
                self.agent_root / "memory" / "archive" / current_month,
                
                # Memory - timeless reference
                self.agent_root / "memory" / "entities" / "users",
                self.agent_root / "memory" / "entities" / "companies",
                self.agent_root / "memory" / "knowledge",
                
                # Legacy folders for compatibility
                self.agent_root / "memory" / "facts",
                self.agent_root / "memory" / "learnings",
                self.agent_root / "memory" / "history",
                
                # Users folder (parent for all user folders)
                self.agent_root / "users",
                
                # Teams folder (parent for all team folders)
                self.agent_root / "teams",
                
                # System folders
                self.agent_root / ".audit",
                self.agent_root / ".index",
                
                # Shared folders
                self.shared_path / "policies",
                self.shared_path / "knowledge",
                self.shared_path / "email_templates",
                self.shared_path / "integrations" / "databases",
                self.shared_path / "integrations" / "apis",
                self.global_shared / "reference",
                self.global_shared / "compliance",
                
                # Memory subdirectories for specific use cases
                self.agent_root / "memory" / "senders",
                self.agent_root / "memory" / "patterns",
            ]
        
        # Add current user's folder structure if user_id is set
        if self.user_id:
            user_folder = self.agent_root / "users" / self.user_id
            dirs.extend([
                user_folder,
                user_folder / "profile",
                user_folder / "preferences",
                user_folder / "data",
            ])
        
        # Add team folder if team_id is set
        if self.team_id:
            team_folder = self.agent_root / "teams" / self.team_id
            dirs.append(team_folder)
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
        
        # Create default user profile if it doesn't exist
        if self.user_id:
            profile_file = self.agent_root / "users" / self.user_id / "profile.md"
            if not profile_file.exists():
                profile_file.write_text(f"# User Profile\nID: {self.user_id}\nName: \nRole: \nTeam: {self.team_id or '(not set)'}\n")
    
    def _initialize_shared_memory_from_config(self):
        """Initialize shared memory from config/memory/shared/pipeline/{pipeline_id}/ if available.
        
        This copies template files from the project's config/memory/shared/pipeline/{pipeline_id}/ directory
        to the AgentOS data directory (data/agentos/{pipeline_id}/shared/) on first run.
        
        If templates are updated (newer than last initialization), files are re-copied.
        
        Also supports template_source from memory config for custom template locations.
        """
        if not self.pipeline_id or not self.project_dir:
            return
        
        # Check if memory config specifies template_source for shared directories
        template_source = None
        if self.memory_config:
            for dir_config in self.memory_config.shared_directories:
                if dir_config.template_source:
                    # Use explicit template_source from config
                    template_source = self.project_dir / dir_config.template_source
                    if template_source.exists():
                        self._copy_template_directory(template_source, self.shared_path, dir_config.path)
                        continue
        
        # Fallback to default location: config/memory/shared/pipeline/{pipeline_id}/
        if not template_source:
            template_source = self.project_dir / "config" / "memory" / "shared" / "pipeline" / self.pipeline_id
            if not template_source.exists():
                # Try old location for backward compatibility during migration
                old_location = self.project_dir / "config" / "shared" / self.pipeline_id
                if old_location.exists():
                    self.logger.warning("Using deprecated location: config/shared/. Please migrate to config/memory/shared/pipeline/")
                    template_source = old_location
                else:
                    self.logger.debug("No template files found at {}", template_source)
                    return
        
        if template_source.exists():
            self._copy_template_directory(template_source, self.shared_path, "/shared/")
    
    def _copy_template_directory(self, template_source: Path, dest_path: Path, virtual_path: str):
        """Copy template directory to destination, checking for updates."""
        if not template_source.exists():
            return
        
        init_marker = dest_path / ".initialized"
        
        # Check if we need to re-initialize (templates changed)
        needs_init = True
        if init_marker.exists():
            marker_mtime = init_marker.stat().st_mtime
            
            def has_newer_files(path: Path) -> bool:
                """Recursively check if any files are newer than marker."""
                try:
                    for item in path.iterdir():
                        if item.is_file():
                            if item.stat().st_mtime > marker_mtime:
                                return True
                        elif item.is_dir():
                            if has_newer_files(item):
                                return True
                except (OSError, PermissionError):
                    pass
                return False
            
            if not has_newer_files(template_source):
                self.logger.debug("Shared memory already initialized and templates unchanged for {}", virtual_path)
                needs_init = False
        
        if not needs_init:
            return
        
        # Copy template files to shared memory
        try:
            import shutil
            self.logger.info("Initializing shared memory from {} to {}", template_source, dest_path)
            
            # Ensure dest_path exists
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Copy all files and directories
            for item in template_source.iterdir():
                dest = dest_path / item.name
                if item.is_dir():
                    if dest.exists():
                        # Remove existing directory and copy fresh to ensure clean state
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    # Copy file (overwrites if exists)
                    shutil.copy2(item, dest)
            
            # Update marker file timestamp
            init_marker.touch()
            self.logger.success("Initialized shared memory for {} from templates", virtual_path)
        
        except Exception as e:
            self.logger.warning("Failed to initialize shared memory from config: {}", e)
        
        shared_path = self.shared_path
        init_marker = shared_path / ".initialized"
        
        # Check if we need to re-initialize (templates changed)
        needs_init = True
        if init_marker.exists():
            # Check if any template files are newer than the marker
            marker_mtime = init_marker.stat().st_mtime
            
            def has_newer_files(path: Path) -> bool:
                """Recursively check if any files are newer than marker."""
                try:
                    for item in path.iterdir():
                        if item.is_file():
                            if item.stat().st_mtime > marker_mtime:
                                return True
                        elif item.is_dir():
                            if has_newer_files(item):
                                return True
                except (OSError, PermissionError):
                    pass
                return False
            
            if not has_newer_files(template_source):
                self.logger.debug("Shared memory already initialized and templates unchanged for pipeline {}", self.pipeline_id)
                needs_init = False
        
        if not needs_init:
            return
        
        # Copy template files to shared memory
        try:
            import shutil
            self.logger.info("Initializing shared memory from {} to {}", template_source, shared_path)
            
            # Ensure shared_path exists
            shared_path.mkdir(parents=True, exist_ok=True)
            
            # Copy all files and directories
            # Use copytree with dirs_exist_ok to handle existing directories
            for item in template_source.iterdir():
                dest = shared_path / item.name
                if item.is_dir():
                    if dest.exists():
                        # Remove existing directory and copy fresh to ensure clean state
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    # Copy file (overwrites if exists)
                    shutil.copy2(item, dest)
            
            # Update marker file timestamp
            init_marker.touch()
            self.logger.success("Initialized shared memory for pipeline {} from templates", self.pipeline_id)
        
        except Exception as e:
            self.logger.warning("Failed to initialize shared memory from config: {}", e)
    
    def _initialize_global_memory_from_config(self):
        """Initialize global memory from config/memory/shared/global/ if available.
        
        This copies template files from the project's config/memory/shared/global/ directory
        to the AgentOS data directory (data/agentos/global_shared/) on first run.
        
        If templates are updated (newer than last initialization), files are re-copied.
        
        Also supports template_source from memory config for custom template locations.
        """
        if not self.project_dir:
            return
        
        # Check if memory config specifies template_source for global directories
        if self.memory_config:
            for dir_config in self.memory_config.global_directories:
                if dir_config.template_source:
                    # Use explicit template_source from config
                    template_source = self.project_dir / dir_config.template_source
                    if template_source.exists():
                        # Resolve the destination path for this global directory
                        # Extract the subdirectory from the virtual path (e.g., /global/reference/ -> reference)
                        subdir = dir_config.path.rstrip("/").replace("/global/", "").replace("/global", "")
                        if subdir:
                            dest_path = self.global_shared / subdir
                        else:
                            dest_path = self.global_shared
                        self._copy_template_directory(template_source, dest_path, dir_config.path)
                        continue
        
        # Fallback to default location: config/memory/shared/global/
        template_source = self.project_dir / "config" / "memory" / "shared" / "global"
        if template_source.exists():
            self._copy_template_directory(template_source, self.global_shared, "/global/")
    
    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a virtual path to a real path.
        
        Handles special prefixes:
        - /me/ -> current user's folder (shortcut for /users/{user_id}/)
        - /team/ -> team folder
        - /users/{id}/ -> specific user folder (RBAC checked)
        - /shared/ -> tenant shared directory
        - /global/ -> global shared directory
        - Everything else -> agent root
        """
        path = path.strip()
        
        # Block path traversal
        if ".." in path:
            raise SecurityError(
                "Error [PATH_ESCAPE]: Access denied. "
                "Cannot navigate outside your sandbox using '..'"
            )
        
        # Handle empty or current dir
        if not path or path == ".":
            return self._resolve_cwd()
        
        # Normalize the path
        if path.startswith("/"):
            virtual_path = path
        else:
            # Relative to CWD
            if self.cwd == "/":
                virtual_path = "/" + path
            else:
                virtual_path = self.cwd.rstrip("/") + "/" + path
        
        # Expand /me/ shortcut to /users/{user_id}/
        if virtual_path == "/me" or virtual_path.startswith("/me/"):
            if not self.user_id:
                raise SecurityError(
                    "Error [NO_USER]: /me/ path requires user_id to be set."
                )
            if virtual_path == "/me":
                virtual_path = f"/users/{self.user_id}"
            else:
                virtual_path = f"/users/{self.user_id}{virtual_path[3:]}"
        
        # Expand /team/ shortcut to /teams/{team_id}/
        if virtual_path == "/team" or virtual_path.startswith("/team/"):
            if not self.team_id:
                raise SecurityError(
                    "Error [NO_TEAM]: /team/ path requires team_id to be set."
                )
            if virtual_path == "/team":
                virtual_path = f"/teams/{self.team_id}"
            else:
                virtual_path = f"/teams/{self.team_id}{virtual_path[5:]}"
        
        # Check RBAC for /users/ paths
        if virtual_path.startswith("/users/"):
            self._check_user_access(virtual_path)
        
        # Route based on prefix using configurable mappings
        # Check path mappings in order (longest prefix first)
        sorted_prefixes = sorted(self.path_mappings.keys(), key=len, reverse=True)
        
        for prefix in sorted_prefixes:
            if virtual_path == prefix or virtual_path.startswith(prefix + "/"):
                mapping = self.path_mappings[prefix]
                if virtual_path == prefix:
                    return self.data_root / mapping.base
                else:
                    # Remove prefix and leading slash
                    remainder = virtual_path[len(prefix):].lstrip("/")
                    return (self.data_root / mapping.base) / remainder
        
        # Fallback: Agent's own directories (default behavior)
        remainder = virtual_path.lstrip("/")
        return self.agent_root / remainder
    
    def _check_user_access(self, virtual_path: str):
        """
        Check if current user can access this /users/ path.
        
        Raises:
            AccessDeniedError: If access is not allowed.
        """
        # If no user_id is set, RBAC is disabled - allow all
        if not self.user_id:
            return
        
        # Extract target user from path
        # /users/{target_user}/... -> target_user
        parts = virtual_path.split("/")
        if len(parts) < 3:
            return  # Just /users or /users/ - allow listing
        
        target_user = parts[2]
        
        # Admin can access everything
        if self.user_role == UserRole.ADMIN:
            return
        
        # Auditor can access everything (but writes are blocked elsewhere)
        if self.user_role == UserRole.AUDITOR:
            return
        
        # User accessing their own folder - always allowed
        if target_user == self.user_id:
            return
        
        # Manager can access team members' folders
        if self.user_role == UserRole.MANAGER:
            managed_users = self.team_resolver.get_managed_users(
                self.user_id, self.team_id
            )
            if target_user in managed_users:
                return
        
        # Access denied
        raise AccessDeniedError(
            f"Error [ACCESS_DENIED]: User '{self.user_id}' cannot access "
            f"'/users/{target_user}/'. You can only access your own folder at '/me/'."
        )
    
    def _is_user_write_allowed(self, virtual_path: str) -> bool:
        """
        Check if current user can write to this path.
        
        Auditors cannot write anywhere.
        Users can only write to their own folder.
        Managers can write to their folder and team folders.
        Admins can write anywhere.
        """
        # Auditors cannot write
        if self.user_role == UserRole.AUDITOR:
            return False
        
        # If no user_id set, skip user-level write checks
        if not self.user_id:
            return True
        
        # Check if writing to /users/ path
        if virtual_path.startswith("/users/"):
            parts = virtual_path.split("/")
            if len(parts) >= 3:
                target_user = parts[2]
                
                # Own folder - allowed
                if target_user == self.user_id:
                    return True
                
                # Admin - allowed
                if self.user_role == UserRole.ADMIN:
                    return True
                
                # Manager writing to team member - allowed
                if self.user_role == UserRole.MANAGER:
                    managed_users = self.team_resolver.get_managed_users(
                        self.user_id, self.team_id
                    )
                    if target_user in managed_users:
                        return True
                
                # Not allowed
                return False
        
        # Non-user paths use default write check
        return True
    
    def _resolve_cwd(self) -> Path:
        """Resolve current working directory."""
        if self.cwd == "/":
            return self.agent_root
        
        if self.cwd.startswith("/shared/"):
            remainder = self.cwd[8:]
            return self.shared_path / remainder
        elif self.cwd.startswith("/global/"):
            remainder = self.cwd[8:]
            return self.global_shared / remainder
        else:
            return self.agent_root / self.cwd.lstrip("/")
    
    def _to_virtual_path(self, real_path: Path) -> str:
        """Convert a real path back to virtual path."""
        real_path = Path(real_path).resolve()
        
        # Check which root it belongs to
        try:
            relative = real_path.relative_to(self.shared_path)
            return "/shared/" + str(relative)
        except ValueError:
            pass
        
        try:
            relative = real_path.relative_to(self.global_shared)
            return "/global/" + str(relative)
        except ValueError:
            pass
        
        try:
            relative = real_path.relative_to(self.agent_root)
            if str(relative) == ".":
                return "/"
            return "/" + str(relative)
        except ValueError:
            return str(real_path)
    
    def _is_writable(self, virtual_path: str) -> bool:
        """
        Check if a virtual path is writable.
        
        Combines:
        - System-level checks (shared/global directories based on config)
        - User-level RBAC checks
        """
        # Check shared directories against memory config
        if virtual_path.startswith("/shared/"):
            if self.memory_config:
                # Find matching shared directory config (prefer most specific match)
                best_match = None
                best_match_length = 0
                for dir_config in self.memory_config.shared_directories:
                    dir_path = dir_config.path.rstrip("/")
                    # Check if path matches this directory (exact match or subdirectory)
                    if virtual_path == dir_path or virtual_path.startswith(dir_path + "/"):
                        # Prefer longer (more specific) paths
                        if len(dir_path) > best_match_length:
                            best_match = dir_config
                            best_match_length = len(dir_path)
                
                if best_match:
                    # Found matching directory - check its readonly flag
                    if best_match.readonly:
                        return False
                    # Directory is writable according to config
                else:
                    # No matching config found - default to read-only for safety
                    return False
            else:
                # No memory config - default to read-only for safety
                return False
        elif virtual_path.startswith("/global/"):
            if self.memory_config:
                # Find matching global directory config (prefer most specific match)
                best_match = None
                best_match_length = 0
                for dir_config in self.memory_config.global_directories:
                    dir_path = dir_config.path.rstrip("/")
                    # Check if path matches this directory (exact match or subdirectory)
                    if virtual_path == dir_path or virtual_path.startswith(dir_path + "/"):
                        # Prefer longer (more specific) paths
                        if len(dir_path) > best_match_length:
                            best_match = dir_config
                            best_match_length = len(dir_path)
                
                if best_match:
                    # Found matching directory - check its readonly flag
                    if best_match.readonly:
                        return False
                    # Directory is writable according to config
                else:
                    # No matching config found - default to read-only for safety
                    return False
            else:
                # No memory config - default to read-only for safety
                return False
        
        # Check user-level write permissions
        if not self._is_user_write_allowed(virtual_path):
            return False
        
        return True
    
    def _get_audit_file_path(self, date: Optional[datetime] = None) -> Path:
        """Get the audit log file path for a specific date."""
        if date is None:
            date = datetime.now(timezone.utc)
        date_str = date.strftime("%Y-%m-%d")
        return self.agent_root / ".audit" / f"commands_{date_str}.jsonl"
    
    def _rotate_audit_logs(self):
        """
        Rotate and compress old audit logs.
        
        - Compress logs older than AUDIT_LOG_COMPRESS_AFTER_DAYS
        - Delete logs older than AUDIT_LOG_MAX_DAYS
        """
        audit_dir = self.agent_root / ".audit"
        if not audit_dir.exists():
            return
        
        now = datetime.now(timezone.utc)
        compress_threshold = now - timedelta(days=self.AUDIT_LOG_COMPRESS_AFTER_DAYS)
        delete_threshold = now - timedelta(days=self.AUDIT_LOG_MAX_DAYS)
        
        for log_file in audit_dir.glob("commands_*.jsonl"):
            # Extract date from filename
            try:
                date_str = log_file.stem.replace("commands_", "")
                log_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            
            # Delete old logs
            if log_date < delete_threshold:
                log_file.unlink(missing_ok=True)
                # Also delete compressed version
                gz_file = log_file.with_suffix(".jsonl.gz")
                if gz_file.exists():
                    gz_file.unlink()
                continue
            
            # Compress logs older than threshold
            if log_date < compress_threshold:
                gz_path = log_file.with_suffix(".jsonl.gz")
                if not gz_path.exists():
                    try:
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(gz_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        log_file.unlink()  # Remove original after compression
                    except Exception:
                        pass  # Silently fail compression
        
        # Also handle legacy commands.jsonl (no date suffix)
        legacy_log = audit_dir / "commands.jsonl"
        if legacy_log.exists():
            # Migrate to date-based naming
            try:
                today_log = self._get_audit_file_path()
                with open(legacy_log, 'r') as f_in:
                    with open(today_log, 'a') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                legacy_log.unlink()
            except Exception:
                pass
    
    def _log_command(self, command: str, result: str, success: bool, duration: float):
        """Log command to audit trail with file locking."""
        if not self.enable_audit_log:
            return
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "output_preview": result[:500] if result else "",
            "success": success,
            "duration_ms": int(duration * 1000)
        }
        
        audit_file = self._get_audit_file_path()
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Use file locking for thread safety
        lock = FileLock.get_lock(audit_file)
        with lock:
            with open(audit_file, "a") as f:
                # OS-level locking on Unix
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(json.dumps(log_entry) + "\n")
                finally:
                    if HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def run_shell_command(self, command: str, confirmed: bool = False) -> str:
        """
        Main entry point - execute a shell command.
        
        Args:
            command: The command string to execute.
            confirmed: If True, skip confirmation for write operations.
                      Set to True only after user explicitly approves.
            
        Returns:
            Command output as string.
        """
        start_time = time.time()
        command = command.strip()
        
        if not command:
            return "Error: Empty command."
        
        # Rate limiting check
        try:
            self.rate_limiter.check()
        except RateLimitExceeded as e:
            return str(e)
        
        # Periodic log rotation (check once per command, low overhead)
        try:
            self._rotate_audit_logs()
        except Exception:
            pass  # Don't fail command on rotation error
        
        try:
            result = self._execute(command, confirmed=confirmed)
            duration = time.time() - start_time
            self._log_command(command, result, True, duration)
            return result
        except SecurityError as e:
            duration = time.time() - start_time
            self._log_command(command, str(e), False, duration)
            return str(e)
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Error [INTERNAL]: {str(e)}"
            self._log_command(command, error_msg, False, duration)
            return error_msg
    
    # Legacy confirmation tag (kept for backward compatibility)
    CONFIRMATION_TAG = "# CONFIRMED"
    
    def _requires_confirmation(self, command: str, cmd: str, args: List[str], redirect: Optional[Dict], confirmed: bool = False) -> Optional[str]:
        """
        Check if a command requires user confirmation.
        
        Args:
            command: The full command string
            cmd: The parsed command name
            args: Command arguments
            redirect: Redirect info if present
            confirmed: If True, user has approved this operation
        
        Returns:
            None if no confirmation needed, or an error message asking for confirmation.
        """
        if not self.require_confirmation:
            return None
        
        # Already confirmed via parameter or legacy tag?
        if confirmed or self.CONFIRMATION_TAG in command:
            return None
        
        # Determine operation type
        operation = None
        target_path = None
        
        if redirect:  # echo "..." > file or echo "..." >> file
            operation = "write"
            target_path = redirect["target"]
        elif cmd == "rm":
            operation = "delete"
            target_path = args[0] if args else None
        elif cmd == "mkdir":
            operation = "mkdir"
            # Get path (skip -p flag)
            for arg in args:
                if not arg.startswith("-"):
                    target_path = arg
                    break
        elif cmd == "touch":
            operation = "write"
            target_path = args[0] if args else None
        
        # No operation needing confirmation
        if operation not in self.confirm_operations:
            return None
        
        # Check if path requires confirmation
        if self.confirm_paths and target_path:
            # Resolve to virtual path for checking
            if not target_path.startswith("/"):
                target_path = self.cwd.rstrip("/") + "/" + target_path
            
            # Check if any confirm_path matches
            path_matches = any(target_path.startswith(cp) for cp in self.confirm_paths)
            if not path_matches:
                return None
        
        # Build confirmation message
        return (
            f"⚠️ CONFIRMATION REQUIRED\n"
            f"Operation: {operation}\n"
            f"Target: {target_path or 'unknown'}\n"
            f"Command: {command}\n\n"
            f"Ask user for approval, then call again with confirmed=True"
        )
    
    def _execute(self, command: str, confirmed: bool = False) -> str:
        """Parse and execute a command."""
        # Parse the command (strip legacy confirmation tag before parsing)
        clean_command = command.replace(self.CONFIRMATION_TAG, "").strip()
        parsed = self._parse_command(clean_command)
        cmd = parsed["cmd"].lower()
        args = parsed["args"]
        redirect = parsed.get("redirect")
        
        # Check if blocked
        if cmd in self.BLOCKED_COMMANDS:
            return f"Error [COMMAND_BLOCKED]: '{cmd}' is disabled for safety."
        
        # Check if confirmation is required
        confirmation_msg = self._requires_confirmation(command, cmd, args, redirect, confirmed=confirmed)
        if confirmation_msg:
            return confirmation_msg
        
        # Route to handlers
        handlers = {
            "ls": self._cmd_ls,
            "dir": self._cmd_ls,
            "cd": self._cmd_cd,
            "pwd": self._cmd_pwd,
            "cat": self._cmd_cat,
            "head": self._cmd_head,
            "tail": self._cmd_tail,
            "grep": self._cmd_grep,
            "find": self._cmd_find,
            "mkdir": self._cmd_mkdir,
            "touch": self._cmd_touch,
            "echo": lambda a: self._cmd_echo(a, redirect),
            "semgrep": self._cmd_semgrep,
            "tree": self._cmd_tree,
            "wc": self._cmd_wc,
        }
        
        if cmd not in handlers:
            return f"Error [UNKNOWN_COMMAND]: '{cmd}' not recognized. Supported: {', '.join(sorted(handlers.keys()))}"
        
        return handlers[cmd](args)
    
    def _parse_command(self, command: str) -> Dict[str, Any]:
        """Parse a command string into components."""
        redirect = None
        
        # Block command chaining operators (security)
        # Check for dangerous operators ONLY outside quotes
        # This allows: echo "Hello; World" but blocks: ls; grep
        for op in self.DANGEROUS_OPERATORS:
            if self._has_unquoted_operator(command, op):
                raise SecurityError(
                    f"Error [COMMAND_INJECTION]: Command chaining with '{op}' is not allowed. "
                    "Run commands one at a time."
                )
        
        # Check for pipe character ONLY outside quotes
        # This allows: echo "Hello | World" but blocks: ls | grep
        if self._has_unquoted_pipe(command):
            raise SecurityError(
                f"Error [COMMAND_INJECTION]: Command chaining with '{self.PIPE_OPERATOR}' is not allowed. "
                "Run commands one at a time."
            )
        
        # Handle redirection (>> or >)
        if " >> " in command:
            parts = command.split(" >> ", 1)
            command = parts[0]
            redirect = {"target": parts[1].strip(), "append": True}
        elif " > " in command:
            parts = command.split(" > ", 1)
            command = parts[0]
            redirect = {"target": parts[1].strip(), "append": False}
        
        # Split respecting quotes
        tokens = self._tokenize(command)
        
        return {
            "cmd": tokens[0] if tokens else "",
            "args": tokens[1:],
            "redirect": redirect
        }
    
    def _tokenize(self, command: str) -> List[str]:
        """Tokenize command respecting quotes."""
        tokens = []
        current = ""
        in_quotes = False
        quote_char = None
        
        for char in command:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == " " and not in_quotes:
                if current:
                    tokens.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            tokens.append(current)
        
        return tokens
    
    def _has_unquoted_operator(self, command: str, operator: str) -> bool:
        """
        Check if command contains an operator outside quotes.
        
        Args:
            command: The command string to check
            operator: The operator to look for (e.g., ";", "&&", "||")
        
        Returns:
            True if operator is found outside quotes, False otherwise.
        """
        in_quotes = False
        quote_char = None
        i = 0
        
        while i < len(command):
            char = command[i]
            
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif not in_quotes:
                # Check if operator starts at this position
                if command[i:i+len(operator)] == operator:
                    return True
            
            i += 1
        
        return False
    
    def _has_unquoted_pipe(self, command: str) -> bool:
        """
        Check if command contains a pipe character outside quotes.
        
        Returns:
            True if pipe is found outside quotes, False otherwise.
        """
        return self._has_unquoted_operator(command, self.PIPE_OPERATOR)
    
    # =========================================================================
    # COMMAND IMPLEMENTATIONS
    # =========================================================================
    
    def _cmd_ls(self, args: List[str]) -> str:
        """List directory contents."""
        # Parse flags
        show_all = "-a" in args or "-la" in args or "-al" in args
        long_format = "-l" in args or "-la" in args or "-al" in args
        recursive = "-R" in args
        
        # Get path (first non-flag argument)
        path = "."
        for arg in args:
            if not arg.startswith("-"):
                path = arg
                break
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        if not resolved.exists():
            return f"Error [FILE_NOT_FOUND]: '{path}' does not exist."
        
        if not resolved.is_dir():
            return f"Error: '{path}' is not a directory."
        
        # List contents
        items = []
        try:
            for item in sorted(resolved.iterdir()):
                if not show_all and item.name.startswith("."):
                    continue
                
                if long_format:
                    stat = item.stat()
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%b %d %H:%M")
                    type_char = "d" if item.is_dir() else "-"
                    items.append(f"{type_char}rw-r--r--  {size:>8}  {mtime}  {item.name}")
                else:
                    suffix = "/" if item.is_dir() else ""
                    items.append(item.name + suffix)
                
                if len(items) >= self.MAX_LIST_ITEMS:
                    items.append(f"... (truncated, showing first {self.MAX_LIST_ITEMS} items)")
                    break
        except PermissionError:
            return f"Error [PERMISSION_DENIED]: Cannot read directory '{path}'."
        
        if not items:
            return "(empty directory)"
        
        return "\n".join(items)
    
    def _cmd_cd(self, args: List[str]) -> str:
        """Change current directory."""
        if not args:
            self.cwd = "/"
            return "Changed to /"
        
        path = args[0]
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        if not resolved.exists():
            return f"Error [FILE_NOT_FOUND]: Directory '{path}' does not exist."
        
        if not resolved.is_dir():
            return f"Error: '{path}' is not a directory."
        
        # Update CWD
        self.cwd = self._to_virtual_path(resolved)
        return f"Changed to {self.cwd}"
    
    def _cmd_pwd(self, args: List[str]) -> str:
        """Print working directory."""
        return self.cwd
    
    def _cmd_cat(self, args: List[str]) -> str:
        """Read file contents."""
        if not args:
            return "Error: cat requires a file path."
        
        path = args[0]
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        if not resolved.exists():
            return f"Error [FILE_NOT_FOUND]: File '{path}' does not exist.\nSuggestion: Use 'ls' to see available files."
        
        if not resolved.is_file():
            return f"Error: '{path}' is not a file."
        
        try:
            content = resolved.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return f"Error: '{path}' is not a text file."
        except PermissionError:
            return f"Error [PERMISSION_DENIED]: Cannot read file '{path}'."
        
        # Truncate if too large
        if len(content) > self.MAX_READ_BYTES:
            content = content[:self.MAX_READ_BYTES]
            content += f"\n\n... [OUTPUT TRUNCATED - File exceeds {self.MAX_READ_BYTES // 1024}KB. Use 'head', 'tail', or 'grep' to read specific sections.]"
        
        return content
    
    def _cmd_head(self, args: List[str]) -> str:
        """Read first N lines of a file."""
        # Parse -n flag
        n = 20  # default
        path = None
        
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                try:
                    n = min(int(args[i + 1]), self.MAX_READ_LINES)
                except ValueError:
                    pass
                i += 2
            elif not args[i].startswith("-"):
                path = args[i]
                i += 1
            else:
                i += 1
        
        if not path:
            return "Error: head requires a file path."
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        if not resolved.exists():
            return f"Error [FILE_NOT_FOUND]: File '{path}' does not exist."
        
        try:
            with open(resolved, "r", encoding="utf-8") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= n:
                        break
                    lines.append(line.rstrip())
            return "\n".join(lines)
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def _cmd_tail(self, args: List[str]) -> str:
        """Read last N lines of a file."""
        # Parse -n flag
        n = 20
        path = None
        
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                try:
                    n = min(int(args[i + 1]), self.MAX_READ_LINES)
                except ValueError:
                    pass
                i += 2
            elif not args[i].startswith("-"):
                path = args[i]
                i += 1
            else:
                i += 1
        
        if not path:
            return "Error: tail requires a file path."
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        if not resolved.exists():
            return f"Error [FILE_NOT_FOUND]: File '{path}' does not exist."
        
        try:
            with open(resolved, "r", encoding="utf-8") as f:
                lines = f.readlines()
            return "".join(lines[-n:]).rstrip()
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
    def _cmd_grep(self, args: List[str]) -> str:
        """Search for pattern in files."""
        # Parse flags
        recursive = "-r" in args or "-R" in args
        ignore_case = "-i" in args
        show_line_nums = "-n" in args
        
        # Extract pattern and path
        non_flag_args = [a for a in args if not a.startswith("-")]
        
        if len(non_flag_args) < 1:
            return "Error: grep requires a pattern. Usage: grep [-r] [-i] [-n] 'pattern' [path]"
        
        pattern = non_flag_args[0]
        path = non_flag_args[1] if len(non_flag_args) > 1 else "."
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        if not resolved.exists():
            return f"Error [FILE_NOT_FOUND]: '{path}' does not exist."
        
        # Compile regex
        flags = re.IGNORECASE if ignore_case else 0
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return f"Error: Invalid regex pattern: {str(e)}"
        
        results = []
        
        def search_file(file_path: Path, virtual_path: str):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if regex.search(line):
                            if show_line_nums:
                                results.append(f"{virtual_path}:{line_num}: {line.rstrip()}")
                            else:
                                results.append(f"{virtual_path}: {line.rstrip()}")
                            if len(results) >= self.MAX_GREP_RESULTS:
                                return True  # Stop
            except (UnicodeDecodeError, PermissionError):
                pass
            return False
        
        if resolved.is_file():
            search_file(resolved, path)
        elif recursive:
            for file_path in resolved.rglob("*"):
                if file_path.is_file():
                    virtual = self._to_virtual_path(file_path)
                    if search_file(file_path, virtual):
                        break
        else:
            for file_path in resolved.iterdir():
                if file_path.is_file():
                    virtual = self._to_virtual_path(file_path)
                    if search_file(file_path, virtual):
                        break
        
        if not results:
            return f"No matches found for '{pattern}'."
        
        output = "\n".join(results)
        if len(results) >= self.MAX_GREP_RESULTS:
            output += f"\n... (truncated at {self.MAX_GREP_RESULTS} results)"
        
        return output
    
    def _cmd_find(self, args: List[str]) -> str:
        """Find files by name pattern."""
        path = "."
        name_pattern = None
        
        i = 0
        while i < len(args):
            if args[i] == "-name" and i + 1 < len(args):
                name_pattern = args[i + 1]
                i += 2
            elif not args[i].startswith("-"):
                path = args[i]
                i += 1
            else:
                i += 1
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        if not resolved.exists():
            return f"Error [FILE_NOT_FOUND]: '{path}' does not exist."
        
        # Convert glob pattern
        if name_pattern:
            pattern = name_pattern
        else:
            pattern = "*"
        
        results = []
        for item in resolved.rglob(pattern):
            virtual = self._to_virtual_path(item)
            results.append(virtual)
            if len(results) >= self.MAX_FIND_RESULTS:
                break
        
        if not results:
            return "No files found."
        
        output = "\n".join(results)
        if len(results) >= self.MAX_FIND_RESULTS:
            output += f"\n... (truncated at {self.MAX_FIND_RESULTS} results)"
        
        return output
    
    def _cmd_mkdir(self, args: List[str]) -> str:
        """Create a directory. Supports -p flag for parents."""
        if not args:
            return "Error: mkdir requires a directory path."
        
        # Parse flags
        parents = False
        path = None
        for arg in args:
            if arg == "-p":
                parents = True
            elif not arg.startswith("-"):
                path = arg
        
        if not path:
            return "Error: mkdir requires a directory path."
        
        # Check if writable
        if not self._is_writable(path if path.startswith("/") else self.cwd + "/" + path):
            return f"Error [PERMISSION_DENIED]: Cannot create directory in read-only area."
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        if resolved.exists():
            return f"Directory '{path}' already exists."
        
        # If -p not specified and parent doesn't exist, error
        if not parents and not resolved.parent.exists():
            return f"Error: Parent directory does not exist. Use 'mkdir -p {path}' to create parents."
        
        resolved.mkdir(parents=True, exist_ok=True)
        return f"Created directory: {self._to_virtual_path(resolved)}"
    
    def _cmd_touch(self, args: List[str]) -> str:
        """Create an empty file."""
        if not args:
            return "Error: touch requires a file path."
        
        path = args[0]
        
        # Check if writable
        virtual_path = path if path.startswith("/") else (self.cwd.rstrip("/") + "/" + path)
        if not self._is_writable(virtual_path):
            return f"Error [PERMISSION_DENIED]: Cannot create file in read-only area."
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        # Create parent directories
        resolved.parent.mkdir(parents=True, exist_ok=True)
        
        # Touch the file
        resolved.touch()
        return f"Created: {self._to_virtual_path(resolved)}"
    
    def _cmd_echo(self, args: List[str], redirect: Optional[Dict]) -> str:
        """Echo text (with optional file redirection)."""
        content = " ".join(args)
        
        if not redirect:
            return content
        
        target = redirect["target"]
        append = redirect["append"]
        
        # Validate filename - no dangerous characters
        for char in self.INVALID_FILENAME_CHARS:
            if char in target:
                return f"Error [INVALID_FILENAME]: Filename cannot contain '{char}'. Use a simple filename like 'notes.txt'."
        
        # Build virtual path
        if target.startswith("/"):
            virtual_path = target
        else:
            virtual_path = self.cwd.rstrip("/") + "/" + target
        
        # Check write permission
        if not self._is_writable(virtual_path):
            return f"Error [PERMISSION_DENIED]: Cannot write to '{target}'. This directory is read-only."
        
        try:
            resolved = self._resolve_path(target)
        except SecurityError as e:
            return str(e)
        
        # Auto-validate and clean JSON content for .jsonl files
        if target.endswith(".jsonl") or target.endswith(".json"):
            content = self._clean_json_content(content)
            if content.startswith("Error"):
                return content  # Return error if JSON validation failed
        
        # Create parent directories
        resolved.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content with file locking
        mode = "a" if append else "w"
        lock = FileLock.get_lock(resolved)
        with lock:
            with open(resolved, mode, encoding="utf-8") as f:
                # OS-level locking on Unix
                if HAS_FCNTL:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(content + "\n")
                finally:
                    if HAS_FCNTL:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
        # AUTO-INDEX: If writing to /memory/, trigger vector indexing
        if "/memory/" in virtual_path:
            self._index_file(resolved)
            return f"Wrote to {virtual_path} (indexed to memory)"
        
        return f"Wrote to {virtual_path}"
    
    def _clean_json_content(self, content: str) -> str:
        """
        Clean and validate JSON content before writing.
        
        Handles common issues:
        - Removes escaped quotes that might cause parsing issues
        - Validates JSON structure
        - Ensures proper formatting for JSONL (single JSON object per line)
        
        Args:
            content: Raw content string that should be JSON
            
        Returns:
            Cleaned JSON string, or error message starting with "Error"
        """
        # Strip leading/trailing whitespace
        content = content.strip()
        
        # Remove any leading/trailing quotes that might have been added during command parsing
        # This handles cases where the content was quoted in the command
        if (content.startswith('"') and content.endswith('"')) or \
           (content.startswith("'") and content.endswith("'")):
            # Only remove outer quotes if they match
            if content[0] == content[-1]:
                content = content[1:-1]
        
        # Try to parse and re-serialize JSON to ensure it's valid
        # This also normalizes the format (removes extra whitespace, ensures proper escaping)
        try:
            # Parse the JSON
            parsed = json.loads(content)
            
            # Re-serialize to ensure proper formatting
            # Use ensure_ascii=False to preserve Unicode, compact separators for single-line JSONL
            cleaned = json.dumps(parsed, ensure_ascii=False, separators=(',', ':'))
            
            return cleaned
        except json.JSONDecodeError as e:
            # If JSON parsing fails, try to provide helpful error message
            error_msg = str(e)
            # Extract line/column info if available
            if hasattr(e, 'lineno') and hasattr(e, 'colno'):
                return f"Error [INVALID_JSON]: Invalid JSON format at line {e.lineno}, column {e.colno}: {error_msg}. Please ensure the JSON is properly formatted."
            else:
                return f"Error [INVALID_JSON]: Invalid JSON format: {error_msg}. Please ensure the JSON is properly formatted."
        except Exception as e:
            return f"Error [JSON_PROCESSING]: Failed to process JSON content: {str(e)}"
    
    def _cmd_semgrep(self, args: List[str]) -> str:
        """
        Semantic grep - search by meaning, not exact text.
        
        Usage: semgrep "natural language query" [path]
        """
        if not args:
            return "Error: semgrep requires a query. Usage: semgrep 'concept to find' [path]"
        
        query = args[0]
        path_prefix = None
        
        if len(args) > 1:
            path = args[1]
            try:
                resolved = self._resolve_path(path)
                path_prefix = str(resolved)
            except SecurityError:
                pass
        
        # Search vector store
        results = self.vector_store.search(query, path_prefix=path_prefix, top_k=10)
        
        if not results:
            return f"semgrep: No conceptually similar content found for '{query}'.\nSuggestion: Try 'grep' for exact text matches, or write more content to /memory/."
        
        # Format like grep output
        lines = []
        for r in results:
            virtual_path = self._to_virtual_path(Path(r.path))
            score_pct = int(r.score * 100)
            lines.append(f"{virtual_path} [{score_pct}% match]: {r.snippet}")
        
        return "\n".join(lines)
    
    def _cmd_tree(self, args: List[str]) -> str:
        """Display directory tree."""
        path = args[0] if args else "."
        max_depth = 3
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        if not resolved.exists():
            return f"Error [FILE_NOT_FOUND]: '{path}' does not exist."
        
        lines = [self._to_virtual_path(resolved)]
        
        def add_tree(dir_path: Path, prefix: str, depth: int):
            if depth > max_depth:
                return
            
            try:
                items = sorted(dir_path.iterdir())
            except PermissionError:
                return
            
            for i, item in enumerate(items):
                if item.name.startswith("."):
                    continue
                
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{item.name}")
                
                if item.is_dir():
                    extension = "    " if is_last else "│   "
                    add_tree(item, prefix + extension, depth + 1)
        
        add_tree(resolved, "", 1)
        return "\n".join(lines)
    
    def _cmd_wc(self, args: List[str]) -> str:
        """Count lines, words, characters."""
        if not args:
            return "Error: wc requires a file path."
        
        path = args[-1]  # Last non-flag arg
        
        try:
            resolved = self._resolve_path(path)
        except SecurityError as e:
            return str(e)
        
        if not resolved.exists():
            return f"Error [FILE_NOT_FOUND]: File '{path}' does not exist."
        
        try:
            content = resolved.read_text(encoding="utf-8")
        except:
            return f"Error reading file."
        
        lines = content.count("\n")
        words = len(content.split())
        chars = len(content)
        
        return f"  {lines}  {words}  {chars} {path}"
    
    def _index_file(self, file_path: Path):
        """Add or update a file in the vector index."""
        try:
            content = file_path.read_text(encoding="utf-8")
            self.vector_store.upsert(
                path=str(file_path),
                content=content,
                metadata={
                    "virtual_path": self._to_virtual_path(file_path),
                    "indexed_at": datetime.now(timezone.utc).isoformat()
                }
            )
        except Exception:
            pass  # Silently fail indexing
