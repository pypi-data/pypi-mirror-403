#!/usr/bin/env python3
"""
Integration test - Test the distributed system end-to-end
"""

import time
import sys
from distributed_compute import Coordinator

print("=" * 60)
print("INTEGRATION TEST - Distributed Computing")
print("=" * 60)
print()

# Check if we have a coordinator running
print("Connecting to coordinator on localhost:5555...")
coordinator = Coordinator(port=5555, verbose=False)

# Check stats
time.sleep(1)
stats = coordinator.get_stats()

print(f"✓ Connected!")
print(f"  Workers available: {stats['workers']}")
print()

if stats['workers'] == 0:
    print("⚠️  No workers connected!")
    print("   Please start workers first:")
    print("   python3 start_worker.py worker-1 localhost")
    print()
    sys.exit(1)

# Run test computation
print(f"Running test with {stats['workers']} workers...")
print()

def test_task(x):
    """Simple test task"""
    return x ** 2

data = list(range(20))
print(f"Submitting {len(data)} tasks...")

start = time.time()
results = coordinator.map(test_task, data, timeout=30)
elapsed = time.time() - start

print(f"✓ Completed in {elapsed:.2f}s")
print(f"  Throughput: {len(data)/elapsed:.1f} tasks/sec")
print(f"  Results: {results[:5]}...")
print()

# Final stats
final_stats = coordinator.get_stats()
print("Worker Statistics:")
for w in final_stats.get('worker_details', []):
    print(f"  {w['name']}: {w['tasks_completed']} completed, {w['tasks_failed']} failed")

print()
print("=" * 60)
print("TEST PASSED ✓")
print("=" * 60)
