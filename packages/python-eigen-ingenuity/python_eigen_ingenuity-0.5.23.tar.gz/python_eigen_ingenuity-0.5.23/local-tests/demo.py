#!/usr/bin/env python3
"""
Demo script to showcase the Eigen Ingenuity Test Suite

This script demonstrates how the test suite works and shows examples
of running different types of tests.
"""

import os
import subprocess

def run_command(cmd, description):
    """Run a command and display the results"""
    print(f"\n{'='*60}")
    print(f"DEMO: {description}")
    print(f"Command: {cmd}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=project_root)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def main():
    global project_root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    print("Eigen Ingenuity Python Library Test Suite - DEMO")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print()
    print("This demo shows how to use the comprehensive test suite")
    print("that tests the LOCAL development version of the library.")
    
    # Demo 1: List available tests
    run_command("python3 tests/run_tests.py --list", 
                "List all available test modules")
    
    # Demo 2: Run a specific test with verbose output
    run_command("python3 tests/run_tests.py historian.getCurrentDataPoints --verbose", 
                "Run specific historian test with verbose output")
    
    # Demo 3: Run all historian tests quietly
    run_command("python3 tests/run_tests.py historian --quiet", 
                "Run all historian tests with quiet output")
    
    # Demo 4: Show the bash script method
    print(f"\n{'='*60}")
    print("DEMO: Alternative - Using the bash script")
    print("Command: ./tests/run_all_tests.sh historian")
    print(f"{'='*60}")
    print("You can also run tests using the bash script:")
    print("  ./tests/run_all_tests.sh                    # All tests")
    print("  ./tests/run_all_tests.sh historian          # Historian tests")
    print("  ./tests/run_all_tests.sh historianmulti     # HistorianMulti tests")
    
    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print(f"{'='*60}")
    print()
    print("Test Suite Features:")
    print("✓ Tests LOCAL development version (not installed package)")
    print("✓ Comprehensive coverage of historian and historianmulti functions")
    print("✓ Organized by function in separate test files")
    print("✓ Easy to run individual tests or test suites")
    print("✓ Graceful handling of network issues and permissions")
    print("✓ Clear reporting and error messages")
    print()
    print("Next steps:")
    print("1. Run individual function tests during development")
    print("2. Run full test suite before commits")
    print("3. Add new tests when adding new functions")
    print("4. Use in CI/CD pipelines for automated testing")

if __name__ == '__main__':
    main()
