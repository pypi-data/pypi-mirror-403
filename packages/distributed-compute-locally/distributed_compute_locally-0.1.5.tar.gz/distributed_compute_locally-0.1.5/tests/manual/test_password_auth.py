#!/usr/bin/env python3
"""
Quick test script for password authentication
"""
from distributed_compute import Coordinator, Worker
import time
import threading

print("=" * 60)
print("Testing Password Authentication")
print("=" * 60)

# Test 1: Coordinator with password
print("\n[Test 1] Starting coordinator with password 'testpass123'...")
coordinator = Coordinator(port=5556, password="testpass123", verbose=True)
coordinator.start_server()
time.sleep(1)

# Test 2: Worker with correct password
print("\n[Test 2] Starting worker WITH correct password...")
worker1 = Worker(
    coordinator_host="localhost",
    coordinator_port=5556,
    name="worker-correct",
    password="testpass123"
)
thread1 = threading.Thread(target=worker1.start, daemon=True)
thread1.start()
time.sleep(2)

if worker1.worker_id:
    print(f"✓ Worker 1 connected successfully! ID: {worker1.worker_id}")
else:
    print("✗ Worker 1 failed to connect")

# Test 3: Worker with wrong password
print("\n[Test 3] Starting worker WITH wrong password...")
worker2 = Worker(
    coordinator_host="localhost",
    coordinator_port=5556,
    name="worker-wrong",
    password="wrongpassword"
)
try:
    worker2.start()
    if worker2.worker_id:
        print(f"✗ Worker 2 connected (SHOULD HAVE FAILED)! ID: {worker2.worker_id}")
    else:
        print("✓ Worker 2 correctly rejected")
except Exception as e:
    print(f"✓ Worker 2 correctly rejected: {e}")

# Test 4: Worker without password
print("\n[Test 4] Starting worker WITHOUT password...")
worker3 = Worker(
    coordinator_host="localhost",
    coordinator_port=5556,
    name="worker-nopass"
)
try:
    worker3.start()
    if worker3.worker_id:
        print(f"✗ Worker 3 connected (SHOULD HAVE FAILED)! ID: {worker3.worker_id}")
    else:
        print("✓ Worker 3 correctly rejected")
except Exception as e:
    print(f"✓ Worker 3 correctly rejected: {e}")

time.sleep(1)

# Cleanup
print("\n[Cleanup] Stopping coordinator...")
coordinator.stop_server()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
