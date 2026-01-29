"""
Test script for password authentication
"""
import time

def square(x):
    """Square a number with a small delay."""
    time.sleep(0.05)
    return x ** 2

TASK_FUNC = square
ITERABLE = range(1, 11)  # 10 tasks
