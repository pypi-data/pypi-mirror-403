#!/usr/bin/env python3
"""
CLI Authentication Integration Test
"""
import subprocess
import time
import os

print("="*70)
print("CLI AUTHENTICATION TEST")
print("="*70)

# Clean up any existing process on port 5558
os.system("lsof -ti:5558 | xargs kill -9 2>/dev/null")
time.sleep(1)

# Start coordinator WITH password
print("\n[Step 1] Starting coordinator WITH password on port 5558...")
print("Command: distcompute coordinator 5558 --password secretPass123")
coord_proc = subprocess.Popen(
    ['distcompute', 'coordinator', '5558', '--password', 'secretPass123'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)
time.sleep(4)

# Try worker WITHOUT password
print("\n[Step 2] Worker WITHOUT password (should fail)...")
print("Command: distcompute worker localhost 5558 worker-fail")
result = subprocess.run(
    ['distcompute', 'worker', 'localhost', '5558', 'worker-fail'],
    capture_output=True,
    text=True,
    timeout=5
)
if "Authentication failed" in result.stderr or result.returncode != 0:
    print("    ✓ CORRECTLY REJECTED")
else:
    print("    ✗ INCORRECTLY ACCEPTED")
    print(f"    stdout: {result.stdout[:200]}")
    print(f"    stderr: {result.stderr[:200]}")

# Try worker WITH correct password
print("\n[Step 3] Worker WITH correct password (should succeed)...")
print("Command: distcompute worker localhost 5558 worker-ok --password secretPass123")
worker_proc = subprocess.Popen(
    ['distcompute', 'worker', 'localhost', '5558', 'worker-ok', '--password', 'secretPass123'],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)
time.sleep(4)

if worker_proc.poll() is None:
    print("    ✓ CORRECTLY CONNECTED")
    worker_proc.terminate()
else:
    print("    ✗ FAILED TO CONNECT")

# Cleanup
print("\n[Cleanup]")
coord_proc.terminate()
time.sleep(1)
os.system("lsof -ti:5558 | xargs kill -9 2>/dev/null")

print("\n" + "="*70)
print("TEST COMPLETE")
print("="*70)
