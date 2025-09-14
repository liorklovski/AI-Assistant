#!/usr/bin/env python3
"""
Test runner for AI Chat Assistant
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests(test_type: str = "all", verbose: bool = True):
    """
    Run tests with different configurations
    
    Args:
        test_type: "unit", "integration", "all", or "fast"
        verbose: Whether to run in verbose mode
    """
    
    # Ensure we're in the right directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    # Add specific test paths based on type
    if test_type == "unit":
        cmd.append("tests/unit/")
        print("🧪 Running Unit Tests...")
    elif test_type == "integration":
        cmd.append("tests/integration/")
        print("🔗 Running Integration Tests...")
    elif test_type == "fast":
        cmd.extend(["tests/", "-m", "not slow"])
        print("⚡ Running Fast Tests...")
    else:  # all
        cmd.append("tests/")
        print("🚀 Running All Tests...")
    
    # Add coverage if available
    try:
        import coverage
        cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=html"])
        print("📊 Coverage reporting enabled")
    except ImportError:
        print("📝 Install 'coverage' for test coverage reports")
    
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)
    
    # Run tests
    result = subprocess.run(cmd, capture_output=False)
    
    print("=" * 60)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        
    return result.returncode


def main():
    """Main test runner function"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"
    
    valid_types = ["unit", "integration", "all", "fast"]
    if test_type not in valid_types:
        print(f"❌ Invalid test type: {test_type}")
        print(f"Valid options: {', '.join(valid_types)}")
        sys.exit(1)
    
    exit_code = run_tests(test_type)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
