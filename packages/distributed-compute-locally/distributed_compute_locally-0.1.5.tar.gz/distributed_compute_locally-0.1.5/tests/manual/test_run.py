#!/usr/bin/env python3
"""
Test file to run via: run test_run.py
This defines TASK_FUNC and ITERABLE for the coordinator CLI.
"""

import time

def square(x):
    """Square function with delay."""
    time.sleep(0.05)
    return x ** 2

# These variables are required by the coordinator CLI
TASK_FUNC = square
ITERABLE = range(1, 51)  # 50 tasks

print("\n✨ Task file loaded: will compute squares of 1-50 with 50ms delay each")

