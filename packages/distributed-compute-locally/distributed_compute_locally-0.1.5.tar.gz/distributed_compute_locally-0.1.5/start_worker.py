#!/usr/bin/env python3
"""
Start a worker node - Run this in a separate terminal/machine
Usage: python3 start_worker.py [worker-name] [coordinator-host]
"""

import sys
from distributed_compute import Worker

# Get worker name from args or use default
worker_name = sys.argv[1] if len(sys.argv) > 1 else "worker-1"
coordinator_host = sys.argv[2] if len(sys.argv) > 2 else "localhost"

print(f"\n{'='*60}")
print(f"🔧 WORKER: {worker_name}")
print(f"{'='*60}\n")

worker = Worker(
    coordinator_host=coordinator_host,
    coordinator_port=5555,
    max_concurrent_tasks=2,
    name=worker_name
)

print(f"→ Connecting to coordinator at {coordinator_host}:5555...\n")

try:
    worker.start(block=True)
except KeyboardInterrupt:
    print(f"\n\n✅ Worker {worker_name} stopped")
    print(f"   Total tasks completed: {worker.tasks_completed}\n")
