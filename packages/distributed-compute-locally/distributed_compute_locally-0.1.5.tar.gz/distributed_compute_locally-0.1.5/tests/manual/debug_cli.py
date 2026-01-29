#!/usr/bin/env python3
"""Debug script to test CLI argument parsing"""
import sys
sys.path.insert(0, '/Users/neelbullywon/Desktop/distributed_compute_locally')

# Simulate the CLI call
sys.argv = ['distcompute', 'coordinator', '5555', '--password', 'mySecret123']

print(f"sys.argv = {sys.argv}")

# Import and test the main function
from distributed_compute.cli import main

# Patch run_coordinator_cli to see what arguments it receives
original_run = None

def debug_run_coordinator_cli(port=5555, password=None):
    print(f"\n=== COORDINATOR DEBUG ===")
    print(f"Port: {port}")
    print(f"Password: {password!r}")
    print(f"Password is None: {password is None}")
    print(f"Password length: {len(password) if password else 0}")
    print(f"========================\n")
    
    # Don't actually start the coordinator
    import time
    time.sleep(1)

import distributed_compute.cli as cli_module
cli_module.run_coordinator_cli = debug_run_coordinator_cli

try:
    main()
except SystemExit:
    pass
