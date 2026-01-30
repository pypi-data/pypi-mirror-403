"""
File watcher trigger handler using watchdog library.
"""

import asyncio
import fnmatch
import inspect
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent, FileMovedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from topaz_agent_kit.core.triggers.base import BaseTriggerHandler
from topaz_agent_kit.core.triggers.event import TriggerEvent
from topaz_agent_kit.core.triggers.registry import TriggerRegistry
from topaz_agent_kit.utils.logger import Logger


class FileWatcherEventHandler(FileSystemEventHandler):
    """Handles file system events for file watcher trigger."""
    
    def __init__(
        self,
        handler: "FileWatcherTriggerHandler",
        file_patterns: List[str],
        event_types: List[str],
        exclude_directories: List[str],
        exclude_patterns: List[str],
    ):
        self.handler = handler
        self.file_patterns = file_patterns
        self.event_types = event_types
        self.exclude_directories = exclude_directories
        self.exclude_patterns = exclude_patterns
    
    def _should_process(self, event: Any, event_type: str) -> bool:
        """Check if event should be processed."""
        if event.is_directory:
            return False
        
        if event_type not in self.event_types:
            return False
        
        # Get file path relative to watch directory
        file_path = Path(event.src_path)
        filename = file_path.name
        
        # Check if file is in an excluded directory
        # exclude_directories are relative to each watch_directory
        # Example: watch_directories: ["data/covenant/pre_contract", "data/covenant/draft_contracts"]
        #          exclude_directories: ["reports"]
        #          This will exclude: data/covenant/pre_contract/reports/* and data/covenant/draft_contracts/reports/*
        if self.exclude_directories:
            # Get relative path from the watch directory that contains this file
            rel_path = None
            for watch_path in self.handler.watch_paths:
                try:
                    rel_path = file_path.relative_to(watch_path)
                    break
                except ValueError:
                    continue
            
            if rel_path is None:
                # File is outside all watch directories, skip
                return False
            
            # Check each path component against exclude patterns
            # exclude_directories are relative to the watch_directory
            path_parts = rel_path.parts
            for exclude_dir in self.exclude_directories:
                # Check if any directory in the path matches the exclude pattern
                # path_parts[:-1] excludes the filename, leaving only directory parts
                for part in path_parts[:-1]:
                    if fnmatch.fnmatch(part, exclude_dir):
                        return False
                # Also check if any parent directory path matches (for patterns like "*/reports")
                for i in range(len(path_parts) - 1):
                    parent_path = "/".join(path_parts[:i+1])
                    if fnmatch.fnmatch(parent_path, exclude_dir):
                        return False
        
        # Check if file matches exclude patterns
        if self.exclude_patterns:
            if any(fnmatch.fnmatch(filename, pattern) for pattern in self.exclude_patterns):
                return False
            # Also check full relative path from any watch directory
            for watch_path in self.handler.watch_paths:
                try:
                    rel_path = file_path.relative_to(watch_path)
                    if any(fnmatch.fnmatch(str(rel_path), pattern) for pattern in self.exclude_patterns):
                        return False
                    break
                except ValueError:
                    continue
        
        # Check file pattern match (inclusion)
        if not any(
            fnmatch.fnmatch(filename, pattern) for pattern in self.file_patterns
        ):
            return False
        
        return True
    
    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation event."""
        if self._should_process(event, "created"):
            self.handler._handle_event(event)
    
    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification event."""
        if self._should_process(event, "modified"):
            self.handler._handle_event(event)
    
    def on_deleted(self, event: FileDeletedEvent) -> None:
        """Handle file deletion event."""
        if self._should_process(event, "deleted"):
            self.handler._handle_event(event)
    
    def on_moved(self, event: FileMovedEvent) -> None:
        """Handle file move/rename event."""
        if self._should_process(event, "moved"):
            self.handler._handle_event(event)


