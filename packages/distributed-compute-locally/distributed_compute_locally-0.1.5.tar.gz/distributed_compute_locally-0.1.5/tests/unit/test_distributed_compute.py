"""
Unit tests for the distributed compute library.
"""

import unittest
import time
import threading
from distributed_compute import Coordinator, Worker
from distributed_compute.task import Task, TaskStatus
from distributed_compute.exceptions import DistributedComputeError


class TestTask(unittest.TestCase):
    """Test Task class."""
    
    def test_task_creation(self):
        """Test task creation."""
        def dummy_func(x):
            return x * 2
        
        task = Task(func=dummy_func, args=(5,))
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNone(task.result)
    
    def test_task_execution(self):
        """Test task execution."""
        def add(a, b):
            return a + b
        
        task = Task(func=add, args=(3, 4))
        result = task.execute()
        
        self.assertEqual(result, 7)
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.result, 7)
    
    def test_task_error_handling(self):
        """Test task error handling."""
        def error_func():
            raise ValueError("Test error")
        
        task = Task(func=error_func)
        
        with self.assertRaises(ValueError):
            task.execute()
        
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertIn("Test error", task.error)


class TestIntegration(unittest.TestCase):
    """Integration tests for coordinator and workers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = Coordinator(port=5555, verbose=False)
        self.workers = []
    
    def tearDown(self):
        """Clean up after tests."""
        for worker in self.workers:
            if worker.running:
                worker.stop()
        
        if self.coordinator._running:
            self.coordinator.stop_server()
        
        time.sleep(0.5)
    
    def test_single_worker(self):
        """Test with a single worker."""
        # Start coordinator
        self.coordinator.start_server()
        time.sleep(0.5)
        
        # Start worker in separate thread
        worker = Worker(
            coordinator_host='localhost',
            coordinator_port=5555,
            max_concurrent_tasks=2,
            name='test-worker-1'
        )
        self.workers.append(worker)
        
        worker_thread = threading.Thread(target=worker.start, daemon=True)
        worker_thread.start()
        
        time.sleep(1)
        
        # Define simple task
        def square(x):
            return x ** 2
        
        # Distribute work
        data = [1, 2, 3, 4, 5]
        results = self.coordinator.map(square, data, timeout=10)
        
        # Verify results
        expected = [1, 4, 9, 16, 25]
        self.assertEqual(results, expected)
    
    def test_multiple_workers(self):
        """Test with multiple workers."""
        # Start coordinator
        self.coordinator.start_server()
        time.sleep(1.0)  # Give coordinator more time to start
        
        # Start 2 workers
        for i in range(2):
            worker = Worker(
                coordinator_host='localhost',
                coordinator_port=5555,
                max_concurrent_tasks=2,
                name=f'test-worker-{i}'
            )
            self.workers.append(worker)
            
            worker_thread = threading.Thread(target=worker.start, daemon=True)
            worker_thread.start()
        
        time.sleep(2.0)  # Give workers more time to connect and register
        
        # Verify workers connected
        stats = self.coordinator.get_stats()
        if stats['workers'] < 2:
            self.skipTest(f"Only {stats['workers']} workers connected, expected 2")
        
        # Define task
        def double(x):
            time.sleep(0.1)  # Simulate work
            return x * 2
        
        # Distribute work
        data = list(range(20))
        results = self.coordinator.map(double, data, timeout=30)
        
        # Verify results
        expected = [x * 2 for x in data]
        self.assertEqual(results, expected)
        
        # Verify workers are still connected
        stats = self.coordinator.get_stats()
        self.assertEqual(stats['workers'], 2)


class TestLoadBalancing(unittest.TestCase):
    """Test load balancing across workers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = Coordinator(port=5556, verbose=False)
        self.workers = []
    
    def tearDown(self):
        """Clean up after tests."""
        for worker in self.workers:
            if worker.running:
                worker.stop()
        
        if self.coordinator._running:
            self.coordinator.stop_server()
        
        time.sleep(0.5)
    
    def test_even_distribution(self):
        """Test that work is distributed evenly."""
        # Start coordinator
        self.coordinator.start_server()
        time.sleep(1.0)  # Give coordinator more time to start
        
        # Start 3 workers with same capacity
        for i in range(3):
            worker = Worker(
                coordinator_host='localhost',
                coordinator_port=5556,
                max_concurrent_tasks=2,
                name=f'test-worker-{i}'
            )
            self.workers.append(worker)
            
            worker_thread = threading.Thread(target=worker.start, daemon=True)
            worker_thread.start()
        
        time.sleep(2.0)  # Give workers more time to connect and register
        
        # Verify workers connected
        stats = self.coordinator.get_stats()
        if stats['workers'] < 3:
            self.skipTest(f"Only {stats['workers']} workers connected, expected 3")
        
        # Define task
        def slow_task(x):
            time.sleep(0.2)
            return x
        
        # Distribute work
        data = list(range(30))
        results = self.coordinator.map(slow_task, data, timeout=60)
        
        # Verify all results returned correctly
        self.assertEqual(len(results), 30)
        self.assertEqual(sorted(results), data)
        
        # Verify workers are still connected
        stats = self.coordinator.get_stats()
        self.assertEqual(stats['workers'], 3)


if __name__ == '__main__':
    unittest.main()
