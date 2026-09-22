"""
Programmatic Test Runner for Milestone 1 Backend
Executes all pytest test files and prints structured results.
"""
import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

import pytest

def main():
    test_dir = os.path.join(backend_dir, "tests")
    args = [
        test_dir,
        "-v",
        "-s",
        "--tb=short"
    ]
    print(f"Running pytest with args: {args}")
    exit_code = pytest.main(args)
    print(f"\nPytest exited with code: {exit_code}")
    return int(exit_code)

if __name__ == "__main__":
    sys.exit(main())
