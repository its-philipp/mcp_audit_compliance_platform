"""
Mock Google A2A Framework Implementation

This module provides a mock implementation of Google's A2A framework
for demonstration purposes, since the actual package is not available
in the public registry.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
import json


class RequestContext:
    """Mock request context for A2A framework."""
    
    def __init__(self, user_input: str, request_id: str = None, task_id: str = None):
        self.user_input = user_input
        self.request_id = request_id or f"req_{datetime.now().timestamp()}"
        self.task_id = task_id or f"task_{self.request_id}"
    
    def get_user_input(self) -> str:
        return self.user_input
    
    def get_request_id(self) -> str:
        return self.request_id
    
    def get_task_id(self) -> str:
        return self.task_id


class EventQueue:
    """Mock event queue for A2A framework."""
    
    def __init__(self):
        self.events = []
    
    async def put(self, event: Any):
        """Add an event to the queue."""
        self.events.append(event)
    
    def get_events(self) -> List[Any]:
        """Get all events from the queue."""
        return self.events


class Message:
    """Mock message class for A2A framework."""
    
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata
        }


class Task:
    """Mock task class for A2A framework."""
    
    def __init__(self, task_id: str, description: str, metadata: Dict[str, Any] = None):
        self.task_id = task_id
        self.description = description
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "metadata": self.metadata
        }


class TaskStatusUpdateEvent:
    """Mock task status update event for A2A framework."""
    
    def __init__(self, task_id: str, state: str, metadata: Dict[str, Any] = None):
        self.task_id = task_id
        self.state = state
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "state": self.state,
            "metadata": self.metadata
        }


class TaskArtifactUpdateEvent:
    """Mock task artifact update event for A2A framework."""
    
    def __init__(self, task_id: str, artifact: Any, metadata: Dict[str, Any] = None):
        self.task_id = task_id
        self.artifact = artifact
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "artifact": self.artifact,
            "metadata": self.metadata
        }


class TaskState:
    """Mock task state constants for A2A framework."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class AgentExecutor(ABC):
    """Mock base AgentExecutor class for A2A framework."""
    
    def __init__(self):
        self.agent_name = "base-agent"
        self.agent_version = "1.0.0"
    
    @abstractmethod
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute the main agent logic.
        
        Args:
            context: Request context containing user input and metadata
            event_queue: Queue for sending responses and events
        """
        pass
    
    @abstractmethod
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Cancel an ongoing task.
        
        Args:
            context: Request context containing task information
            event_queue: Queue for sending status updates
        """
        pass


# Create events module for compatibility
class events:
    Message = Message
    Task = Task
    TaskStatusUpdateEvent = TaskStatusUpdateEvent
    TaskArtifactUpdateEvent = TaskArtifactUpdateEvent

# Create tasks module for compatibility  
class tasks:
    TaskState = TaskState

# Mock module exports to match Google A2A framework
__all__ = [
    "AgentExecutor",
    "RequestContext", 
    "EventQueue",
    "Message",
    "Task",
    "TaskStatusUpdateEvent",
    "TaskArtifactUpdateEvent",
    "TaskState",
    "events",
    "tasks"
]
