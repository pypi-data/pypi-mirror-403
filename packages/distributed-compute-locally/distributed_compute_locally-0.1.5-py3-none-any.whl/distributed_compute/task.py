"""
Task representation and management.
"""

import uuid
import time
from enum import Enum
from typing import Any, Callable


class TaskStatus(Enum):
    """Status of a task."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Task:
    """Represents a computational task to be executed."""
    
    def __init__(self, func: Callable, args: tuple = None, kwargs: dict = None, task_id: str = None):
        """
        Initialize a task.
        
        Args:
            func: The function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            task_id: Optional task ID (generated if not provided)
        """
        self.task_id = task_id or str(uuid.uuid4())
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.worker_id = None
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
    
    def execute(self) -> Any:
        """
        Execute the task and return the result.
        
        Returns:
            The result of the function execution
        
        Raises:
            Exception: Any exception raised during function execution
        """
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()
        
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.status = TaskStatus.COMPLETED
            self.completed_at = time.time()
            return self.result
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            self.completed_at = time.time()
            raise
    
    def to_dict(self) -> dict:
        """Convert task to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "func": self.func,
            "args": self.args,
            "kwargs": self.kwargs,
            "status": self.status.value,
        }
    
    def get_execution_time(self) -> float:
        """Get task execution time in seconds."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return 0.0
    
    def __repr__(self):
        return f"Task(id={self.task_id[:8]}, status={self.status.value}, func={self.func.__name__})"
