"""
Network protocol definitions for communication between coordinator and workers.
"""

import json
import struct
import socket
import cloudpickle


class MessageType:
    """Message types for coordinator-worker communication."""
    REGISTER_WORKER = "register_worker"
    WORKER_REGISTERED = "worker_registered"
    AUTH_FAILED = "auth_failed"
    HEARTBEAT = "heartbeat"
    TASK_ASSIGNMENT = "task_assignment"
    TASK_RESULT = "task_result"
    TASK_ERROR = "task_error"
    WORKER_STATUS = "worker_status"
    SHUTDOWN = "shutdown"
    SUBMIT_JOB = "submit_job"
    JOB_RESULT = "job_result"
    JOB_ERROR = "job_error"


class Protocol:
    """Handles message serialization and deserialization."""
    
    @staticmethod
    def serialize_message(message_type: str, payload: dict) -> bytes:
        """
        Serialize a message with type and payload.
        
        Format: [4 bytes length][message type][payload]
        """
        message = {
            "type": message_type,
            "payload": payload
        }
        
        # Use cloudpickle to serialize the entire message (supports functions)
        serialized = cloudpickle.dumps(message)
        
        # Prepend length as 4-byte integer
        length = struct.pack('!I', len(serialized))
        
        return length + serialized
    
    @staticmethod
    def deserialize_message(data: bytes) -> tuple:
        """
        Deserialize a message into type and payload.
        
        Returns: (message_type, payload)
        """
        message = cloudpickle.loads(data)
        return message["type"], message["payload"]
    
    @staticmethod
    def send_message(sock: socket.socket, message_type: str, payload: dict):
        """Send a message through a socket."""
        data = Protocol.serialize_message(message_type, payload)
        sock.sendall(data)
    
    @staticmethod
    def receive_message(sock: socket.socket, timeout: float = None) -> tuple:
        """
        Receive a message from a socket.
        
        Returns: (message_type, payload)
        """
        if timeout:
            sock.settimeout(timeout)
        
        # Read the message length (4 bytes)
        length_data = Protocol._recv_exact(sock, 4)
        if not length_data:
            return None, None
        
        length = struct.unpack('!I', length_data)[0]
        
        # Read the message data
        message_data = Protocol._recv_exact(sock, length)
        if not message_data:
            return None, None
        
        return Protocol.deserialize_message(message_data)
    
    @staticmethod
    def _recv_exact(sock: socket.socket, num_bytes: int) -> bytes:
        """Receive exactly num_bytes from socket."""
        data = b''
        while len(data) < num_bytes:
            chunk = sock.recv(num_bytes - len(data))
            if not chunk:
                return None
            data += chunk
        return data
