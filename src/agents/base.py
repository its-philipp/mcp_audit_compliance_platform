"""
Base AgentExecutor implementation using Google A2A framework.

This module provides the foundation for all agents in the A2A audit compliance system.
"""

from typing import Any, Dict, Optional
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.events import Event
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseAuditAgent(AgentExecutor):
    """
    Base class for all audit compliance agents using Google A2A framework.
    
    This class provides common functionality for:
    - Request processing
    - Error handling
    - Logging
    - Task management
    """
    
    def __init__(self, agent_name: str, agent_version: str = "1.0.0"):
        """
        Initialize the base audit agent.
        
        Args:
            agent_name: Name of the agent (e.g., "financial-data-agent")
            agent_version: Version of the agent
        """
        super().__init__()
        self.agent_name = agent_name
        self.agent_version = agent_version
        self.logger = logging.getLogger(f"a2a.{agent_name}")
        
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute the main agent logic.
        
        This method should be overridden by subclasses to implement
        specific agent functionality.
        
        Args:
            context: Request context containing user input and metadata
            event_queue: Queue for sending responses and events
        """
        try:
            self.logger.info(f"Processing request in {self.agent_name}")
            
            # Extract user input from context
            user_input = context.get_user_input()
            self.logger.debug(f"User input: {user_input}")
            
            # Process the request (to be implemented by subclasses)
            result = await self._process_request(context)
            
            # Send response event
            response_event = Event(
                content=str(result),
                metadata={
                    "agent_name": self.agent_name,
                    "agent_version": self.agent_version,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_id": context.context_id
                }
            )
            
            event_queue.enqueue_event(response_event)
            self.logger.info(f"Response sent from {self.agent_name}")
            
        except Exception as e:
            self.logger.error(f"Error in {self.agent_name}: {str(e)}")
            error_event = Event(
                content=f"Error processing request: {str(e)}",
                metadata={
                    "agent_name": self.agent_name,
                    "error": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            event_queue.enqueue_event(error_event)
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Cancel an ongoing task.
        
        Args:
            context: Request context containing task information
            event_queue: Queue for sending status updates
        """
        task_id = context.task_id
        self.logger.info(f"Cancelling task {task_id} in {self.agent_name}")
        
        # Send cancellation event
        cancel_event = Event(
            content=f"Task {task_id} cancelled",
            metadata={
                "agent_name": self.agent_name,
                "task_id": task_id,
                "status": "cancelled",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        event_queue.enqueue_event(cancel_event)
        self.logger.info(f"Task {task_id} cancelled in {self.agent_name}")
    
    async def _process_request(self, context: RequestContext) -> Any:
        """
        Process the specific request for this agent.
        
        This method should be overridden by subclasses to implement
        agent-specific logic.
        
        Args:
            context: Request context
            
        Returns:
            Result of the processing
        """
        raise NotImplementedError("Subclasses must implement _process_request")
    
    def get_agent_card(self) -> Dict[str, Any]:
        """
        Get the agent card describing this agent's capabilities.
        
        Returns:
            Dictionary containing agent metadata and capabilities
        """
        return {
            "name": self.agent_name,
            "version": self.agent_version,
            "description": f"A2A agent for {self.agent_name}",
            "capabilities": self._get_capabilities(),
            "endpoints": self._get_endpoints(),
            "metadata": {
                "framework": "google-a2a",
                "created_at": datetime.utcnow().isoformat()
            }
        }
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this agent.
        
        Returns:
            Dictionary describing agent capabilities
        """
        return {
            "input_types": ["text", "json"],
            "output_types": ["text", "json"],
            "supported_operations": []
        }
    
    def _get_endpoints(self) -> Dict[str, Any]:
        """
        Get the endpoints this agent exposes.
        
        Returns:
            Dictionary describing agent endpoints
        """
        return {
            "execute": {
                "method": "POST",
                "description": "Execute agent logic"
            },
            "cancel": {
                "method": "POST", 
                "description": "Cancel ongoing task"
            }
        }
