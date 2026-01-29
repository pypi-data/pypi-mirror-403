"""
DistributedCompute - A library for distributing computational workloads across multiple devices.
"""

from .coordinator import Coordinator
from .worker import Worker
from .exceptions import (
    DistributedComputeError,
    WorkerConnectionError,
    TaskExecutionError,
    TimeoutError,
)

__version__ = "0.1.5"
__all__ = [
    "Coordinator",
    "Worker",
    "DistributedComputeError",
    "WorkerConnectionError",
    "TaskExecutionError",
    "TimeoutError",
]
