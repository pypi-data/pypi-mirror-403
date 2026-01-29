#!/usr/bin/env python3
"""
Run computation on the distributed cluster.
Make sure coordinator and workers are already running!
"""

from distributed_compute import Coordinator
import time

print("\n🎯 Connecting to cluster...\n")

# Connect to existing coordinator (don't start new one)
coordinator = Coordinator(port=5555, verbose=False)

# Give it a moment
time.sleep(1)

# Check cluster status
stats = coordinator.get_stats()
print(f"✅ Connected! Workers available: {stats['workers']}\n")

if stats['workers'] == 0:
    print("❌ No workers connected! Start workers first with: ./run_real_demo.sh")
    exit(1)

print(f"📊 Running Monte Carlo Pi estimation...")
print(f"   30 tasks × 10M samples = 300M calculations\n")

# Define the heavy computation
def compute_task(iterations):
    """Monte Carlo simulation to estimate Pi - VERY CPU intensive"""
    import random
    import math
    
    samples = 10000000  # 10 million samples per task
    inside_circle = 0
    
    for _ in range(samples):
        x = random.random()
        y = random.random()
        if x*x + y*y <= 1.0:
            inside_circle += 1
    
    pi_estimate = 4.0 * inside_circle / samples
    return pi_estimate

# Run the computation
num_tasks = 30
data = list(range(1, num_tasks + 1))

start_time = time.time()
print("⏳ Processing...")

# Monitor progress
import threading

def show_progress():
    while True:
        stats = coordinator.get_stats()
        completed = stats['tasks_completed']
        pending = stats['tasks_pending']
        if completed >= num_tasks:
            break
        
        percent = int((completed / num_tasks) * 100)
        bar = '█' * (percent // 2) + '░' * (50 - percent // 2)
        print(f"\r[{bar}] {percent}% ({completed}/{num_tasks})", end='', flush=True)
        time.sleep(0.5)

progress_thread = threading.Thread(target=show_progress, daemon=True)
progress_thread.start()

# Run the actual computation
results = coordinator.map(compute_task, data, timeout=300)
elapsed = time.time() - start_time

# Final results
print(f"\r[{'█' * 50}] 100% ({num_tasks}/{num_tasks})\n")
print(f"✅ Complete!\n")

stats = coordinator.get_stats()
print(f"📈 Results:")
print(f"   Total tasks:     {num_tasks}")
print(f"   Time elapsed:    {elapsed:.1f}s")
print(f"   Throughput:      {num_tasks/elapsed:.1f} tasks/sec")
print(f"   Pi estimates:    {results[:5]}...")
print(f"   Avg Pi:          {sum(results)/len(results):.7f} (actual: 3.1415927)")

if stats.get('worker_details'):
    print(f"\n💻 Worker Performance:")
    for w in stats['worker_details']:
        print(f"   {w['name']:<15} {w['tasks_completed']} tasks")

print()
