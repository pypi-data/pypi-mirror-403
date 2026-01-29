#!/usr/bin/env python3
"""Simple test of argument parsing"""
import sys

# Test coordinator command
sys.argv = ['distcompute', 'coordinator', '5555', '--password', 'mySecret123']

command = sys.argv[1].lower()
port = 5555
password = None

# Parse arguments
args = sys.argv[2:]
i = 0
while i < len(args):
    if args[i] == "--password" and i + 1 < len(args):
        password = args[i + 1]
        i += 2
    elif args[i].startswith("--"):
        i += 1
    else:
        # First non-flag argument is port
        try:
            port = int(args[i])
        except ValueError:
            pass
        i += 1

print(f"Command: {command}")
print(f"Port: {port}")
print(f"Password: {password!r}")
print(f"Password is None: {password is None}")

# Test worker command
print("\n" + "="*60 + "\n")
sys.argv = ['distcompute', 'worker', 'localhost', '5555', 'worker-1', '--password', 'mySecret123']

host = "localhost"
port = 5555
name = None
password = None

# Parse arguments
args = sys.argv[2:]
positional = []
i = 0
while i < len(args):
    if args[i] == "--password" and i + 1 < len(args):
        password = args[i + 1]
        i += 2
    elif args[i].startswith("--"):
        i += 1
    else:
        positional.append(args[i])
        i += 1

# Assign positional arguments
if len(positional) > 0:
    host = positional[0]
if len(positional) > 1:
    try:
        port = int(positional[1])
    except ValueError:
        pass
if len(positional) > 2:
    name = positional[2]

print(f"Host: {host}")
print(f"Port: {port}")
print(f"Name: {name}")
print(f"Password: {password!r}")
print(f"Password is None: {password is None}")
