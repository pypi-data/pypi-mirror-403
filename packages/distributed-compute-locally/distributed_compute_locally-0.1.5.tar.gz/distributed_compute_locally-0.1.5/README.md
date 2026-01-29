[![PyPI](https://img.shields.io/pypi/v/distributed-compute-locally.svg)](https://pypi.org/project/distributed-compute-locally/) [![Downloads](https://static.pepy.tech/badge/distributed-compute-locally)](https://pepy.tech/project/distributed-compute-locally) [![Downloads](https://static.pepy.tech/badge/distributed-compute-locally/month)](https://pepy.tech/project/distributed-compute-locally) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# Distributed Compute

A Python library for distributing computational workloads across multiple devices on a local network. Turn your spare laptops, desktops, and servers into a unified computing cluster with just a few commands.

Distributed Compute allows you to easily harness the power of multiple machines to process large workloads in parallel. Whether you're training ML models, processing data, or running simulations, this library makes distributed computing accessible without complex cluster management tools.

## Features

- **Simple Setup** - Get started with just 2 commands
- **Interactive CLI** - Beautiful terminal interface with Rich UI (v0.1.4+)
- **Live Worker Stats** - Monitor CPU usage, task counts, and active workers
- **Automatic Load Balancing** - Tasks distributed to least-loaded workers
- **Fault Tolerance** - Automatic task redistribution on worker failure
- **Real-time Monitoring** - Live progress tracking and status updates
- **Clean API** - Pythonic interface similar to `multiprocessing.Pool`
- **Plug & Play** - No complex configuration required

## Installation

Install via pip (Python 3.7+):

```bash
pip install distributed-compute-locally
```

## Quick Start

### 1. Start the Coordinator

On your main machine:

```bash
distcompute coordinator
```

This starts an **interactive coordinator** with a beautiful CLI where you can run commands, check status, and execute tasks directly.

### 2. Connect Workers

On each worker machine (laptops, desktops, etc.):

```bash
distcompute worker <coordinator-ip>
```

Or on the same machine for local testing:
```bash
distcompute worker
# Defaults to localhost
```

Example with remote coordinator:
```bash
distcompute worker 192.168.1.100
```

### 3. Run Your Computation

```python
from distributed_compute import Coordinator

# Initialize coordinator
coordinator = Coordinator(port=5555)
coordinator.start()

# Define your compute function
def heavy_computation(x):
    return x ** 2

# Distribute work across all connected workers
results = coordinator.map(heavy_computation, range(1000))
print(results)  # [0, 1, 4, 9, 16, ...]
```

That's it! Your computation is now running across all connected machines.

## Usage Examples

### Running the Demo

See it in action with the built-in demo:

```bash
distcompute demo
```

This runs a Monte Carlo Pi estimation across 2 local workers with beautiful progress visualization.

### Basic Usage

```python
from distributed_compute import Coordinator

# Start coordinator
coordinator = Coordinator(port=5555)
coordinator.start()

# Simple map operation
def square(x):
    return x ** 2

results = coordinator.map(square, range(100))
```

### Progress Tracking (New in v0.1.2!)

Track computation progress in real-time with callbacks:

```python
from distributed_compute import Coordinator

coordinator = Coordinator(port=5555)
coordinator.start()

def process_task(x):
    return x ** 2

# Progress bar callback
def show_progress(completed, total):
    percent = (completed / total) * 100
    print(f"Progress: {completed}/{total} ({percent:.1f}%)")

# Per-task callback
def on_task_done(task_idx, result):
    print(f"Task {task_idx} completed: {result}")

results = coordinator.map(
    process_task, 
    range(100),
    on_progress=show_progress,      # Called after each task
    on_task_complete=on_task_done   # Called with task details
)
```

See `examples/progress_callback_example.py` for more advanced usage including ETA calculation and custom progress trackers.

### ML Model Inference

```python
from distributed_compute import Coordinator

coordinator = Coordinator(port=5555)
coordinator.start()

def predict(data_batch):
    # Your ML inference code
    return model.predict(data_batch)

# Distribute inference across workers
predictions = coordinator.map(predict, data_batches)
```

### Data Processing Pipeline

```python
from distributed_compute import Coordinator

coordinator = Coordinator(port=5555)
coordinator.start()

def process_file(filepath):
    # Your data processing logic
    data = load_file(filepath)
    result = transform(data)
    return result

# Process files in parallel
results = coordinator.map(process_file, file_list)
```

## CLI Commands

The `distcompute` command provides several options:

```bash
# Start coordinator (with interactive mode)
distcompute coordinator [port]

# Connect worker (host defaults to localhost)
distcompute worker [host] [port] [name]

# Run demo
distcompute demo
```

### Interactive Coordinator Mode (New in v0.1.4!)

When you start the coordinator, it now launches an **interactive terminal** with a beautiful CLI interface (powered by Rich and prompt_toolkit):

```bash
distcompute coordinator
```

You'll see a prompt where you can run commands:

```
distcompute> help

Available Commands:
  run <file.py>  - Execute a task file across workers
  status         - Show cluster status with worker stats
  help           - Show this help message
  exit           - Shutdown coordinator
```

**Example task file** (`my_task.py`):
```python
def square(x):
    return x * x

TASK_FUNC = square
ITERABLE = range(20)
```

**Running tasks interactively**:
```
distcompute> status
┌──────────────────────────────────────┐
│         Cluster Status              │
├────────────────┬────────────────────┤
│ Metric         │ Value              │
├────────────────┼────────────────────┤
│ Workers        │ 2                  │
│ Tasks Pending  │ 0                  │
│ Tasks Completed│ 20                 │
└────────────────┴────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              Worker Details                             │
├──────────────┬────────────┬─────────────┬──────────────┤
│ Worker       │ CPU %      │ Tasks Done  │ Active       │
├──────────────┼────────────┼─────────────┼──────────────┤
│ worker-1     │ 25.4%      │ 12          │ 0            │
│ worker-2     │ 18.7%      │ 8           │ 0            │
└──────────────┴────────────┴─────────────┴──────────────┘

distcompute> run my_task.py
Running my_task.py across 2 worker(s)...
✓ Results: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81, 100, ...]

distcompute> exit
Shutting down coordinator...
```

The interactive mode features:
- 🎨 **Beautiful UI** with bordered panels and tables (Claude/Gemini style)
- 📊 **Worker Statistics** showing CPU usage, tasks completed, and active tasks
- ⚡ **Direct Task Execution** - run Python files directly from the coordinator
- 🔄 **Live Status Updates** - check cluster health anytime with `status` command

### Progress Tracking (New in v0.1.2!)

## Architecture

```
┌─────────────┐
│ Coordinator │ ← Main machine
└──────┬──────┘
       │
   ┌───┴────┬─────────┬─────────┐
   │        │         │         │
┌──▼──┐  ┌──▼──┐   ┌──▼──┐   ┌──▼──┐
│ W-1 │  │ W-2 │   │ W-3 │   │ W-4 │  ← Worker machines
└─────┘  └─────┘   └─────┘   └─────┘
```

- **Coordinator**: Manages task distribution and collects results
- **Workers**: Execute tasks and report back to coordinator
- **Load Balancing**: Tasks assigned to least-loaded workers
- **Fault Tolerance**: Failed tasks automatically redistributed

## Advanced Configuration

### Custom Port

```python
coordinator = Coordinator(port=6000)
```

### Verbose Logging

```python
coordinator = Coordinator(port=5555, verbose=True)
```

### Worker with Custom Name

```bash
distcompute worker 192.168.1.100 5555 my-worker-name
```

## Requirements

- Python 3.7 or higher
- Network connectivity between machines
- Same Python environment on all workers (recommended)
- `prompt_toolkit>=3.0.0` and `rich>=13.0.0` (auto-installed for interactive CLI)

## Examples

Check out the `examples/` directory for more:

- `basic_usage.py` - Simple distributed map example
- `ml_inference.py` - ML model inference simulation
- `data_processing.py` - Data processing pipeline
- `integration_test.py` - Full end-to-end test

## Troubleshooting

**Workers not connecting?**
- Ensure port 5555 (default) is open on the coordinator machine
- Check firewall settings
- Verify machines are on the same network
- Try specifying IP explicitly: `distcompute worker 192.168.1.100`

**Tasks failing?**
- Ensure all workers have required dependencies installed
- Check worker logs for error messages
- Verify functions are serializable (no lambdas with external state)

## Contributing

Contributions are welcome! This project aims to make distributed computing accessible to everyone.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

Built to democratize distributed computing. Powered by Python's `cloudpickle` for seamless function serialization and `psutil` for resource monitoring.
