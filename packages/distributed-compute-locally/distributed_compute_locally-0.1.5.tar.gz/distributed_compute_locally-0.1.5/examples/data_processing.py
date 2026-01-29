"""
Example: Distributed data processing pipeline.

This example demonstrates how to use the library for parallel data processing.
"""

import time
import json
import random
from distributed_compute import Coordinator, Worker


def process_data_chunk(chunk):
    """
    Process a chunk of data (e.g., log parsing, data transformation).
    
    This simulates ETL operations on data.
    """
    results = []
    
    for item in chunk:
        # Simulate parsing/transformation
        time.sleep(0.05)  # 50ms per item
        
        processed = {
            'id': item['id'],
            'value': item['value'] * 2,
            'processed_at': time.time(),
            'status': 'completed'
        }
        results.append(processed)
    
    return results


def aggregate_results(results):
    """Aggregate results from all workers."""
    all_items = [item for chunk in results for item in chunk]
    
    total_value = sum(item['value'] for item in all_items)
    avg_value = total_value / len(all_items)
    
    return {
        'total_items': len(all_items),
        'total_value': total_value,
        'average_value': avg_value,
    }


def main_coordinator():
    """Run data processing coordinator."""
    print("=== Distributed Data Processing Example ===\n")
    
    # Initialize coordinator
    coordinator = Coordinator(port=5000, verbose=False)
    coordinator.start_server()
    
    print("Coordinator started. Waiting for workers...\n")
    time.sleep(5)
    
    # Generate sample data
    num_items = 1000
    chunk_size = 50
    
    data = [{'id': i, 'value': random.randint(1, 100)} for i in range(num_items)]
    
    # Split into chunks
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    
    print(f"Processing {num_items} items in {len(chunks)} chunks...\n")
    
    start_time = time.time()
    
    # Distribute processing
    results = coordinator.map(process_data_chunk, chunks, timeout=300)
    
    # Aggregate results
    summary = aggregate_results(results)
    
    elapsed = time.time() - start_time
    
    print(f"\n✓ Processing completed!")
    print(f"  Items processed: {summary['total_items']}")
    print(f"  Total value: {summary['total_value']}")
    print(f"  Average value: {summary['average_value']:.2f}")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Throughput: {summary['total_items']/elapsed:.2f} items/sec")
    
    stats = coordinator.get_stats()
    print(f"\nWorkers: {stats['workers']} active")
    for worker in stats['worker_details']:
        print(f"  - {worker['name']}: {worker['tasks_completed']} chunks")
    
    coordinator.stop_server()


def main_worker(coordinator_host):
    """Run data processing worker."""
    print(f"Starting data processing worker...")
    print(f"Connecting to {coordinator_host}:5000\n")
    
    worker = Worker(
        coordinator_host=coordinator_host,
        coordinator_port=5000,
        max_concurrent_tasks=4,
        name=f"data-worker"
    )
    
    try:
        worker.start()
    except KeyboardInterrupt:
        print("\nWorker stopped")
        worker.stop()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        coordinator_host = sys.argv[2] if len(sys.argv) > 2 else 'localhost'
        main_worker(coordinator_host)
    else:
        main_coordinator()
