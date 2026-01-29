"""
Example: Distributed machine learning inference across multiple devices.

This example shows how to distribute ML model inference workloads.
"""

import time
import random
from distributed_compute import Coordinator, Worker


def simulate_ml_inference(data_batch):
    """
    Simulate ML model inference on a batch of data.
    
    In a real scenario, this would load a model and run inference.
    """
    # Simulate loading model (cached after first call)
    time.sleep(0.5)
    
    # Simulate inference time
    batch_size = len(data_batch)
    inference_time = batch_size * 0.1  # 100ms per item
    time.sleep(inference_time)
    
    # Return mock predictions
    predictions = [random.choice(['cat', 'dog', 'bird']) for _ in data_batch]
    return predictions


def main_coordinator():
    """Run inference coordinator."""
    print("=== Distributed ML Inference Example ===\n")
    
    # Initialize coordinator
    coordinator = Coordinator(port=5000, verbose=True)
    coordinator.start_server()
    
    print("Coordinator started. Waiting for worker devices...")
    print("Start workers on other devices with:")
    print("  python ml_inference.py --worker <coordinator-ip>\n")
    
    time.sleep(5)
    
    # Simulate batches of images/data to process
    num_batches = 50
    batch_size = 10
    data_batches = [[f"image_{i*batch_size + j}" for j in range(batch_size)] 
                    for i in range(num_batches)]
    
    print(f"Processing {num_batches} batches ({num_batches * batch_size} items total)...\n")
    
    start_time = time.time()
    
    # Distribute inference across workers
    results = coordinator.map(simulate_ml_inference, data_batches, timeout=300)
    
    elapsed = time.time() - start_time
    
    # Flatten results
    all_predictions = [pred for batch in results for pred in batch]
    
    print(f"\n✓ Inference completed!")
    print(f"  Processed: {len(all_predictions)} items")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Throughput: {len(all_predictions)/elapsed:.2f} items/sec")
    
    stats = coordinator.get_stats()
    print(f"\nWorker Statistics:")
    for worker in stats['worker_details']:
        print(f"  - {worker['name']}: {worker['tasks_completed']} batches processed")
    
    coordinator.stop_server()


def main_worker(coordinator_host):
    """Run inference worker."""
    print(f"Starting inference worker...")
    print(f"Connecting to coordinator at {coordinator_host}:5000\n")
    
    worker = Worker(
        coordinator_host=coordinator_host,
        coordinator_port=5000,
        max_concurrent_tasks=3,  # Process up to 3 batches concurrently
        name=f"ml-worker"
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
