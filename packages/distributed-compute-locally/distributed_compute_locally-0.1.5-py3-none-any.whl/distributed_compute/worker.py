"""
Worker node implementation.
"""

import socket
import threading
import time
import logging
import psutil
from typing import Optional

from .protocol import Protocol, MessageType
from .task import Task, TaskStatus
from .exceptions import WorkerConnectionError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Worker:
    """
    Worker node that connects to a coordinator and executes tasks.
    """
    
    def __init__(
        self,
        coordinator_host: str,
        coordinator_port: int,
        max_concurrent_tasks: int = 2,
        name: Optional[str] = None,
        heartbeat_interval: float = 5.0,
        password: Optional[str] = None,
    ):
        """
        Initialize a worker node.
        
        Args:
            coordinator_host: IP address or hostname of the coordinator
            coordinator_port: Port number of the coordinator
            max_concurrent_tasks: Maximum number of tasks to run concurrently
            name: Optional name for this worker
            heartbeat_interval: Seconds between heartbeat messages
            password: Optional password for coordinator authentication
        """
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port
        self.max_concurrent_tasks = max_concurrent_tasks
        self.name = name or f"worker-{socket.gethostname()}"
        self.heartbeat_interval = heartbeat_interval
        self.password = password
        
        self.worker_id = None
        self.socket = None
        self.running = False
        self.current_tasks = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        
        self._lock = threading.Lock()
        self._threads = []
    
    def start(self, block: bool = False):
        """Start the worker and connect to the coordinator.

        Args:
            block: When True, block the calling thread and keep the worker running.
                   When False, return immediately (useful for tests and programmatic use).
        """
        logger.info(f"Starting worker '{self.name}'...")
        
        try:
            self._connect_to_coordinator()
            self._register_with_coordinator()
            
            self.running = True
            
            # Start listening for tasks
            listen_thread = threading.Thread(
                target=self._listen_for_tasks,
                daemon=not block
            )
            listen_thread.start()
            self._threads.append(listen_thread)
            
            # Start heartbeat thread
            heartbeat_thread = threading.Thread(target=self._send_heartbeats, daemon=True)
            heartbeat_thread.start()
            self._threads.append(heartbeat_thread)
            
            if block:
                listen_thread.join()
            
        except KeyboardInterrupt:
            logger.info("Worker interrupted by user")
            self.stop()
        except Exception as e:
            logger.error(f"Worker error: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the worker gracefully."""
        logger.info(f"Stopping worker '{self.name}'...")
        self.running = False
        
        if self.socket:
            try:
                Protocol.send_message(self.socket, MessageType.SHUTDOWN, {
                    "worker_id": self.worker_id
                })
                self.socket.close()
            except:
                pass
        
        logger.info(f"Worker stopped. Completed: {self.tasks_completed}, Failed: {self.tasks_failed}")
    
    def _connect_to_coordinator(self):
        """Establish connection to the coordinator."""
        logger.info(f"Connecting to coordinator at {self.coordinator_host}:{self.coordinator_port}")
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.coordinator_host, self.coordinator_port))
            logger.info("Connected to coordinator")
        except Exception as e:
            raise WorkerConnectionError(f"Failed to connect to coordinator: {e}")
    
    def _register_with_coordinator(self):
        """Register this worker with the coordinator."""
        cpu_count = psutil.cpu_count()
        memory = psutil.virtual_memory()
        
        payload = {
            "name": self.name,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "cpu_count": cpu_count,
            "memory_total": memory.total,
            "memory_available": memory.available,
        }
        
        # Add password if provided
        if self.password:
            payload["password"] = self.password
        
        Protocol.send_message(self.socket, MessageType.REGISTER_WORKER, payload)
        
        # Wait for registration confirmation
        msg_type, payload = Protocol.receive_message(self.socket, timeout=10.0)
        
        if msg_type == MessageType.WORKER_REGISTERED:
            self.worker_id = payload["worker_id"]
            logger.info(f"Registered with coordinator. Worker ID: {self.worker_id}")
        elif msg_type == MessageType.AUTH_FAILED:
            reason = payload.get("reason", "Authentication failed")
            raise WorkerConnectionError(f"Authentication failed: {reason}")
        else:
            raise WorkerConnectionError("Failed to register with coordinator")
    
    def _send_heartbeats(self):
        """Send periodic heartbeat messages to the coordinator."""
        while self.running:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                payload = {
                    "worker_id": self.worker_id,
                    "current_tasks": self.current_tasks,
                    "tasks_completed": self.tasks_completed,
                    "tasks_failed": self.tasks_failed,
                    "cpu_percent": cpu_percent,
                    "memory_available": memory.available,
                }
                
                Protocol.send_message(self.socket, MessageType.HEARTBEAT, payload)
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                if self.running:
                    self.stop()
                break
    
    def _listen_for_tasks(self):
        """Listen for task assignments from the coordinator."""
        logger.info("Listening for tasks...")
        
        while self.running:
            try:
                msg_type, payload = Protocol.receive_message(self.socket, timeout=1.0)
                
                if msg_type is None:
                    continue
                
                if msg_type == MessageType.TASK_ASSIGNMENT:
                    # Execute task in a separate thread
                    task_thread = threading.Thread(
                        target=self._execute_task,
                        args=(payload,),
                        daemon=True
                    )
                    task_thread.start()
                    self._threads.append(task_thread)
                
                elif msg_type == MessageType.SHUTDOWN:
                    logger.info("Received shutdown command from coordinator")
                    self.stop()
                    break
                    
            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error listening for tasks: {e}")
                if self.running:
                    self.stop()
                break
    
    def _execute_task(self, task_data: dict):
        """Execute a task and send the result back to the coordinator."""
        task = Task(
            func=task_data["func"],
            args=task_data["args"],
            kwargs=task_data["kwargs"],
            task_id=task_data["task_id"]
        )
        
        with self._lock:
            self.current_tasks += 1
        
        logger.info(f"Executing task {task.task_id[:8]}...")
        
        try:
            result = task.execute()
            
            # Send result back to coordinator
            payload = {
                "task_id": task.task_id,
                "result": result,
                "worker_id": self.worker_id,
                "execution_time": task.get_execution_time(),
            }
            
            Protocol.send_message(self.socket, MessageType.TASK_RESULT, payload)
            
            with self._lock:
                self.tasks_completed += 1
            
            logger.info(f"Task {task.task_id[:8]} completed in {task.get_execution_time():.2f}s")
            
        except Exception as e:
            logger.error(f"Task {task.task_id[:8]} failed: {e}")
            
            # Send error back to coordinator
            payload = {
                "task_id": task.task_id,
                "error": str(e),
                "worker_id": self.worker_id,
            }
            
            try:
                Protocol.send_message(self.socket, MessageType.TASK_ERROR, payload)
            except:
                pass
            
            with self._lock:
                self.tasks_failed += 1
        
        finally:
            with self._lock:
                self.current_tasks -= 1
