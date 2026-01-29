"""
Basic usage example of the distributed compute library.
"""

import time
from distributed_compute import Coordinator, Worker


def expensive_computation(x):
    """Simulate an expensive computation."""
    time.sleep(2)  # Simulate work
    result = sum(range(x * 1000)) % 10000
    return result


def main_coordinator():
    """Run as coordinator (main device)."""
    print("Starting coordinator...")
    
    coordinator = Coordinator(port=5000, verbose=True)
    coordinator.start_server()
    
    print("\nWaiting for workers to connect...")
    print("Start worker nodes with: python basic_usage.py --worker")
    
    time.sleep(5)  # Wait for workers to connect
    
    # Prepare work
    data = list(range(1, 21))  # 20 tasks
    print(f"\nDistributing {len(data)} tasks...")
    
    start_time = time.time()
    
    # Distribute computation
    results = coordinator.map(expensive_computation, data, timeout=120)
    
    elapsed = time.time() - start_time
    
    print(f"\nAll tasks completed!")
    print(f"Results: {results}")
    print(f"Total time: {elapsed:.2f}s")
    print(f"\nStats: {coordinator.get_stats()}")
    
    coordinator.stop_server()


def main_worker(coordinator_host='localhost'):
    """Run as worker (secondary device)."""
    print(f"Starting worker and connecting to {coordinator_host}:5000...")
    
    worker = Worker(
        coordinator_host=coordinator_host,
        coordinator_port=5000,
        max_concurrent_tasks=2,
        name=f"worker-example"
    )
    
    try:
        worker.start()
    except KeyboardInterrupt:
        print("\nWorker stopped by user")
        worker.stop()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        # Get coordinator host if provided
        coordinator_host = sys.argv[2] if len(sys.argv) > 2 else 'localhost'
        main_worker(coordinator_host)
    else:
        main_coordinator()
