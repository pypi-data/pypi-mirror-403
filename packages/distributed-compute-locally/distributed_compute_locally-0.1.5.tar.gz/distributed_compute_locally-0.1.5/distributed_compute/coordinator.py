"""
Coordinator node implementation.
"""

import socket
import threading
import time
import logging
from collections import deque
from typing import List, Callable, Any, Optional
import queue

from .protocol import Protocol, MessageType
from .task import Task, TaskStatus
from .exceptions import TimeoutError as DistributedTimeoutError
from .auth import AuthManager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkerInfo:
    """Information about a connected worker."""
    
    def __init__(self, worker_id: str, socket: socket.socket, name: str, max_tasks: int):
        self.worker_id = worker_id
        self.socket = socket
        self.name = name
        self.max_tasks = max_tasks
        self.current_tasks = 0
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.last_heartbeat = time.time()
        self.cpu_percent = 0.0
        self.memory_available = 0
        self.is_alive = True


class Coordinator:
    """
    Coordinator node that manages workers and distributes tasks.
    """
    
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 5000,
        verbose: bool = False,
        worker_timeout: float = 30.0,
        password: Optional[str] = None,
    ):
        """
        Initialize the coordinator.
        
        Args:
            host: Host address to bind to (0.0.0.0 for all interfaces)
            port: Port number to listen on
            verbose: Enable verbose logging
            worker_timeout: Seconds before marking a worker as dead
            password: Optional password for worker authentication
        """
        self.host = host
        self.port = port
        self.verbose = verbose
        self.worker_timeout = worker_timeout
        
        # Initialize authentication
        self.auth_manager = AuthManager(password)
        if password:
            logger.info("Password authentication enabled")
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        self.workers = {}  # worker_id -> WorkerInfo
        self.task_queue = deque()
        self.pending_tasks = {}  # task_id -> Task
        self.completed_tasks = {}  # task_id -> Task
        self.result_queue = queue.Queue()
        
        self._lock = threading.Lock()
        self._server_socket = None
        self._running = False
        self._threads = []
    
    def start_server(self):
        """Start the coordinator server in the background."""
        if self._running:
            logger.warning("Server already running")
            return
        
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(5)
        
        self._running = True
        
        logger.info(f"Coordinator listening on {self.host}:{self.port}")
        
        # Start accepting connections in a separate thread
        accept_thread = threading.Thread(target=self._accept_workers, daemon=True)
        accept_thread.start()
        self._threads.append(accept_thread)
        
        # Start worker health check thread
        health_thread = threading.Thread(target=self._check_worker_health, daemon=True)
        health_thread.start()
        self._threads.append(health_thread)
    
    def stop_server(self):
        """Stop the coordinator server."""
        logger.info("Stopping coordinator server...")
        self._running = False
        
        # Notify all workers to shutdown
        with self._lock:
            for worker_id, worker in list(self.workers.items()):
                try:
                    Protocol.send_message(worker.socket, MessageType.SHUTDOWN, {})
                    worker.socket.close()
                except:
                    pass
        
        if self._server_socket:
            self._server_socket.close()
        
        logger.info("Coordinator stopped")
    
    def map(
        self,
        func: Callable,
        iterable: List[Any],
        timeout: Optional[float] = None,
        chunk_size: int = 1,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_task_complete: Optional[Callable[[int, Any], None]] = None,
    ) -> List[Any]:
        """
        Distribute function execution across workers (similar to multiprocessing.Pool.map).
        
        Args:
            func: Function to apply to each item
            iterable: List of items to process
            timeout: Maximum time to wait for all results (in seconds)
            chunk_size: Number of items per task (not yet implemented)
            on_progress: Callback function(completed, total) called after each task completes
            on_task_complete: Callback function(task_index, result) called when each task finishes
        
        Returns:
            List of results in the same order as the input iterable
        
        Raises:
            TimeoutError: If timeout is exceeded
        """
        # Start server if not already running
        if not self._running:
            self.start_server()
            time.sleep(0.5)  # Give server time to start
        
        # Create tasks
        tasks = []
        for i, item in enumerate(iterable):
            task = Task(func=func, args=(item,), task_id=f"task-{i}")
            tasks.append(task)
            
            with self._lock:
                self.task_queue.append(task)
                self.pending_tasks[task.task_id] = task
        
        logger.info(f"Created {len(tasks)} tasks")
        
        # Distribute tasks to workers
        self._distribute_tasks()
        
        # Wait for results
        start_time = time.time()
        results = {}
        task_index_map = {task.task_id: i for i, task in enumerate(tasks)}
        
        while len(results) < len(tasks):
            if timeout and (time.time() - start_time) > timeout:
                raise DistributedTimeoutError(f"Timeout exceeded: {len(results)}/{len(tasks)} tasks completed")
            
            try:
                task_id, result, error = self.result_queue.get(timeout=1.0)
                
                if error:
                    logger.error(f"Task {task_id[:8]} failed: {error}")
                    # For now, store None for failed tasks
                    results[task_id] = None
                else:
                    results[task_id] = result
                
                # Call progress callbacks
                completed = len(results)
                total = len(tasks)
                
                if on_progress:
                    try:
                        on_progress(completed, total)
                    except Exception as e:
                        logger.error(f"Progress callback error: {e}")
                
                if on_task_complete:
                    try:
                        task_idx = task_index_map.get(task_id, -1)
                        on_task_complete(task_idx, results[task_id])
                    except Exception as e:
                        logger.error(f"Task complete callback error: {e}")
                    
                if self.verbose:
                    logger.info(f"Progress: {completed}/{total} tasks completed")
                    
            except queue.Empty:
                # Check if we need to redistribute tasks from dead workers
                self._redistribute_failed_tasks()
                continue
        
        # Return results in original order
        ordered_results = [results[task.task_id] for task in tasks]
        
        logger.info(f"All tasks completed in {time.time() - start_time:.2f}s")
        
        return ordered_results
    
    def get_stats(self) -> dict:
        """Get statistics about the coordinator and workers."""
        with self._lock:
            stats = {
                "workers": len([w for w in self.workers.values() if w.is_alive]),
                "tasks_pending": len(self.task_queue) + len(self.pending_tasks),
                "tasks_completed": len(self.completed_tasks),
                "worker_details": [
                    {
                        "name": w.name,
                        "tasks_completed": w.tasks_completed,
                        "tasks_failed": w.tasks_failed,
                        "current_tasks": w.current_tasks,
                        "cpu_percent": w.cpu_percent,
                    }
                    for w in self.workers.values() if w.is_alive
                ]
            }
            
            # Add authentication stats if auth manager exists
            if self.auth_manager:
                stats["authentication"] = self.auth_manager.get_stats()
            
            return stats
    
    def _accept_workers(self):
        """Accept incoming worker connections."""
        self._server_socket.settimeout(1.0)
        
        while self._running:
            try:
                client_socket, address = self._server_socket.accept()
                logger.info(f"New connection from {address}")
                
                # Handle worker in a separate thread
                worker_thread = threading.Thread(
                    target=self._handle_worker,
                    args=(client_socket, address),
                    daemon=True
                )
                worker_thread.start()
                self._threads.append(worker_thread)
                
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Error accepting connection: {e}")
    
    def _handle_worker(self, client_socket: socket.socket, address: tuple):
        """Handle communication with a worker."""
        worker_id = None
        
        try:
            # Receive initial message
            msg_type, payload = Protocol.receive_message(client_socket, timeout=10.0)
            
            if msg_type == MessageType.SUBMIT_JOB:
                self._handle_client_job(client_socket, payload)
                return
            
            if msg_type != MessageType.REGISTER_WORKER:
                logger.error("Expected registration message")
                client_socket.close()
                return
            
            # Extract worker info and password
            worker_name = payload.get("name", "unknown")
            worker_password = payload.get("password")
            
            # Check authentication (only if auth is enabled)
            if self.auth_manager:
                can_connect, reason = self.auth_manager.can_worker_connect(worker_name, worker_password)
                
                if not can_connect:
                    logger.warning(f"Worker {worker_name} from {address} authentication failed: {reason}")
                    Protocol.send_message(client_socket, MessageType.AUTH_FAILED, {
                        "reason": reason
                    })
                    client_socket.close()
                    return
                
                if self.auth_manager.password:
                    logger.info(f"Worker {worker_name} authenticated successfully")
            
            # Register worker
            worker_id = f"worker-{len(self.workers)}-{int(time.time())}"
            worker = WorkerInfo(
                worker_id=worker_id,
                socket=client_socket,
                name=worker_name,
                max_tasks=payload["max_concurrent_tasks"]
            )
            
            with self._lock:
                self.workers[worker_id] = worker
            
            # Register connection with auth manager (only if auth is enabled)
            if self.auth_manager:
                self.auth_manager.register_connection(worker_name)
            
            logger.info(f"Registered worker: {worker.name} (ID: {worker_id})")
            
            # Send registration confirmation
            Protocol.send_message(client_socket, MessageType.WORKER_REGISTERED, {
                "worker_id": worker_id
            })
            
            # Don't call _distribute_tasks() here - it will be called from map()
            # This prevents deadlock between sending tasks and receiving messages
            
            # Listen for messages from worker
            while self._running and worker.is_alive:
                try:
                    msg_type, payload = Protocol.receive_message(client_socket, timeout=5.0)
                except socket.timeout:
                    # No message yet; keep worker alive and try distributing tasks
                    self._distribute_tasks()
                    continue
                
                if msg_type is None:
                    # Connection closed or empty read
                    continue
                
                if msg_type == MessageType.HEARTBEAT:
                    self._handle_heartbeat(worker_id, payload)
                
                elif msg_type == MessageType.TASK_RESULT:
                    self._handle_task_result(worker_id, payload)
                    # After task completion, try to send more tasks
                    self._distribute_tasks()
                
                elif msg_type == MessageType.TASK_ERROR:
                    self._handle_task_error(worker_id, payload)
                    # After task error, try to redistribute
                    self._distribute_tasks()
                
                elif msg_type == MessageType.SHUTDOWN:
                    logger.info(f"Worker {worker.name} disconnecting")
                    break
        except Exception as e:
            logger.error(f"Error handling worker: {e}")
        finally:
            if worker_id:
                with self._lock:
                    if worker_id in self.workers:
                        worker = self.workers[worker_id]
                        worker.is_alive = False
                        # Unregister from auth manager
                        if self.auth_manager:
                            self.auth_manager.unregister_connection(worker.name)
                logger.info(f"Worker {worker_id} disconnected")
            
            try:
                client_socket.close()
            except:
                pass
    
    def _handle_heartbeat(self, worker_id: str, payload: dict):
        """Handle heartbeat message from worker."""
        with self._lock:
            if worker_id in self.workers:
                worker = self.workers[worker_id]
                worker.last_heartbeat = time.time()
                worker.current_tasks = payload.get("current_tasks", 0)
                worker.tasks_completed = payload.get("tasks_completed", 0)
                worker.tasks_failed = payload.get("tasks_failed", 0)
                worker.cpu_percent = payload.get("cpu_percent", 0.0)
                worker.memory_available = payload.get("memory_available", 0)
    
    def _handle_task_result(self, worker_id: str, payload: dict):
        """Handle task result from worker."""
        task_id = payload["task_id"]
        result = payload["result"]
        
        with self._lock:
            if task_id in self.pending_tasks:
                task = self.pending_tasks[task_id]
                task.result = result
                task.status = TaskStatus.COMPLETED
                self.completed_tasks[task_id] = task
                del self.pending_tasks[task_id]
                
                # Update worker stats
                if worker_id in self.workers:
                    worker = self.workers[worker_id]
                    worker.current_tasks = max(0, worker.current_tasks - 1)
        
        # Add result to queue
        self.result_queue.put((task_id, result, None))
        
        # Task distribution now happens in _handle_worker loop
    
    def _handle_task_error(self, worker_id: str, payload: dict):
        """Handle task error from worker."""
        task_id = payload["task_id"]
        error = payload["error"]
        
        logger.error(f"Task {task_id[:8]} failed on worker {worker_id}: {error}")
        
        with self._lock:
            if task_id in self.pending_tasks:
                task = self.pending_tasks[task_id]
                task.status = TaskStatus.FAILED
                task.error = error
                
                # For now, mark as completed with error
                self.completed_tasks[task_id] = task
                del self.pending_tasks[task_id]
                
                # Update worker stats
                if worker_id in self.workers:
                    worker = self.workers[worker_id]
                    worker.current_tasks = max(0, worker.current_tasks - 1)
        
        # Add error to result queue
        self.result_queue.put((task_id, None, error))

    def _handle_client_job(self, client_socket: socket.socket, payload: dict):
        """Handle a client job submission and return results."""
        try:
            func = payload["func"]
            iterable = payload["iterable"]
            timeout = payload.get("timeout")
            chunk_size = payload.get("chunk_size", 1)

            results = self.map(func, iterable, timeout=timeout, chunk_size=chunk_size)

            Protocol.send_message(client_socket, MessageType.JOB_RESULT, {
                "results": results
            })
        except Exception as exc:
            Protocol.send_message(client_socket, MessageType.JOB_ERROR, {
                "error": str(exc)
            })
        finally:
            try:
                client_socket.close()
            except Exception:
                pass
    
    def _distribute_tasks(self):
        """Distribute pending tasks to available workers."""
        with self._lock:
            if not self.task_queue:
                return
            
            available_workers = [
                w for w in self.workers.values()
                if w.is_alive and w.current_tasks < w.max_tasks
            ]
            
            if not available_workers:
                return
            
            # Sort workers by current load (least loaded first)
            available_workers.sort(key=lambda w: w.current_tasks / w.max_tasks)
            
            while self.task_queue and available_workers:
                task = self.task_queue.popleft()
                worker = available_workers[0]
                
                try:
                    # Send task to worker
                    task_data = task.to_dict()
                    Protocol.send_message(worker.socket, MessageType.TASK_ASSIGNMENT, task_data)
                    
                    task.status = TaskStatus.ASSIGNED
                    task.worker_id = worker.worker_id
                    worker.current_tasks += 1
                    
                    logger.debug(f"Assigned task {task.task_id[:8]} to worker {worker.name}")
                    
                    # Re-sort workers
                    available_workers.sort(key=lambda w: w.current_tasks / w.max_tasks)
                    
                    # Remove workers that are now at max capacity
                    available_workers = [
                        w for w in available_workers
                        if w.current_tasks < w.max_tasks
                    ]
                    
                except Exception as e:
                    logger.error(f"Failed to assign task to worker {worker.name}: {e}")
                    worker.is_alive = False
                    # Unregister from auth manager
                    self.auth_manager.unregister_connection(worker.name)
                    # Put task back in queue
                    self.task_queue.appendleft(task)
                    available_workers.remove(worker)
    
    def _check_worker_health(self):
        """Periodically check worker health and mark dead workers."""
        while self._running:
            time.sleep(5.0)
            
            current_time = time.time()
            
            with self._lock:
                for worker_id, worker in self.workers.items():
                    if worker.is_alive:
                        time_since_heartbeat = current_time - worker.last_heartbeat
                        
                        if time_since_heartbeat > self.worker_timeout:
                            logger.warning(f"Worker {worker.name} timed out")
                            worker.is_alive = False
                            
                            # Unregister from auth manager
                            self.auth_manager.unregister_connection(worker.name)
                            
                            # Redistribute its tasks
                            for task_id, task in list(self.pending_tasks.items()):
                                if task.worker_id == worker_id and task.status == TaskStatus.ASSIGNED:
                                    logger.info(f"Redistributing task {task_id[:8]}")
                                    task.status = TaskStatus.PENDING
                                    task.worker_id = None
                                    self.task_queue.append(task)
    
    def _redistribute_failed_tasks(self):
        """Redistribute tasks from failed workers."""
        self._distribute_tasks()
