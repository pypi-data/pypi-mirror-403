"""
Trigger manager for orchestrating all pipeline triggers.
"""

import asyncio
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from jinja2 import Template

from topaz_agent_kit.core.ag_ui_event_emitter import AGUIEventEmitter
from topaz_agent_kit.core.triggers.base import BaseTriggerHandler
from topaz_agent_kit.core.triggers.event import TriggerEvent
from topaz_agent_kit.core.triggers.registry import TriggerRegistry
from topaz_agent_kit.orchestration.assistant import Assistant
from topaz_agent_kit.services.ag_ui_service import AGUIService
from topaz_agent_kit.utils.logger import Logger


class TriggerManager:
    """
    Manages all trigger handlers for pipelines.
    
    Loads pipeline configurations, creates trigger handlers, and coordinates
    event processing and pipeline execution.
    """
    
    def __init__(
        self,
        orchestrator: Any,  # Orchestrator instance
        project_dir: str,
        pipeline_configs: Dict[str, Dict[str, Any]],
        setup_emitter_fn: Optional[Callable[[str], Tuple[Any, Any, Any]]] = None,
    ):
        """
        Initialize trigger manager.
        
        Args:
            orchestrator: Orchestrator instance for executing pipelines
            project_dir: Project directory path
            pipeline_configs: Dict mapping pipeline_id to pipeline config
            setup_emitter_fn: Optional function to set up emitter infrastructure for a session
                            Returns (emitter, agui_service, queue) tuple
                            If provided, events will be sent to frontend via SSE
        """
        self.orchestrator = orchestrator
        self.project_dir = Path(project_dir)
        self.pipeline_configs = pipeline_configs
        self.logger = Logger("TriggerManager")
        self.setup_emitter_fn = setup_emitter_fn
        
        # Store handlers - can be single handler or list of handlers per pipeline
        self.handlers: Dict[str, BaseTriggerHandler | List[BaseTriggerHandler]] = {}
        # Mapping for per_pipeline strategy: pipeline_id -> session_id
        self._pipeline_session_map: Dict[str, str] = {}
    
    async def start(self) -> None:
        """Start all configured triggers."""
        self.logger.info("Starting trigger manager")
        
        for pipeline_id, config in self.pipeline_configs.items():
            event_triggers = config.get("event_triggers")
            if not event_triggers:
                continue
            
            # Support both single trigger config and list of trigger configs
            trigger_configs = []
            if isinstance(event_triggers, list):
                # Multiple trigger configurations
                trigger_configs = event_triggers
            elif isinstance(event_triggers, dict):
                # Single trigger configuration (backward compatibility)
                trigger_configs = [event_triggers]
            else:
                self.logger.warning(
                    "Pipeline {} has invalid event_triggers format (expected dict or list)",
                    pipeline_id
                )
                continue
            
            pipeline_handlers = []
            for idx, trigger_config in enumerate(trigger_configs):
                trigger_type = trigger_config.get("type")
                if not trigger_type:
                    self.logger.warning(
                        "Pipeline {} trigger config {} has no type specified",
                        pipeline_id, idx
                    )
                    continue
                
                try:
                    # Create handler instance
                    handler = TriggerRegistry.get_handler(
                        trigger_type=trigger_type,
                        pipeline_id=pipeline_id,
                        config=trigger_config,
                        logger=self.logger,
                        project_dir=self.project_dir,
                    )
                    
                    # Set up callback for this pipeline and trigger config
                    callback = self._create_callback(pipeline_id, trigger_config)
                    
                    # Start handler
                    await handler.start(callback)
                    
                    pipeline_handlers.append(handler)
                    
                    self.logger.success(
                        "Started {} trigger {} for pipeline {}",
                        trigger_type, idx + 1 if len(trigger_configs) > 1 else "", pipeline_id
                    )
                except Exception as e:
                    self.logger.error(
                        "Failed to start trigger {} for pipeline {}: {}",
                        idx + 1 if len(trigger_configs) > 1 else "", pipeline_id, e
                    )
            
            # Store handlers (single handler or list)
            if len(pipeline_handlers) == 1:
                self.handlers[pipeline_id] = pipeline_handlers[0]
            elif len(pipeline_handlers) > 1:
                self.handlers[pipeline_id] = pipeline_handlers
    
    async def stop(self) -> None:
        """Stop all triggers."""
        self.logger.info("Stopping trigger manager")
        
        for pipeline_id, handler_or_handlers in self.handlers.items():
            try:
                # Handle both single handler and list of handlers
                if isinstance(handler_or_handlers, list):
                    for handler in handler_or_handlers:
                        await handler.stop()
                else:
                    await handler_or_handlers.stop()
            except Exception as e:
                self.logger.error(
                    "Error stopping trigger for pipeline {}: {}",
                    pipeline_id, e
                )
        
        self.handlers.clear()
    
    def _create_callback(
        self, pipeline_id: str, event_triggers: Dict[str, Any]
    ) -> Callable[[TriggerEvent], None]:
        """
        Create callback function for handling trigger events.
        
        Args:
            pipeline_id: Pipeline ID
            event_triggers: Event triggers configuration
            
        Returns:
            Callback function
        """
        extract_config = event_triggers.get("extract_context", {})
        user_text_template_str = extract_config.get(
            "user_text_template", "Process file: {{source}}"
        )
        session_strategy = event_triggers.get("session_strategy", "per_file")
        ui_mode = event_triggers.get("ui_mode", "background")
        pass_files_as_uploads = event_triggers.get("pass_files_as_uploads", False)  # Default False - files are passed via user_text_template instead
        
        async def callback(event: TriggerEvent) -> None:
            """Handle trigger event and execute pipeline."""
            try:
                # Build user_text from template
                template = Template(user_text_template_str)
                
                # Prepare file paths list for template context
                file_paths_list = []
                if event.trigger_type == "file_watcher" and event.event_type != "deleted":
                    batched_paths = event.metadata.get("batched_file_paths")
                    if batched_paths:
                        file_paths_list = batched_paths
                    else:
                        file_path = Path(event.source)
                        if file_path.exists():
                            file_paths_list = [str(file_path)]
                    
                    # Filter out system files (safety check - should already be filtered by file watcher)
                    def _is_system_file(file_path_str: str) -> bool:
                        """Check if file is a system file that should be excluded."""
                        path = Path(file_path_str)
                        filename = path.name
                        # Common system files to exclude
                        system_patterns = [
                            ".DS_Store",
                            ".DS_Store?",
                            "Thumbs.db",
                            "desktop.ini",
                        ]
                        # Check exact matches
                        if filename in system_patterns:
                            return True
                        # Check patterns
                        if filename.startswith("._"):
                            return True
                        if filename.endswith((".swp", ".tmp", ".bak")):
                            return True
                        return False
                    
                    # Filter out system files
                    file_paths_list = [
                        fp for fp in file_paths_list 
                        if not _is_system_file(fp)
                    ]
                
                # Determine folder path (parent directory of the file)
                file_path_obj = Path(event.source)
                folder_path = str(file_path_obj.parent) if file_path_obj.parent else ""
                
                # For batched events, use the common parent directory if all files are in the same folder
                if file_paths_list and len(file_paths_list) > 1:
                    # Find common parent directory
                    batched_paths_objs = [Path(p) for p in file_paths_list]
                    # Get all parent directories
                    parents = [p.parent for p in batched_paths_objs]
                    # Find the longest common path
                    if parents:
                        common_parts = []
                        for parts in zip(*[p.parts for p in parents]):
                            if len(set(parts)) == 1:
                                common_parts.append(parts[0])
                            else:
                                break
                        if common_parts:
                            folder_path = str(Path(*common_parts))
                        else:
                            # No common parent, use the first file's parent
                            folder_path = str(batched_paths_objs[0].parent)
                
                # Build template context with file information
                context = {
                    "source": event.source,
                    "file_path": event.source,  # Alias for file_watcher (primary file or latest in batch)
                    "file_name": event.metadata.get("file_name", ""),
                    "folder_path": folder_path,  # Parent directory of file(s)
                    "event_type": event.event_type,
                    "file_count": len(file_paths_list),  # Number of files in batch
                    "file_paths": file_paths_list,  # List of all file paths for template
                    **event.metadata,  # Include all metadata
                }
                user_text = template.render(**context)
                
                # Determine session ID
                session_id = self._determine_session_id(
                    pipeline_id, event, session_strategy
                )
                
                # Determine user_files based on pass_files_as_uploads flag
                user_files = []
                if pass_files_as_uploads and event.trigger_type == "file_watcher" and event.event_type != "deleted":
                    # Pass files as uploads (for frameworks that need multimodal input)
                    user_files = file_paths_list
                    if user_files:
                        self.logger.info(
                            "Triggering pipeline {} with {} file(s) as uploads from {} events",
                            pipeline_id, len(user_files), event.metadata.get("batched_event_count", 1)
                        )
                else:
                    # Files are only referenced in user_text_template, not passed as uploads
                    # Agent will use tools to read files from disk
                    if file_paths_list:
                        self.logger.info(
                            "Triggering pipeline {} with {} file(s) referenced in user_text (not as uploads)",
                            pipeline_id, len(file_paths_list)
                        )
                
                # Execute pipeline
                self.logger.info(
                    "Triggering pipeline {} from {} event: {} (ui_mode: {}, session_strategy: {})",
                    pipeline_id, event.trigger_type, event.source, ui_mode, session_strategy
                )
                
                # Execute in background task to avoid blocking
                asyncio.create_task(
                    self._execute_pipeline(
                        pipeline_id, user_text, user_files, session_id, ui_mode, session_strategy
                    )
                )
            except Exception as e:
                self.logger.error(
                    "Error in trigger callback for pipeline {}: {}",
                    pipeline_id, e
                )
        
        return callback
    
    def _determine_session_id(
        self, pipeline_id: str, event: TriggerEvent, strategy: str
    ) -> Optional[str]:
        """
        Determine session ID based on session strategy.
        
        Args:
            pipeline_id: Pipeline ID
            event: Trigger event
            strategy: Session strategy ("per_file", "per_pipeline", "use_current", "custom")
            
        Returns:
            Session ID string, or None if "use_current" and no active session exists
        """
        if strategy == "use_current":
            # Use the most recent active session
            try:
                sessions = self.orchestrator.get_all_sessions(status="active")
                if sessions:
                    # Sort by last_accessed (most recent first)
                    sorted_sessions = sorted(
                        sessions,
                        key=lambda s: getattr(s, 'last_accessed', None) or 0,
                        reverse=True
                    )
                    most_recent = sorted_sessions[0]
                    self.logger.input(
                        "Triggered pipeline will use current session: {} (last accessed: {})",
                        most_recent.id, getattr(most_recent, 'last_accessed', 'unknown')
                    )
                    return most_recent.id
                else:
                    self.logger.warning(
                        "No active sessions found for 'use_current' strategy. Will create new session."
                    )
                    return None
            except Exception as e:
                self.logger.error(
                    "Error getting current session: {}. Will create new session.",
                    e
                )
                return None
        elif strategy == "per_file":
            # New session for each file event
            # Return None to let the system create a new session with its own generated ID
            return None
        elif strategy == "per_pipeline":
            # One session for all events
            # Check mapping first for fast lookup
            if pipeline_id in self._pipeline_session_map:
                mapped_session_id = self._pipeline_session_map[pipeline_id]
                # Verify the session still exists
                try:
                    existing_session = self.orchestrator.get_session(mapped_session_id)
                    if existing_session:
                        self.logger.debug(
                            "Using mapped session {} for pipeline {} (per_pipeline strategy)",
                            mapped_session_id, pipeline_id
                        )
                        return mapped_session_id
                    else:
                        # Session was deleted, remove from map
                        self.logger.warning(
                            "Mapped session {} for pipeline {} no longer exists, removing from map",
                            mapped_session_id, pipeline_id
                        )
                        del self._pipeline_session_map[pipeline_id]
                except Exception as e:
                    self.logger.warning(
                        "Error verifying mapped session {} for pipeline {}: {}, removing from map",
                        mapped_session_id, pipeline_id, e
                    )
                    del self._pipeline_session_map[pipeline_id]
            
            # No mapping or session deleted, return placeholder
            # Will be resolved in _execute_pipeline
            return f"{pipeline_id}-session"
        elif strategy == "custom":
            # Pipeline-specific logic
            # For file_watcher, could use file directory or other metadata
            # For now, default to per_file behavior (return None to create new session)
            return None
        else:
            # Default to per_file (return None to create new session)
            return None
    
    async def _execute_pipeline(
        self,
        pipeline_id: str,
        user_text: str,
        user_files: list[str],
        session_id: Optional[str],
        ui_mode: str = "background",
        session_strategy: str = "per_file",
    ) -> None:
        """
        Execute pipeline from trigger event.
        
        Args:
            pipeline_id: Pipeline ID
            user_text: User text for pipeline
            user_files: List of file paths
            session_id: Session ID (None means create new or use current)
            ui_mode: UI mode ("background" or "ui")
            session_strategy: Session strategy used to determine session
        """
        try:
            emitter = None
            agui_service = None
            turn_id = None
            run_id = None
            
            if ui_mode == "ui":
                # Get or create session
                if session_id is None:
                    # Create new session with source="trigger"
                    session_id = self.orchestrator.create_session(source="trigger")
                    self.logger.info(
                        "Created new database session {} for triggered pipeline {}",
                        session_id, pipeline_id
                    )
                    # Store in mapping if per_pipeline strategy
                    if session_strategy == "per_pipeline":
                        self._pipeline_session_map[pipeline_id] = session_id
                        self.logger.debug(
                            "Stored session mapping: {} -> {} (per_pipeline strategy)",
                            pipeline_id, session_id
                        )
                else:
                    # Check if session exists
                    existing_session = self.orchestrator.get_session(session_id)
                    if not existing_session:
                        # Session doesn't exist
                        if session_strategy == "per_pipeline":
                            # For per_pipeline, check mapping first (should have been checked in _determine_session_id,
                            # but double-check here in case mapping was cleared or session was deleted)
                            if pipeline_id in self._pipeline_session_map:
                                mapped_session_id = self._pipeline_session_map[pipeline_id]
                                mapped_session = self.orchestrator.get_session(mapped_session_id)
                                if mapped_session:
                                    session_id = mapped_session_id
                                    existing_session = mapped_session
                                    self.logger.info(
                                        "Using mapped session {} for pipeline {} (per_pipeline strategy)",
                                        session_id, pipeline_id
                                    )
                            
                            # If still not found, try searching all sessions (fallback)
                            if not existing_session:
                                try:
                                    all_sessions = self.orchestrator.get_all_sessions(status="active")
                                    for session in all_sessions:
                                        # Check if this session has turns for this pipeline
                                        turns = self.orchestrator._database_manager.get_chat_turns(session.id)
                                        for turn in turns:
                                            if turn.get("pipeline_id") == pipeline_id:
                                                # Found existing session for this pipeline
                                                session_id = session.id
                                                self.logger.info(
                                                    "Found existing session {} for pipeline {} (per_pipeline strategy, fallback search)",
                                                    session_id, pipeline_id
                                                )
                                                existing_session = session
                                                # Store in mapping for future use
                                                self._pipeline_session_map[pipeline_id] = session_id
                                                break
                                        if existing_session:
                                            break
                                except Exception as e:
                                    self.logger.warning(
                                        "Error looking for existing session for pipeline {}: {}",
                                        pipeline_id, e
                                    )
                        
                        if not existing_session:
                            # Still no session, create a new one
                            session_id = self.orchestrator.create_session(source="trigger")
                            self.logger.info(
                                "Created new database session {} for triggered pipeline {}",
                                session_id, pipeline_id
                            )
                            # Store in mapping if per_pipeline strategy
                            if session_strategy == "per_pipeline":
                                self._pipeline_session_map[pipeline_id] = session_id
                                self.logger.debug(
                                    "Stored session mapping: {} -> {} (per_pipeline strategy)",
                                    pipeline_id, session_id
                                )
                    elif session_strategy == "use_current":
                        # Update last_accessed to make this session the most recent
                        try:
                            self.orchestrator._database_manager.update_session_last_accessed(session_id)
                            self.logger.debug(
                                "Updated last_accessed for session {} (use_current strategy)",
                                session_id
                            )
                        except Exception as e:
                            self.logger.warning(
                                "Failed to update last_accessed for session {}: {}",
                                session_id, e
                            )
                
                # Set up emitter infrastructure using the same helper as /agui/turn
                # This ensures consistent event emission to the frontend
                if self.setup_emitter_fn:
                    try:
                        emitter, agui_service, queue = self.setup_emitter_fn(session_id)
                        self.logger.debug(
                            "Set up emitter infrastructure for session {} (UI mode)",
                            session_id
                        )
                    except Exception as e:
                        self.logger.warning(
                            "Failed to set up emitter for session {}: {}. Continuing without UI events.",
                            session_id, e
                        )
                        # Fallback: create minimal emitter (no SSE)
                        emitter = None
                        agui_service = None
                else:
                    # No emitter setup function provided (background mode or not in FastAPI context)
                    emitter = None
                    agui_service = None
                
                # Log which session is being used
                self.logger.input(
                    "Triggered pipeline '{}' executing with session ID: {} (strategy: {})",
                    pipeline_id, session_id, session_strategy
                )
                
                # Format user input for Assistant (with Pipeline ID prefix)
                # This tells the Assistant to skip intent classification and execute directly
                formatted_user_input = f"Pipeline ID: {pipeline_id}\nUser request: {user_text}"
                
                # Create Assistant instance (reuse existing session and emitter infrastructure)
                assistant = Assistant(
                    config=self.orchestrator.raw_config,
                    project_dir=str(self.project_dir),
                    emitter=emitter,
                    agui_service=agui_service,
                    session_id=session_id,
                )
                
                # Initialize Assistant (creates LLM and agent)
                await assistant.initialize()
                
                # Execute via Assistant (will see Pipeline ID and execute directly)
                # Assistant handles all event emission (card, text message, run_finished, etc.)
                await assistant.execute_assistant_agent(
                    user_input=formatted_user_input,
                    file_paths=user_files,
                    original_filenames=[Path(f).name for f in user_files] if user_files else [],
                    upload_intent="session",
                    mode="fastapi",
                    is_event_triggered=True,  # Mark as event-triggered to create initial entries
                )
                
                self.logger.success(
                    "Pipeline {} executed successfully via Assistant (ui_mode: {})",
                    pipeline_id, ui_mode
                )
            else:
                # Background mode - no UI components, execute directly via orchestrator
                self.logger.input(
                    "Triggered pipeline '{}' executing in background mode (no UI) - session ID: {} (strategy: {})",
                    pipeline_id, session_id, session_strategy
                )
                
                # For background mode, execute directly without Assistant (no LLM needed)
                result = await self.orchestrator.execute_pipeline(
                    pipeline_id=pipeline_id,
                    user_text=user_text,
                    user_files=user_files,
                    session_id=session_id,
                    emitter=None,  # No emitter for background mode
                    agui_service=None,
                )
                
                self.logger.success(
                    "Pipeline {} executed successfully in background mode",
                    pipeline_id
                )
        except Exception as e:
            self.logger.error(
                "Failed to execute pipeline {} from trigger: {}",
                pipeline_id, e
            )
            # Try to complete turn even on error
            if ui_mode == "ui" and turn_id:
                try:
                    self.orchestrator.complete_turn(turn_id)
                except Exception:
                    pass