class FileWatcherTriggerHandler(BaseTriggerHandler):
    """
    File watcher trigger handler.
    
    Monitors a directory for file system events and triggers pipeline execution.
    Supports debouncing to batch multiple file events within a time window.
    """
    
    def __init__(self, pipeline_id: str, config: Dict[str, Any], logger: Logger, project_dir: Optional[Path] = None):
        super().__init__(pipeline_id, config, logger)
        
        # Extract file_watcher specific config
        # Support new grouped structure and old flat structure (backward compatibility)
        self.project_dir = project_dir or Path.cwd()
        
        # Extract directories configuration (new grouped structure or old flat structure)
        directories_config = config.get("directories", {})
        if directories_config:
            # New grouped structure: directories.watch and directories.exclude
            watch_directories = directories_config.get("watch")
            exclude_directories = directories_config.get("exclude", [])
        else:
            # Old flat structure (backward compatibility)
            watch_directories = config.get("watch_directories")
            if not watch_directories:
                # Backward compatibility: check for watch_directory
                watch_directory = config.get("watch_directory")
                if watch_directory:
                    self.logger.warning(
                        "watch_directory is deprecated, use directories.watch instead (pipeline: {})",
                        self.pipeline_id
                    )
                    watch_directories = watch_directory
                else:
                    raise ValueError("directories.watch or watch_directories is required for file_watcher trigger")
            exclude_directories = config.get("exclude_directories", [])
        
        # Normalize watch_directories to list (support single string for convenience)
        if isinstance(watch_directories, str):
            self.watch_directories = [watch_directories]
        elif isinstance(watch_directories, list):
            if not watch_directories:
                raise ValueError("watch_directories cannot be an empty list")
            self.watch_directories = watch_directories
        else:
            raise ValueError("watch_directories must be a string or list of strings")
        
        # Extract files configuration (new grouped structure or old flat structure)
        files_config = config.get("files", {})
        if files_config:
            # New grouped structure: files.include and files.exclude
            file_patterns = files_config.get("include", ["*"])
            exclude_patterns = files_config.get("exclude", [])
        else:
            # Old flat structure (backward compatibility)
            file_patterns = config.get("file_patterns", ["*"])
            exclude_patterns = config.get("exclude_patterns", [])
        
        # Add default system file exclusions (always exclude common system files)
        default_system_excludes = [
            ".DS_Store",  # macOS Finder metadata
            ".DS_Store?",  # macOS Finder metadata (with query string)
            "._*",  # macOS resource fork files
            "Thumbs.db",  # Windows thumbnail cache
            "desktop.ini",  # Windows folder settings
            "*.swp",  # Vim swap files
            "*.tmp",  # Temporary files
            "*.bak",  # Backup files
            ".git/*",  # Git metadata
            ".gitignore",  # Git ignore file (if watching root)
        ]
        
        # Merge user excludes with default system excludes (user excludes take precedence)
        # Use a set to deduplicate, then convert back to list
        all_exclude_patterns = list(set(exclude_patterns + default_system_excludes))
        
        self.file_patterns = file_patterns
        self.exclude_directories = exclude_directories
        self.exclude_patterns = all_exclude_patterns
        self.event_types = config.get("event_types", ["created"])
        
        # Trigger mode configuration
        # "single": Trigger immediately for each file event (no batching)
        # "batch": Batch multiple file events within time window, trigger once
        # "directory": When triggered, collect all files in the directory (orchestrator handles this)
        self.trigger_mode = config.get("trigger_mode", "single")
        self.debounce_seconds = config.get("debounce_seconds", 2.0)
        
        # Backward compatibility: if batch_events is set, use it to determine mode
        if "batch_events" in config:
            self.batch_events = config.get("batch_events", True)
            if self.batch_events and self.trigger_mode == "single":
                self.trigger_mode = "batch"
        else:
            # Determine batch_events from trigger_mode
            self.batch_events = self.trigger_mode in ("batch", "directory")
        
        self.observers: List[Observer] = []
        self.watch_paths: List[Path] = []
        
        # Debouncing state (lock will be created in _start_impl when event loop is available)
        self._pending_events: List[TriggerEvent] = []
        self._debounce_task: Optional[asyncio.Task] = None
        self._debounce_lock: Optional[asyncio.Lock] = None
    
    async def _start_impl(self) -> None:
        """Start watching directories for file events."""
        # Initialize debounce lock (requires async context)
        self._debounce_lock = asyncio.Lock()
        
        # Create event handler (shared across all watch directories)
        event_handler = FileWatcherEventHandler(
            self, self.file_patterns, self.event_types,
            self.exclude_directories, self.exclude_patterns
        )
        
        # Watch all specified directories
        for watch_dir_str in self.watch_directories:
            # Resolve watch directory (relative to project_dir)
            watch_dir = Path(watch_dir_str)
            if not watch_dir.is_absolute():
                watch_path = self.project_dir / watch_dir
            else:
                watch_path = watch_dir
            
            if not watch_path.exists():
                self.logger.warning(
                    "Watch directory does not exist: {}. Creating it.",
                    watch_path
                )
                watch_path.mkdir(parents=True, exist_ok=True)
            
            if not watch_path.is_dir():
                raise ValueError(f"watch_directory must be a directory: {watch_path}")
            
            # Create and start observer for this directory
            observer = Observer()
            observer.schedule(event_handler, str(watch_path), recursive=True)
            observer.start()
            
            self.observers.append(observer)
            self.watch_paths.append(watch_path)
        
        # Log success with all watched directories
        dirs_str = ", ".join(str(p) for p in self.watch_paths)
        self.logger.success(
            "Started file watcher for pipeline {} watching {} directory(ies): {} (trigger_mode: {}, debounce: {}s)",
            self.pipeline_id, len(self.watch_paths), dirs_str, self.trigger_mode, self.debounce_seconds if self.batch_events else 0
        )
    
    async def stop(self) -> None:
        """Stop watching directories."""
        # Cancel any pending debounce task
        if self._debounce_task and not self._debounce_task.done():
            self._debounce_task.cancel()
            try:
                await self._debounce_task
            except asyncio.CancelledError:
                pass
        
        # Trigger any pending events before stopping
        if self._debounce_lock:
            async with self._debounce_lock:
                if self._pending_events:
                    self.logger.info(
                        "Triggering {} pending events before stopping file watcher for pipeline {}",
                        len(self._pending_events), self.pipeline_id
                    )
                    # Trigger with the latest event
                    latest_event = self._pending_events[-1]
                    self._pending_events.clear()
                    self._trigger_callback(latest_event)
        
        # Stop all observers
        for observer in self.observers:
            observer.stop()
            observer.join(timeout=5.0)
        
        self.observers.clear()
        self.watch_paths.clear()
        self.logger.info("Stopped file watcher for pipeline {}", self.pipeline_id)
    
    def _handle_event(self, raw_event: Any) -> None:
        """
        Internal method to handle raw events with debouncing support.
        
        Normalizes the event and either batches it (if debouncing enabled)
        or calls the callback immediately.
        
        Args:
            raw_event: Raw event from trigger source
        """
        try:
            normalized_event = self.normalize_event(raw_event)
            if not self._callback:
                return
            
            # If debouncing is disabled, trigger immediately
            if not self.batch_events:
                self._trigger_callback(normalized_event)
                return
            
            # Batch events for debouncing
            if self._event_loop and self._event_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._handle_batched_event(normalized_event),
                    self._event_loop
                )
            else:
                # No event loop available, trigger immediately
                self.logger.warning(
                    "No event loop available for debouncing in pipeline {}, triggering immediately",
                    self.pipeline_id
                )
                self._trigger_callback(normalized_event)
        except Exception as e:
            self.logger.error(
                "Error handling trigger event for pipeline {}: {}",
                self.pipeline_id, e
            )
    
    async def _handle_batched_event(self, event: TriggerEvent) -> None:
        """
        Handle event with debouncing - batch events within time window.
        
        Args:
            event: Normalized trigger event
        """
        if not self._debounce_lock:
            # Lock not initialized yet, trigger immediately
            self._trigger_callback(event)
            return
        
        async with self._debounce_lock:
            # Add event to pending batch
            self._pending_events.append(event)
            
            # Cancel existing debounce task if any
            if self._debounce_task and not self._debounce_task.done():
                self._debounce_task.cancel()
            
            # Schedule new debounce task
            self._debounce_task = asyncio.create_task(self._debounce_trigger())
    
    async def _debounce_trigger(self) -> None:
        """
        Wait for debounce period, then trigger callback with batched events.
        """
        try:
            await asyncio.sleep(self.debounce_seconds)
            
            async with self._debounce_lock:
                if not self._pending_events:
                    return
                
                # Get all pending events
                events = self._pending_events.copy()
                self._pending_events.clear()
                self._debounce_task = None
                
                # For batch mode, include all file paths in the event metadata
                # Use the most recent event as the primary trigger event
                if events:
                    latest_event = events[-1]
                    
                    # Collect all unique file paths from all debounced events
                    # Use a set to deduplicate (same file might trigger multiple events: created + modified)
                    all_file_paths_set = set()
                    for event in events:
                        if event.event_type != "deleted":
                            file_path = Path(event.source)
                            if file_path.exists():
                                # Filter out system files (should already be filtered by _should_process, but double-check)
                                filename = file_path.name
                                system_files = {".DS_Store", ".DS_Store?", "Thumbs.db", "desktop.ini"}
                                if filename not in system_files and not filename.startswith("._"):
                                    all_file_paths_set.add(str(file_path))
                    
                    # Convert to sorted list for consistent ordering
                    all_file_paths = sorted(list(all_file_paths_set))
                    
                    # Add all file paths to metadata (even if single file, for consistency)
                    latest_event.metadata["batched_file_paths"] = all_file_paths
                    latest_event.metadata["batched_event_count"] = len(events)
                    
                    if len(all_file_paths) > 1:
                        self.logger.info(
                            "Debounced {} file event(s) for pipeline {}, triggering with {} unique file(s): {}",
                            len(events), self.pipeline_id, len(all_file_paths), 
                            ", ".join(Path(p).name for p in all_file_paths[:5]) + 
                            (f" ... (+{len(all_file_paths)-5} more)" if len(all_file_paths) > 5 else "")
                        )
                    elif len(all_file_paths) == 1:
                        self.logger.info(
                            "Debounced {} file event(s) for pipeline {}, triggering with file: {}",
                            len(events), self.pipeline_id, Path(all_file_paths[0]).name
                        )
                    else:
                        # All events were deleted or files don't exist
                        self.logger.warning(
                            "Debounced {} file event(s) for pipeline {}, but no valid files found",
                            len(events), self.pipeline_id
                        )
                    
                    self._trigger_callback(latest_event)
        except asyncio.CancelledError:
            # Task was cancelled (new event came in), this is expected
            pass
        except Exception as e:
            self.logger.error(
                "Error in debounce trigger for pipeline {}: {}",
                self.pipeline_id, e
            )
    
    def _trigger_callback(self, event: TriggerEvent) -> None:
        """
        Trigger the callback with an event.
        
        Args:
            event: Normalized trigger event
        """
        if not self._callback:
            return
        
        # Check if callback is async
        if inspect.iscoroutinefunction(self._callback):
            # Async callback - schedule it in the event loop
            if self._event_loop and self._event_loop.is_running():
                # Schedule in the running event loop
                asyncio.run_coroutine_threadsafe(
                    self._callback(event),
                    self._event_loop
                )
            else:
                # No event loop available, log error
                self.logger.error(
                    "Cannot execute async callback for pipeline {}: no event loop available",
                    self.pipeline_id
                )
        else:
            # Sync callback - call directly
            self._callback(event)
    
    def normalize_event(self, raw_event: Any) -> TriggerEvent:
        """
        Convert watchdog event to normalized TriggerEvent.
        
        Args:
            raw_event: Watchdog FileSystemEvent
            
        Returns:
            Normalized TriggerEvent
        """
        # Determine event type and file path
        if isinstance(raw_event, FileCreatedEvent):
            event_type = "created"
            file_path = Path(raw_event.src_path)
        elif isinstance(raw_event, FileModifiedEvent):
            event_type = "modified"
            file_path = Path(raw_event.src_path)
        elif isinstance(raw_event, FileDeletedEvent):
            event_type = "deleted"
            # For deleted events, file no longer exists, use src_path
            file_path = Path(raw_event.src_path)
        elif isinstance(raw_event, FileMovedEvent):
            event_type = "moved"
            # For moved events, use destination path as primary
            file_path = Path(raw_event.dest_path)
        else:
            event_type = "unknown"
            file_path = Path(raw_event.src_path)
        
        # Build metadata
        try:
            # For deleted events, file won't exist
            if event_type == "deleted":
                file_size = 0
            else:
                file_size = file_path.stat().st_size if file_path.exists() else 0
        except (OSError, FileNotFoundError):
            file_size = 0
        
        metadata = {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "file_size": file_size,
        }
        
        # Add destination for moved events
        if isinstance(raw_event, FileMovedEvent):
            metadata["source_path"] = str(raw_event.src_path)
            metadata["dest_path"] = str(raw_event.dest_path)
        
        return TriggerEvent(
            trigger_type="file_watcher",
            event_type=event_type,
            source=str(file_path),
            metadata=metadata,
            raw_event=raw_event,
        )


# Register file_watcher handler
TriggerRegistry.register("file_watcher", FileWatcherTriggerHandler)
