"""
Custom exceptions for the distributed compute library.
"""


class DistributedComputeError(Exception):
    """Base exception for all distributed compute errors."""
    pass


class WorkerConnectionError(DistributedComputeError):
    """Raised when unable to connect to a worker node."""
    pass


class TaskExecutionError(DistributedComputeError):
    """Raised when a task fails during execution."""
    pass


class TimeoutError(DistributedComputeError):
    """Raised when a task or operation times out."""
    pass
