#!/usr/bin/env python3
"""Test if coordinator actually uses the password"""

import sys
sys.argv = ['test', 'coordinator', '5555', '--password', 'testSecret']

from distributed_compute.cli import main

# Intercept the Coordinator class initialization
from distributed_compute import Coordinator

original_init = Coordinator.__init__

def debug_init(self, host="0.0.0.0", port=5000, verbose=False, worker_timeout=30.0, password=None):
    print(f"\n{'='*60}")
    print(f"COORDINATOR INITIALIZED WITH:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Password: {password!r}")
    print(f"  Password is None: {password is None}")
    print(f"{'='*60}\n")
    original_init(self, host, port, verbose, worker_timeout, password)

Coordinator.__init__ = debug_init

try:
    main()
except KeyboardInterrupt:
    pass
