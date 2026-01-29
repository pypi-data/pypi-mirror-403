"""
Authentication module for secure coordinator-worker connections.
"""

import hmac
import hashlib
import secrets
from typing import Optional, Dict, Set


class AuthManager:
    """
    Manages authentication for coordinator-worker connections.
    Uses HMAC for constant-time password comparison to prevent timing attacks.
    """
    
    def __init__(self, password: Optional[str] = None):
        """
        Initialize the authentication manager.
        
        Args:
            password: Optional password for authentication. If None, auth is disabled.
        """
        self.password = password
        self.active_connections: Dict[str, int] = {}  # worker_name -> connection_count
    
    def verify_password(self, provided_password: Optional[str]) -> bool:
        """
        Verify if the provided password matches.
        Uses constant-time comparison to prevent timing attacks.
        
        Args:
            provided_password: Password provided by the worker
            
        Returns:
            True if password matches or auth is disabled, False otherwise
        """
        if self.password is None:
            return True  # Auth disabled
        
        if provided_password is None:
            return False
        
        # Use HMAC for constant-time comparison
        return hmac.compare_digest(
            self.password.encode('utf-8'),
            provided_password.encode('utf-8')
        )
    
    def can_worker_connect(self, worker_name: str, password: Optional[str]) -> tuple[bool, str]:
        """
        Check if a worker can connect with the given credentials.
        
        Args:
            worker_name: Name of the worker attempting to connect
            password: Password provided by the worker
            
        Returns:
            Tuple of (can_connect: bool, reason: str)
        """
        if not self.verify_password(password):
            return False, "Invalid password"
        
        return True, "Authentication successful"
    
    def register_connection(self, worker_name: str):
        """Register a new worker connection."""
        if worker_name not in self.active_connections:
            self.active_connections[worker_name] = 0
        self.active_connections[worker_name] += 1
    
    def unregister_connection(self, worker_name: str):
        """Unregister a worker connection."""
        if worker_name in self.active_connections:
            self.active_connections[worker_name] -= 1
            if self.active_connections[worker_name] <= 0:
                del self.active_connections[worker_name]
    
    def get_stats(self) -> dict:
        """Get authentication statistics."""
        return {
            "auth_enabled": self.password is not None,
            "active_connections": dict(self.active_connections),
            "total_workers": len(self.active_connections)
        }
    
    @staticmethod
    def generate_password(length: int = 16) -> str:
        """
        Generate a cryptographically secure random password.
        
        Args:
            length: Length of the password (default: 16 characters)
            
        Returns:
            Secure random password string
        """
        return secrets.token_urlsafe(length)[:length]
