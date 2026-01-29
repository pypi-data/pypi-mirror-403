"""
Unit tests for authentication module
"""
import pytest
from distributed_compute.auth import AuthManager


class TestAuthManager:
    """Test cases for AuthManager class"""
    
    def test_init_without_password(self):
        """Test initialization without password (auth disabled)"""
        auth = AuthManager()
        assert auth.password is None
        assert auth.active_connections == {}
    
    def test_init_with_password(self):
        """Test initialization with password (auth enabled)"""
        auth = AuthManager(password="testpass123")
        assert auth.password == "testpass123"
        assert auth.active_connections == {}
    
    def test_verify_password_disabled(self):
        """Test password verification when auth is disabled"""
        auth = AuthManager()
        assert auth.verify_password(None) is True
        assert auth.verify_password("anypassword") is True
        assert auth.verify_password("") is True
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        auth = AuthManager(password="correctpass")
        assert auth.verify_password("correctpass") is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        auth = AuthManager(password="correctpass")
        assert auth.verify_password("wrongpass") is False
        assert auth.verify_password("") is False
        assert auth.verify_password(None) is False
    
    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive"""
        auth = AuthManager(password="TestPass123")
        assert auth.verify_password("TestPass123") is True
        assert auth.verify_password("testpass123") is False
        assert auth.verify_password("TESTPASS123") is False
    
    def test_verify_password_special_characters(self):
        """Test password with special characters"""
        auth = AuthManager(password="p@ssw0rd!#$%")
        assert auth.verify_password("p@ssw0rd!#$%") is True
        assert auth.verify_password("p@ssw0rd") is False
    
    def test_can_worker_connect_no_auth(self):
        """Test worker connection when auth is disabled"""
        auth = AuthManager()
        can_connect, reason = auth.can_worker_connect("worker-1", None)
        assert can_connect is True
        assert reason == "Authentication successful"
    
    def test_can_worker_connect_correct_password(self):
        """Test worker connection with correct password"""
        auth = AuthManager(password="secret123")
        can_connect, reason = auth.can_worker_connect("worker-1", "secret123")
        assert can_connect is True
        assert reason == "Authentication successful"
    
    def test_can_worker_connect_wrong_password(self):
        """Test worker connection with wrong password"""
        auth = AuthManager(password="secret123")
        can_connect, reason = auth.can_worker_connect("worker-1", "wrong")
        assert can_connect is False
        assert reason == "Invalid password"
    
    def test_can_worker_connect_no_password_when_required(self):
        """Test worker connection without password when required"""
        auth = AuthManager(password="secret123")
        can_connect, reason = auth.can_worker_connect("worker-1", None)
        assert can_connect is False
        assert reason == "Invalid password"
    
    def test_register_connection_single(self):
        """Test registering a single connection"""
        auth = AuthManager()
        auth.register_connection("worker-1")
        assert "worker-1" in auth.active_connections
        assert auth.active_connections["worker-1"] == 1
    
    def test_register_connection_multiple(self):
        """Test registering multiple connections from same worker"""
        auth = AuthManager()
        auth.register_connection("worker-1")
        auth.register_connection("worker-1")
        auth.register_connection("worker-1")
        assert auth.active_connections["worker-1"] == 3
    
    def test_register_connection_different_workers(self):
        """Test registering connections from different workers"""
        auth = AuthManager()
        auth.register_connection("worker-1")
        auth.register_connection("worker-2")
        auth.register_connection("worker-3")
        assert len(auth.active_connections) == 3
        assert auth.active_connections["worker-1"] == 1
        assert auth.active_connections["worker-2"] == 1
        assert auth.active_connections["worker-3"] == 1
    
    def test_unregister_connection_single(self):
        """Test unregistering a single connection"""
        auth = AuthManager()
        auth.register_connection("worker-1")
        auth.unregister_connection("worker-1")
        assert "worker-1" not in auth.active_connections
    
    def test_unregister_connection_multiple(self):
        """Test unregistering one of multiple connections"""
        auth = AuthManager()
        auth.register_connection("worker-1")
        auth.register_connection("worker-1")
        auth.register_connection("worker-1")
        auth.unregister_connection("worker-1")
        assert auth.active_connections["worker-1"] == 2
    
    def test_unregister_connection_nonexistent(self):
        """Test unregistering a connection that doesn't exist"""
        auth = AuthManager()
        # Should not raise an error
        auth.unregister_connection("nonexistent-worker")
        assert "nonexistent-worker" not in auth.active_connections
    
    def test_get_stats_no_auth(self):
        """Test getting stats when auth is disabled"""
        auth = AuthManager()
        stats = auth.get_stats()
        assert stats["auth_enabled"] is False
        assert stats["active_connections"] == {}
        assert stats["total_workers"] == 0
    
    def test_get_stats_with_auth(self):
        """Test getting stats when auth is enabled"""
        auth = AuthManager(password="test123")
        stats = auth.get_stats()
        assert stats["auth_enabled"] is True
        assert stats["active_connections"] == {}
        assert stats["total_workers"] == 0
    
    def test_get_stats_with_connections(self):
        """Test getting stats with active connections"""
        auth = AuthManager(password="test123")
        auth.register_connection("worker-1")
        auth.register_connection("worker-2")
        auth.register_connection("worker-1")
        
        stats = auth.get_stats()
        assert stats["auth_enabled"] is True
        assert stats["total_workers"] == 2
        assert stats["active_connections"]["worker-1"] == 2
        assert stats["active_connections"]["worker-2"] == 1
    
    def test_generate_password_default_length(self):
        """Test password generation with default length"""
        password = AuthManager.generate_password()
        assert len(password) == 16
        assert isinstance(password, str)
    
    def test_generate_password_custom_length(self):
        """Test password generation with custom length"""
        password = AuthManager.generate_password(32)
        assert len(password) == 32
    
    def test_generate_password_uniqueness(self):
        """Test that generated passwords are unique"""
        passwords = [AuthManager.generate_password() for _ in range(100)]
        assert len(set(passwords)) == 100  # All unique
    
    def test_timing_attack_resistance(self):
        """Test that password comparison is constant-time (timing attack resistant)"""
        import time
        
        auth = AuthManager(password="a" * 100)
        
        # Time comparison with completely wrong password
        start1 = time.perf_counter()
        for _ in range(1000):
            auth.verify_password("b" * 100)
        time1 = time.perf_counter() - start1
        
        # Time comparison with partially correct password
        start2 = time.perf_counter()
        for _ in range(1000):
            auth.verify_password("a" * 99 + "b")
        time2 = time.perf_counter() - start2
        
        # Times should be similar (within 20% variance)
        # This tests constant-time comparison
        ratio = max(time1, time2) / min(time1, time2)
        assert ratio < 1.5, f"Timing ratio too large: {ratio}"
    
    def test_password_with_unicode(self):
        """Test password with unicode characters"""
        auth = AuthManager(password="パスワード123")
        assert auth.verify_password("パスワード123") is True
        assert auth.verify_password("パスワード") is False
    
    def test_empty_password(self):
        """Test with empty password string"""
        auth = AuthManager(password="")
        assert auth.verify_password("") is True
        assert auth.verify_password("anything") is False
    
    def test_very_long_password(self):
        """Test with very long password"""
        long_pass = "a" * 10000
        auth = AuthManager(password=long_pass)
        assert auth.verify_password(long_pass) is True
        assert auth.verify_password(long_pass[:-1]) is False
    
    def test_connection_lifecycle(self):
        """Test full connection lifecycle"""
        auth = AuthManager(password="test123")
        
        # Worker connects
        can_connect, _ = auth.can_worker_connect("worker-1", "test123")
        assert can_connect is True
        
        # Register connection
        auth.register_connection("worker-1")
        assert auth.active_connections["worker-1"] == 1
        
        # Worker reconnects
        auth.register_connection("worker-1")
        assert auth.active_connections["worker-1"] == 2
        
        # Worker disconnects
        auth.unregister_connection("worker-1")
        assert auth.active_connections["worker-1"] == 1
        
        # Worker fully disconnects
        auth.unregister_connection("worker-1")
        assert "worker-1" not in auth.active_connections


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
