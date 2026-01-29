"""
Integration tests for coordinator-worker authentication
"""
import pytest
import threading
import time
from distributed_compute import Coordinator, Worker
from distributed_compute.exceptions import WorkerConnectionError


class TestCoordinatorWorkerAuth:
    """Integration tests for authentication between coordinator and workers"""
    
    @pytest.fixture
    def coordinator_no_auth(self):
        """Fixture: Coordinator without authentication"""
        coord = Coordinator(port=5560, password=None)
        coord.start_server()
        time.sleep(0.5)
        yield coord
        coord.stop_server()
        time.sleep(0.5)
    
    @pytest.fixture
    def coordinator_with_auth(self):
        """Fixture: Coordinator with authentication"""
        coord = Coordinator(port=5561, password="testpass123")
        coord.start_server()
        time.sleep(0.5)
        yield coord
        coord.stop_server()
        time.sleep(0.5)
    
    def test_worker_connects_no_auth_required(self, coordinator_no_auth):
        """Test worker connects when no auth is required"""
        worker = Worker(
            coordinator_host="localhost",
            coordinator_port=5560,
            name="test-worker"
        )
        
        thread = threading.Thread(target=worker.start, daemon=True)
        thread.start()
        time.sleep(2)
        
        assert worker.worker_id is not None
        assert worker.running is True
        
        worker.stop()
        time.sleep(0.5)
    
    def test_worker_connects_with_correct_password(self, coordinator_with_auth):
        """Test worker connects with correct password"""
        worker = Worker(
            coordinator_host="localhost",
            coordinator_port=5561,
            name="test-worker",
            password="testpass123"
        )
        
        thread = threading.Thread(target=worker.start, daemon=True)
        thread.start()
        time.sleep(2)
        
        assert worker.worker_id is not None
        assert worker.running is True
        
        worker.stop()
        time.sleep(0.5)
    
    def test_worker_rejected_wrong_password(self, coordinator_with_auth):
        """Test worker is rejected with wrong password"""
        worker = Worker(
            coordinator_host="localhost",
            coordinator_port=5561,
            name="test-worker",
            password="wrongpassword"
        )
        
        with pytest.raises(WorkerConnectionError, match="Authentication failed"):
            worker.start()
        
        time.sleep(0.5)
    
    def test_worker_rejected_no_password_when_required(self, coordinator_with_auth):
        """Test worker is rejected without password when required"""
        worker = Worker(
            coordinator_host="localhost",
            coordinator_port=5561,
            name="test-worker"
        )
        
        with pytest.raises(WorkerConnectionError, match="Authentication failed"):
            worker.start()
        
        time.sleep(0.5)
    
    def test_multiple_workers_with_auth(self, coordinator_with_auth):
        """Test multiple workers can connect with correct password"""
        workers = []
        threads = []
        
        for i in range(3):
            worker = Worker(
                coordinator_host="localhost",
                coordinator_port=5561,
                name=f"worker-{i}",
                password="testpass123"
            )
            workers.append(worker)
            
            thread = threading.Thread(target=worker.start, daemon=True)
            thread.start()
            threads.append(thread)
        
        time.sleep(3)
        
        # All workers should be connected
        for worker in workers:
            assert worker.worker_id is not None
            assert worker.running is True
        
        # Check coordinator stats
        stats = coordinator_with_auth.get_stats()
        assert stats["workers"] == 3
        
        # Cleanup
        for worker in workers:
            worker.stop()
        time.sleep(0.5)
    
    def test_mixed_auth_attempts(self, coordinator_with_auth):
        """Test mix of successful and failed auth attempts"""
        # Worker with correct password (should succeed)
        worker1 = Worker(
            coordinator_host="localhost",
            coordinator_port=5561,
            name="worker-good",
            password="testpass123"
        )
        thread1 = threading.Thread(target=worker1.start, daemon=True)
        thread1.start()
        time.sleep(2)
        
        assert worker1.worker_id is not None
        assert worker1.running is True
        
        # Worker with wrong password (should fail)
        worker2 = Worker(
            coordinator_host="localhost",
            coordinator_port=5561,
            name="worker-bad",
            password="wrongpass"
        )
        
        with pytest.raises(WorkerConnectionError, match="Authentication failed"):
            worker2.start()
        
        # First worker should still be connected
        assert worker1.running is True
        
        stats = coordinator_with_auth.get_stats()
        assert stats["workers"] == 1
        
        worker1.stop()
        time.sleep(0.5)
    
    def test_auth_stats_tracking(self, coordinator_with_auth):
        """Test that auth manager tracks connections correctly"""
        workers = []
        threads = []
        
        # Connect 3 workers
        for i in range(3):
            worker = Worker(
                coordinator_host="localhost",
                coordinator_port=5561,
                name=f"worker-{i}",
                password="testpass123"
            )
            workers.append(worker)
            
            thread = threading.Thread(target=worker.start, daemon=True)
            thread.start()
            threads.append(thread)
        
        time.sleep(3)
        
        # Check auth stats
        stats = coordinator_with_auth.get_stats()
        assert "authentication" in stats
        assert stats["authentication"]["auth_enabled"] is True
        assert stats["authentication"]["total_workers"] == 3
        
        # Disconnect one worker
        workers[0].stop()
        time.sleep(2)  # Increased wait time for cleanup
        
        # Check updated stats
        stats = coordinator_with_auth.get_stats()
        assert stats["authentication"]["total_workers"] == 2
        
        # Cleanup
        for worker in workers[1:]:
            worker.stop()
        time.sleep(0.5)
    
    def test_worker_reconnect_with_password(self, coordinator_with_auth):
        """Test worker can reconnect with password after disconnect"""
        worker = Worker(
            coordinator_host="localhost",
            coordinator_port=5561,
            name="test-worker",
            password="testpass123"
        )
        
        # First connection
        thread = threading.Thread(target=worker.start, daemon=True)
        thread.start()
        time.sleep(2)
        assert worker.worker_id is not None
        first_id = worker.worker_id
        
        # Disconnect
        worker.stop()
        time.sleep(1)
        
        # Reconnect
        worker = Worker(
            coordinator_host="localhost",
            coordinator_port=5561,
            name="test-worker",
            password="testpass123"
        )
        thread = threading.Thread(target=worker.start, daemon=True)
        thread.start()
        time.sleep(2)
        
        assert worker.worker_id is not None
        assert worker.worker_id != first_id  # New ID assigned
        
        worker.stop()
        time.sleep(0.5)
    
    def test_case_sensitive_password(self, coordinator_with_auth):
        """Test that password is case-sensitive"""
        # Correct case
        worker1 = Worker(
            coordinator_host="localhost",
            coordinator_port=5561,
            name="worker-1",
            password="testpass123"
        )
        thread1 = threading.Thread(target=worker1.start, daemon=True)
        thread1.start()
        time.sleep(2)
        assert worker1.worker_id is not None
        worker1.stop()
        time.sleep(0.5)
        
        # Wrong case
        worker2 = Worker(
            coordinator_host="localhost",
            coordinator_port=5561,
            name="worker-2",
            password="TestPass123"
        )
        with pytest.raises(WorkerConnectionError, match="Authentication failed"):
            worker2.start()
        time.sleep(0.5)
    
    def test_coordinator_auth_disabled_by_default(self):
        """Test that coordinator has auth disabled when no password provided"""
        coord = Coordinator(port=5562)
        coord.start_server()
        time.sleep(0.5)
        
        # Worker should connect without password
        worker = Worker(
            coordinator_host="localhost",
            coordinator_port=5562,
            name="test-worker"
        )
        thread = threading.Thread(target=worker.start, daemon=True)
        thread.start()
        time.sleep(2)
        
        assert worker.worker_id is not None
        
        worker.stop()
        coord.stop_server()
        time.sleep(0.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
