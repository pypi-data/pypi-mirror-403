"""
Operations Assistant Module

Specialized assistant for Operations Center that helps users manage HITL requests
and cases through natural language interactions.
"""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from agent_framework import ChatAgent, ChatMessage, Role

from topaz_agent_kit.frameworks.framework_config_manager import FrameworkConfigManager
from topaz_agent_kit.frameworks.framework_model_factory import FrameworkModelFactory
from topaz_agent_kit.utils.logger import Logger
from topaz_agent_kit.core.chat_database import ChatDatabase
from topaz_agent_kit.core.hitl_queue_manager import HITLQueueManager
from topaz_agent_kit.core.resume_handler import ResumeHandler
from topaz_agent_kit.core.case_manager import CaseManager
from topaz_agent_kit.utils.prompt_loader import PromptLoader
from topaz_agent_kit.utils.json_utils import JSONUtils


class OperationsAssistant:
    """
    Operations Assistant for managing HITL requests and cases.
    
    Similar to Assistant class but specialized for operations center tasks.
    Provides tools for approving/rejecting HITL requests, viewing cases,
    and managing the operations queue.
    """
    
    def __init__(
        self,
        config: Dict[str, Any],
        project_dir: str,
        database: ChatDatabase,
        session_id: Optional[str] = None,
        resume_handler: Optional[ResumeHandler] = None,
        case_manager: Optional[CaseManager] = None,
    ):
        """
        Initialize Operations Assistant.
        
        Args:
            config: Configuration dictionary (must contain operations_assistant section)
            project_dir: Project directory path
            database: ChatDatabase instance
            session_id: Optional session ID (creates new if not provided)
            resume_handler: Optional ResumeHandler for resuming pipelines after HITL responses
            case_manager: Optional CaseManager for managing cases
        """
        self.logger = Logger("OperationsAssistant")
        self._project_dir = project_dir
        self._database = database
        self._hitl_queue_manager = HITLQueueManager(database)
        self._resume_handler = resume_handler
        self._case_manager = case_manager or CaseManager(database)
        
        # Load operations assistant config
        self._assistant_config = config.get("operations_assistant")
        if not self._assistant_config:
            # Fallback to assistant config if operations_assistant not found
            self._assistant_config = config.get("assistant")
            if not self._assistant_config:
                raise ValueError("operations_assistant or assistant section missing in config")
        
        self._agent_id = self._assistant_config.get("id", "operations_assistant")
        self._framework_type = self._assistant_config.get("type", "maf")
        self._model_type = self._assistant_config.get("model", "azure_openai")
        self._llm = None
        self._agent = None
        
        # Load assistant instruction
        self._prompt_loader = PromptLoader(self._project_dir)
        self._prompt_spec = self._assistant_config.get("prompt", {})
        self._prompt_spec_instruction = self._prompt_spec.get("instruction")
        
        if not self._prompt_spec_instruction:
            # Default prompt path
            self._prompt_spec_instruction = "prompts/operations_assistant.jinja"
        
        # Load the prompt template (raw, not rendered yet)
        # We'll render it with context when creating the agent
        self._assistant_instruction_template = self._prompt_loader.load_prompt(
            self._prompt_spec_instruction
        )
        
        if not self._assistant_instruction_template:
            self.logger.error(
                "Failed to load operations assistant instruction: {}",
                self._prompt_spec_instruction
            )
            raise ValueError(
                f"Operations assistant prompt not found: {self._prompt_spec_instruction}. "
                "Please ensure the prompt file exists in config/prompts/"
            )
        
        # Session management
        if session_id:
            self._session_id = session_id
            self.logger.info("Using provided session ID: {}", session_id)
        else:
            # Create a new session for operations assistant
            self._session_id = f"ops-{Path(project_dir).name}-{id(self)}"
            self.logger.info("Created new operations session ID: {}", self._session_id)
        
        self._thread = None
        
        # Context for current operation (case_id, queue_item_id)
        self._context: Dict[str, Any] = {}
        
        self.logger.success(
            "Operations Assistant initialized with session ID: {}", self._session_id
        )
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set context for the assistant (case_id, queue_item_id, etc.).
        
        Args:
            context: Context dictionary with case_id, queue_item_id, etc.
        """
        self._context = context.copy()
        self.logger.debug("Updated context: {}", context)
    
    def get_context(self) -> Dict[str, Any]:
        """Get current context."""
        return self._context.copy()
    
    async def _initialize_llm(self) -> None:
        """Initialize LLM using unified framework-aware factory."""
        try:
            config_manager = FrameworkConfigManager()
            model_config = config_manager.get_model_config(
                model_type=self._model_type,
                framework=self._framework_type,
            )
            
            self._llm = FrameworkModelFactory.get_model(
                model_type=self._model_type,
                framework=self._framework_type,
                **model_config,
            )
            
            self.logger.success(
                "Initialized Operations Assistant with {} {} model",
                self._framework_type.title(),
                self._model_type,
            )
        except Exception as e:
            self.logger.error("Failed to initialize LLM: {}", e)
            raise
    
    async def _create_assistant_agent(self) -> None:
        """Create operations assistant agent with tools."""
        try:
            # Render the prompt template with context variables
            # The template may contain Jinja2 syntax like {{ context.case_id }}
            instruction = self._prompt_loader.render_prompt(
                self._assistant_instruction_template,
                variables={"context": self._context}
            )
            
            self._agent = ChatAgent(
                chat_client=self._llm,
                name=self._agent_id,
                description="Operations Assistant - manages HITL requests and cases",
                instructions=instruction,
                tools=[
                    self.approve_hitl_request,
                    self.reject_hitl_request,
                    self.select_hitl_option,
                    self.retry_hitl_response,
                    self.get_case_details,
                    self.get_queue_items,
                    self.get_case_list,
                    self.add_hitl_notes,
                    self.delete_case,
                    self.delete_cases,
                ],
            )
            
            # Deserialize thread from database if available
            await self._deserialize_session_thread()
            
            self.logger.success("Operations assistant agent created successfully")
        except Exception as e:
            self.logger.error("Failed to create operations assistant agent: {}", e)
            raise
    
    async def initialize(self) -> None:
        """Initialize the operations assistant."""
        await self._initialize_llm()
        await self._create_assistant_agent()
    
    async def execute(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a user message and return response.
        
        Args:
            user_message: User's message
            context: Optional context (case_id, queue_item_id, etc.)
            
        Returns:
            Dictionary with assistant_response and tool execution results
        """
        # Update context if provided
        context_changed = False
        if context:
            # Check if context actually changed
            context_changed = self._context != context
            self.set_context(context)
        
        # Initialize or recreate agent if needed
        # Recreate if context changed (so prompt template is re-rendered with new context)
        if not self._agent or context_changed:
            if not self._llm:
                await self._initialize_llm()
            await self._create_assistant_agent()
        
        # Build user message with context
        message_text = user_message
        if self._context:
            context_info = []
            if self._context.get("case_id"):
                context_info.append(f"Case ID: {self._context['case_id']}")
            if self._context.get("queue_item_id"):
                context_info.append(f"Queue Item ID: {self._context['queue_item_id']}")
            if self._context.get("pipeline_id"):
                context_info.append(f"Pipeline: {self._context['pipeline_id']}")
            if context_info:
                message_text = f"{user_message}\n\nContext: {', '.join(context_info)}"
        
        message = ChatMessage(role=Role.USER, text=message_text)
        
        # Run the agent
        try:
            response = await self._agent.run(
                message,
                tool_choice="required",
                thread=self._thread,
            )
            
            # Extract response
            result = None
            if response.value:
                # Response is a dict with assistant_response, tool_executed, etc.
                result = JSONUtils.normalize_for_ui(response.value)
            else:
                # Fallback to text response
                result = {
                    "assistant_response": str(response),
                    "success": True,
                }
            
            # Serialize thread to database to maintain conversation history
            await self._serialize_session_thread()
            
            return result
        except Exception as e:
            self.logger.error("Error executing operations assistant: {}", e)
            return {
                "assistant_response": f"I encountered an error: {str(e)}",
                "success": False,
                "error": str(e),
            }
    
    # === OPERATIONS TOOLS ===
    
    async def approve_hitl_request(
        self,
        queue_item_id: str,
        notes: Optional[str] = None,
    ) -> str:
        """
        Tool: Approve a pending HITL request.
        
        Args:
            queue_item_id: The queue item ID to approve
            notes: Optional notes to add
            
        Returns:
            JSON string with result
        """
        try:
            # Use resume handler if available to properly resume the pipeline
            if self._resume_handler:
                result = await self._resume_handler.resume_from_queue_response(
                    queue_item_id=queue_item_id,
                    decision="approve",
                    response_data={"notes": notes} if notes else None,
                    responded_by="assistant",  # Operations assistant responding on behalf of user
                )
            else:
                # Fallback to just submitting response (won't resume pipeline)
                self.logger.warning(
                    "ResumeHandler not available, only submitting response without resuming pipeline"
                )
                result = self._hitl_queue_manager.submit_response(
                    queue_item_id=queue_item_id,
                    decision="approve",
                    response_data={"notes": notes} if notes else None,
                    responded_by="assistant",  # Operations assistant responding on behalf of user
                )
            
            if result.get("success"):
                self.logger.info("Approved HITL request: {}", queue_item_id)
                return JSONUtils.normalize_for_ui({
                    "success": True,
                    "action": "approve",
                    "queue_item_id": queue_item_id,
                    "case_id": result.get("case_id"),
                    "message": f"Successfully approved HITL request {queue_item_id}. Pipeline will resume processing.",
                })
            else:
                error_msg = result.get("error", "Unknown error")
                self.logger.error("Failed to approve HITL request {}: {}", queue_item_id, error_msg)
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": error_msg,
                    "queue_item_id": queue_item_id,
                })
        except Exception as e:
            self.logger.error("Error approving HITL request: {}", e)
            return JSONUtils.normalize_for_ui({
                "success": False,
                "error": str(e),
                "queue_item_id": queue_item_id,
            })
    
    async def reject_hitl_request(
        self,
        queue_item_id: str,
        notes: Optional[str] = None,
    ) -> str:
        """
        Tool: Reject a pending HITL request.
        
        Args:
            queue_item_id: The queue item ID to reject
            notes: Optional notes to add
            
        Returns:
            JSON string with result
        """
        try:
            # Use resume handler if available to properly resume the pipeline
            if self._resume_handler:
                result = await self._resume_handler.resume_from_queue_response(
                    queue_item_id=queue_item_id,
                    decision="reject",
                    response_data={"notes": notes} if notes else None,
                    responded_by="assistant",  # Operations assistant responding on behalf of user
                )
            else:
                # Fallback to just submitting response (won't resume pipeline)
                self.logger.warning(
                    "ResumeHandler not available, only submitting response without resuming pipeline"
                )
                result = self._hitl_queue_manager.submit_response(
                    queue_item_id=queue_item_id,
                    decision="reject",
                    response_data={"notes": notes} if notes else None,
                    responded_by="assistant",  # Operations assistant responding on behalf of user
                )
            
            if result.get("success"):
                self.logger.info("Rejected HITL request: {}", queue_item_id)
                return JSONUtils.normalize_for_ui({
                    "success": True,
                    "action": "reject",
                    "queue_item_id": queue_item_id,
                    "case_id": result.get("case_id"),
                    "message": f"Successfully rejected HITL request {queue_item_id}. Pipeline will resume processing.",
                })
            else:
                error_msg = result.get("error", "Unknown error")
                self.logger.error("Failed to reject HITL request {}: {}", queue_item_id, error_msg)
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": error_msg,
                    "queue_item_id": queue_item_id,
                })
        except Exception as e:
            self.logger.error("Error rejecting HITL request: {}", e)
            return JSONUtils.normalize_for_ui({
                "success": False,
                "error": str(e),
                "queue_item_id": queue_item_id,
                })
    
    async def select_hitl_option(
        self,
        queue_item_id: str,
        option_value: str,
        notes: Optional[str] = None,
    ) -> str:
        """
        Tool: Select an option for a selection gate HITL request.
        
        Use this when the HITL request is a selection gate (has multiple options to choose from).
        First call get_queue_items to see available options for the queue item.
        
        Args:
            queue_item_id: The queue item ID
            option_value: The value/ID of the option to select (must match one of the available options)
            notes: Optional notes to add
            
        Returns:
            JSON string with result
        """
        try:
            # Get queue item to verify it's a selection gate and get available options
            queue_item = self._hitl_queue_manager.get_queue_item(queue_item_id)
            if not queue_item:
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": f"Queue item {queue_item_id} not found",
                    "queue_item_id": queue_item_id,
                })
            
            gate_type = queue_item.get("gate_type")
            if gate_type != "selection":
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": f"Queue item {queue_item_id} is not a selection gate (type: {gate_type}). Use approve_hitl_request or reject_hitl_request instead.",
                    "queue_item_id": queue_item_id,
                })
            
            # Get available options
            options = queue_item.get("options") or []
            if not options:
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": f"No options available for selection gate {queue_item_id}",
                    "queue_item_id": queue_item_id,
                })
            
            # Verify the option_value matches one of the available options
            # Options can be dicts with 'value' or 'id' keys, or just strings
            option_values = []
            for opt in options:
                if isinstance(opt, dict):
                    option_values.append(opt.get("value") or opt.get("id") or str(opt))
                else:
                    option_values.append(str(opt))
            
            if option_value not in option_values:
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": f"Option '{option_value}' not found. Available options: {', '.join(option_values)}",
                    "queue_item_id": queue_item_id,
                    "available_options": option_values,
                })
            
            # Use resume handler if available to properly resume the pipeline
            if self._resume_handler:
                result = await self._resume_handler.resume_from_queue_response(
                    queue_item_id=queue_item_id,
                    decision=option_value,  # For selection gates, decision is the selected option value
                    response_data={"notes": notes, "selection": option_value} if notes else {"selection": option_value},
                    responded_by="assistant",  # Operations assistant responding on behalf of user
                )
            else:
                # Fallback to just submitting response (won't resume pipeline)
                self.logger.warning(
                    "ResumeHandler not available, only submitting response without resuming pipeline"
                )
                result = self._hitl_queue_manager.submit_response(
                    queue_item_id=queue_item_id,
                    decision=option_value,
                    response_data={"notes": notes, "selection": option_value} if notes else {"selection": option_value},
                    responded_by="assistant",  # Operations assistant responding on behalf of user
                )
            
            if result.get("success"):
                self.logger.info("Selected option '{}' for HITL request: {}", option_value, queue_item_id)
                return JSONUtils.normalize_for_ui({
                    "success": True,
                    "action": "select",
                    "queue_item_id": queue_item_id,
                    "case_id": result.get("case_id"),
                    "option_value": option_value,
                    "message": f"Successfully selected option '{option_value}' for HITL request {queue_item_id}. Pipeline will resume processing.",
                })
            else:
                error_msg = result.get("error", "Unknown error")
                self.logger.error("Failed to select option for HITL request {}: {}", queue_item_id, error_msg)
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": error_msg,
                    "queue_item_id": queue_item_id,
                })
        except Exception as e:
            self.logger.error("Error selecting option for HITL request: {}", e)
            return JSONUtils.normalize_for_ui({
                "success": False,
                "error": str(e),
                "queue_item_id": queue_item_id,
            })
    
    async def retry_hitl_response(self, queue_item_id: str) -> str:
        """
        Tool: Retry a failed HITL response.
        
        Use this when a HITL response failed and you want to retry it.
        This resets the queue item back to pending status so you can respond again.
        
        Args:
            queue_item_id: The queue item ID to retry
            
        Returns:
            JSON string with result
        """
        try:
            result = self._hitl_queue_manager.reset_queue_item_for_retry(queue_item_id)
            
            if result.get("success"):
                self.logger.info("Reset queue item for retry: {}", queue_item_id)
                return JSONUtils.normalize_for_ui({
                    "success": True,
                    "queue_item_id": queue_item_id,
                    "previous_status": result.get("previous_status"),
                    "message": f"Queue item {queue_item_id} has been reset to pending. You can now retry the response using approve_hitl_request, reject_hitl_request, or select_hitl_option.",
                })
            else:
                error_msg = result.get("error", "Unknown error")
                self.logger.error("Failed to retry HITL response {}: {}", queue_item_id, error_msg)
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": error_msg,
                    "queue_item_id": queue_item_id,
                })
        except Exception as e:
            self.logger.error("Error retrying HITL response: {}", e)
            return JSONUtils.normalize_for_ui({
                "success": False,
                "error": str(e),
                "queue_item_id": queue_item_id,
            })
    
    async def get_case_details(self, case_id: str) -> str:
        """
        Tool: Get detailed information about a case.
        
        Args:
            case_id: The case ID to retrieve
            
        Returns:
            JSON string with case details
        """
        try:
            case = self._database.get_pipeline_case(case_id)
            
            if case:
                self.logger.debug("Retrieved case details: {}", case_id)
                return JSONUtils.normalize_for_ui({
                    "success": True,
                    "case": case,
                })
            else:
                self.logger.warning("Case not found: {}", case_id)
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": f"Case {case_id} not found",
                    "case_id": case_id,
                })
        except Exception as e:
            self.logger.error("Error getting case details: {}", e)
            return JSONUtils.normalize_for_ui({
                "success": False,
                "error": str(e),
                "case_id": case_id,
            })
    
    async def get_queue_items(
        self,
        status: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """
        Tool: List HITL queue items with optional filters.
        
        Args:
            status: Filter by status (pending, responded, etc.)
            pipeline_id: Filter by pipeline
            limit: Maximum number of results
            
        Returns:
            JSON string with queue items
        """
        try:
            items = self._hitl_queue_manager.list_queue(
                pipeline_id=pipeline_id,
                status=status,
                limit=limit,
            )
            
            self.logger.debug("Retrieved {} queue items", len(items))
            return JSONUtils.normalize_for_ui({
                "success": True,
                "items": items,
                "count": len(items),
            })
        except Exception as e:
            self.logger.error("Error getting queue items: {}", e)
            return JSONUtils.normalize_for_ui({
                "success": False,
                "error": str(e),
                "items": [],
            })
    
    async def get_case_list(
        self,
        status: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """
        Tool: List cases with optional filters.
        
        Args:
            status: Filter by status
            pipeline_id: Filter by pipeline
            limit: Maximum number of results
            
        Returns:
            JSON string with cases
        """
        try:
            cases = self._database.list_pipeline_cases(
                pipeline_id=pipeline_id,
                status=status,
                limit=limit,
            )
            
            self.logger.debug("Retrieved {} cases", len(cases))
            return JSONUtils.normalize_for_ui({
                "success": True,
                "cases": cases,
                "count": len(cases),
            })
        except Exception as e:
            self.logger.error("Error getting case list: {}", e)
            return JSONUtils.normalize_for_ui({
                "success": False,
                "error": str(e),
                "cases": [],
            })
    
    async def add_hitl_notes(
        self,
        queue_item_id: str,
        notes: str,
    ) -> str:
        """
        Tool: Add notes to a HITL request.
        
        Args:
            queue_item_id: The queue item ID
            notes: Notes to add
            
        Returns:
            JSON string with result
        """
        try:
            # Get current queue item
            queue_item = self._hitl_queue_manager.get_queue_item(queue_item_id)
            
            if not queue_item:
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": f"Queue item {queue_item_id} not found",
                })
            
            # Get existing response_data
            existing_response_data = {}
            if queue_item.get("response_data"):
                try:
                    if isinstance(queue_item["response_data"], str):
                        existing_response_data = json.loads(queue_item["response_data"])
                    else:
                        existing_response_data = queue_item["response_data"]
                except (json.JSONDecodeError, TypeError):
                    existing_response_data = {}
            
            # Append notes to existing notes
            existing_notes = existing_response_data.get("notes", "")
            if existing_notes:
                updated_notes = f"{existing_notes}\n{notes}"
            else:
                updated_notes = notes
            
            # Update response_data with new notes
            updated_response_data = {**existing_response_data, "notes": updated_notes}
            
            # Get current decision or use "pending" if not set
            current_decision = queue_item.get("decision") or queue_item.get("response_action") or "pending"
            
            # Update the database
            success = self._database.update_hitl_queue_response(
                queue_item_id=queue_item_id,
                decision=current_decision,
                response_data=updated_response_data,
            )
            
            if success:
                self.logger.info("Added notes to queue item: {}", queue_item_id)
                return JSONUtils.normalize_for_ui({
                    "success": True,
                    "queue_item_id": queue_item_id,
                    "message": "Notes added successfully",
                })
            else:
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": "Failed to update notes",
                    "queue_item_id": queue_item_id,
                })
        except Exception as e:
            self.logger.error("Error adding notes: {}", e)
            return JSONUtils.normalize_for_ui({
                "success": False,
                "error": str(e),
                "queue_item_id": queue_item_id,
            })
    
    async def delete_case(self, case_id: str) -> str:
        """
        Tool: Delete a specific case and all associated data.
        
        Args:
            case_id: The case ID to delete
            
        Returns:
            JSON string with result
        """
        try:
            success = self._case_manager.delete_case(case_id)
            
            if success:
                self.logger.info("Deleted case: {}", case_id)
                return JSONUtils.normalize_for_ui({
                    "success": True,
                    "case_id": case_id,
                    "message": f"Case {case_id} deleted successfully",
                })
            else:
                return JSONUtils.normalize_for_ui({
                    "success": False,
                    "error": "Failed to delete case",
                    "case_id": case_id,
                })
        except Exception as e:
            self.logger.error("Error deleting case: {}", e)
            return JSONUtils.normalize_for_ui({
                "success": False,
                "error": str(e),
                "case_id": case_id,
            })
    
    async def delete_cases(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Tool: Delete multiple cases with optional filters.
        
        Args:
            pipeline_id: Filter by pipeline (optional)
            status: Filter by status (optional)
            
        Returns:
            JSON string with result including deleted_count
        """
        try:
            deleted_count = self._case_manager.delete_cases(
                pipeline_id=pipeline_id,
                status=status,
            )
            
            self.logger.info("Deleted {} cases", deleted_count)
            return JSONUtils.normalize_for_ui({
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Deleted {deleted_count} case(s)",
                "pipeline_id": pipeline_id,
                "status": status,
            })
        except Exception as e:
            self.logger.error("Error deleting cases: {}", e)
            return JSONUtils.normalize_for_ui({
                "success": False,
                "error": str(e),
                "deleted_count": 0,
            })
    
    async def _serialize_session_thread(self) -> None:
        """
        Serialize the session thread to database to maintain conversation history.
        """
        if not self._thread:
            self.logger.debug("No thread to serialize")
            return
        
        try:
            self.logger.debug(
                "Serializing session thread to database for session: {}",
                self._session_id,
            )
            serialized_thread = await self._thread.serialize()
            serialized_json = json.dumps(serialized_thread)
            
            # Store thread state in database
            success = self._database.update_chat_session(
                self._session_id, {"thread_state": serialized_json}
            )
            
            if success:
                self.logger.debug(
                    "Thread state saved to database for session: {}", self._session_id
                )
            else:
                self.logger.warning(
                    "Failed to save thread state to database for session: {}",
                    self._session_id,
                )
        except Exception as e:
            self.logger.error("Error serializing thread to database: {}", e)
    
    async def _deserialize_session_thread(self) -> None:
        """
        Deserialize the session thread from database to restore conversation history.
        """
        try:
            # Get session from database
            session_data = self._database.get_chat_session(self._session_id)
            
            if session_data and session_data.get('thread_state'):
                self.logger.debug(
                    "Deserializing session thread from database for session: {}",
                    self._session_id,
                )
                try:
                    serialized_thread = json.loads(session_data['thread_state'])
                    self._thread = await self._agent.deserialize_thread(serialized_thread)
                    self.logger.debug(
                        "Thread state loaded from database for session: {}",
                        self._session_id,
                    )
                except json.JSONDecodeError as e:
                    self.logger.warning(
                        "Failed to parse thread state JSON from database: {}. Creating new thread.",
                        e
                    )
                    self._thread = self._agent.get_new_thread()
            else:
                self.logger.debug(
                    "No thread state found in database for session: {}, creating new thread",
                    self._session_id,
                )
                self._thread = self._agent.get_new_thread()
        except Exception as e:
            self.logger.error("Error deserializing thread from database: {}", e)
            self._thread = self._agent.get_new_thread()