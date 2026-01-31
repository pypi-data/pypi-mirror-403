#!/usr/bin/env python3
"""
Main test runner for Eigen Ingenuity Python Library Test Suite

This script can run all tests or specific test modules.
It ensures the local development version of the library is tested, not the installed version.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py historian          # Run all historian tests
    python run_tests.py historianmulti     # Run all historianmulti tests
    python run_tests.py historian.getCurrentDataPoints  # Run specific test
"""

import sys
import os
import unittest
import argparse
import json
from datetime import datetime
import xml.etree.ElementTree as ET

# Global flag to control local vs installed import
USE_LOCAL_VERSION = True

def setup_python_path(use_local=True):
    """Setup Python path for local or installed version"""
    global USE_LOCAL_VERSION
    USE_LOCAL_VERSION = use_local
    
    if use_local:
        # Add the parent directory to the Python path to ensure we test local version
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
    else:
        # Remove project root from path if it exists to use installed version
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if project_root in sys.path:
            sys.path.remove(project_root)

# Import all test modules
test_modules = {
    'historian': [
        'tests.historian.test_getCurrentDataPoints',
        'tests.historian.test_getInterpolatedPoints',
        'tests.historian.test_getRawDataPoints',
        'tests.historian.test_getInterpolatedRange',
        'tests.historian.test_listDataTags',
        'tests.historian.test_getMetaData',
        'tests.historian.test_writePoints',
    ],
    'historianmulti': [
        'tests.historianmulti.test_getCurrentDataPoints',
        'tests.historianmulti.test_getInterpolatedPoints',
        'tests.historianmulti.test_getInterpolatedRange',
        'tests.historianmulti.test_getRawDatapoints',
        'tests.historianmulti.test_getClosestRawPoint',
        'tests.historianmulti.test_listDataTags',
        'tests.historianmulti.test_getMetaData',
        'tests.historianmulti.test_writePoints',
        'tests.historianmulti.test_tagManagement',
    ]
}

class CompactTestResult(unittest.TestResult):
    """Custom test result class for compact JSON output"""
    
    def __init__(self):
        super().__init__()
        self.test_results = []
        self.module_results = {}
        self.current_module = None
        
    def startTest(self, test):
        super().startTest(test)
        module_name = test.__class__.__module__
        if module_name != self.current_module:
            self.current_module = module_name
            if module_name not in self.module_results:
                self.module_results[module_name] = {"passed": 0, "failed": 0, "error": 0, "skipped": 0}
                
    def addSuccess(self, test):
        super().addSuccess(test)
        module_name = test.__class__.__module__
        self.module_results[module_name]["passed"] += 1
        self.test_results.append({
            "test": f"{test.__class__.__name__}.{test._testMethodName}",
            "module": module_name,
            "status": "PASSED",
            "reason": None
        })
        
    def addError(self, test, err):
        super().addError(test, err)
        module_name = test.__class__.__module__
        self.module_results[module_name]["error"] += 1
        self.test_results.append({
            "test": f"{test.__class__.__name__}.{test._testMethodName}",
            "module": module_name,
            "status": "ERROR",
            "reason": str(err[1])
        })
        
    def addFailure(self, test, err):
        super().addFailure(test, err)
        module_name = test.__class__.__module__
        self.module_results[module_name]["failed"] += 1
        self.test_results.append({
            "test": f"{test.__class__.__name__}.{test._testMethodName}",
            "module": module_name,
            "status": "FAILED",
            "reason": str(err[1])
        })
        
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        module_name = test.__class__.__module__
        self.module_results[module_name]["skipped"] += 1
        self.test_results.append({
            "test": f"{test.__class__.__name__}.{test._testMethodName}",
            "module": module_name,
            "status": "SKIPPED",
            "reason": reason
        })

def run_tests(modules_to_run=None, verbosity=1, json_output=False, xml_output=False):
    """
    Run the specified test modules
    
    Args:
        modules_to_run: List of module names to run, None for all
        verbosity: Test verbosity level (0-2)
        json_output: Output results in JSON format
    """
    
    # Determine which modules to run
    if modules_to_run is None:
        # Run all tests
        all_modules = []
        for category in test_modules.values():
            all_modules.extend(category)
        modules_to_run = all_modules
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    failed_imports = []
    loaded_modules = []
    
    for module_name in modules_to_run:
        try:
            module = __import__(module_name, fromlist=[''])
            suite.addTests(loader.loadTestsFromModule(module))
            loaded_modules.append(module_name)
            if not json_output and verbosity > 0:
                print(f"✓ {module_name.split('.')[-1]}")
        except ImportError as e:
            failed_imports.append((module_name, str(e)))
            if not json_output:
                print(f"✗ Failed to import {module_name}: {e}")
        except Exception as e:
            failed_imports.append((module_name, str(e)))
            if not json_output:
                print(f"✗ Error loading {module_name}: {e}")
    
    if failed_imports and not json_output:
        print(f"\n{len(failed_imports)} modules failed to load")
    
    # Run tests
    if suite.countTestCases() == 0:
        if not json_output:
            print("No tests found to run!")
        return False
    
    if not json_output and verbosity > 0:
        print(f"\nRunning {suite.countTestCases()} tests...")
        print("-" * 50)
    
    # Create result collector
    custom_result = CompactTestResult()
    
    # Run tests with progress tracking
    modules_tested = set()
    
    if not json_output and verbosity > 0:
        print("Progress:")
    
    for test_group in suite:
        if hasattr(test_group, '_tests'):
            for test in test_group:
                module_name = test.__class__.__module__
                
                # Show module progress
                if module_name not in modules_tested and not json_output and verbosity > 0:
                    print(f"  Testing {module_name.split('.')[-1]}...", end="", flush=True)
                    modules_tested.add(module_name)
                
                # Run the test
                test(custom_result)
                
                # Show module completion
                if module_name in custom_result.module_results:
                    stats = custom_result.module_results[module_name]
                    tests_for_module = [t for t in test_group._tests if t.__class__.__module__ == module_name]
                    completed_tests = stats["passed"] + stats["failed"] + stats["error"] + stats["skipped"]
                    
                    if completed_tests == len(tests_for_module) and not json_output and verbosity > 0:
                        print(f" {stats['passed']}P {stats['failed']}F {stats['error']}E {stats['skipped']}S")
        else:
            test_group(custom_result)
    
    result = custom_result
    
    # Generate output
    if json_output:
        output_json_results(result, loaded_modules, failed_imports)
    elif xml_output:
        output_xml_results(result)
        if verbosity > 0:
            print("XML results written to test-results/results.xml")
    else:
        output_summary(result, loaded_modules, failed_imports, verbosity)
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    return success

def output_json_results(result, loaded_modules, failed_imports):
    """Output test results in JSON format"""
    output = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": result.testsRun,
            "passed": len([r for r in result.test_results if r["status"] == "PASSED"]),
            "failed": len([r for r in result.test_results if r["status"] == "FAILED"]),
            "errors": len([r for r in result.test_results if r["status"] == "ERROR"]),
            "skipped": len([r for r in result.test_results if r["status"] == "SKIPPED"]),
            "success": len(result.failures) == 0 and len(result.errors) == 0
        },
        "modules": {
            "loaded": loaded_modules,
            "failed_imports": [{"module": mod, "error": err} for mod, err in failed_imports]
        },
        "module_results": result.module_results,
        "test_details": result.test_results
    }
    print(json.dumps(output, indent=2))

def output_xml_results(result, output_dir="test-results"):
    """Output test results in JUnit XML format for Jenkins"""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create root testsuites element
    testsuites = ET.Element("testsuites")
    testsuites.set("name", "Eigen Ingenuity Tests")
    testsuites.set("tests", str(result.testsRun))
    testsuites.set("failures", str(len([r for r in result.test_results if r["status"] == "FAILED"])))
    testsuites.set("errors", str(len([r for r in result.test_results if r["status"] == "ERROR"])))
    testsuites.set("time", "0.0")
    testsuites.set("timestamp", datetime.now().isoformat())
    
    # Group tests by module
    modules = {}
    for test_result in result.test_results:
        module = test_result["module"]
        if module not in modules:
            modules[module] = []
        modules[module].append(test_result)
    
    # Create testsuite element for each module
    for module_name, tests in modules.items():
        testsuite = ET.SubElement(testsuites, "testsuite")
        testsuite.set("name", module_name)
        testsuite.set("tests", str(len(tests)))
        testsuite.set("failures", str(len([t for t in tests if t["status"] == "FAILED"])))
        testsuite.set("errors", str(len([t for t in tests if t["status"] == "ERROR"])))
        testsuite.set("skipped", str(len([t for t in tests if t["status"] == "SKIPPED"])))
        testsuite.set("time", "0.0")  # unittest doesn't provide timing by default
        testsuite.set("timestamp", datetime.now().isoformat())
        
        # Add testcase elements
        for test in tests:
            testcase = ET.SubElement(testsuite, "testcase")
            testcase.set("name", test["test"])
            testcase.set("classname", f"{module_name}.{test['test'].split('.')[-1]}")
            testcase.set("time", "0.0")
            
            if test["status"] == "FAILED":
                failure = ET.SubElement(testcase, "failure")
                failure.set("message", "Test failed")
                failure.text = test["reason"] or "Test failed"
            elif test["status"] == "ERROR":
                error = ET.SubElement(testcase, "error")
                error.set("message", "Test error")
                error.text = test["reason"] or "Test error"
            elif test["status"] == "SKIPPED":
                skipped = ET.SubElement(testcase, "skipped")
                skipped.set("message", test["reason"] or "Test skipped")
    
    # Write consolidated XML file
    filepath = os.path.join(output_dir, "results.xml")
    tree = ET.ElementTree(testsuites)
    tree.write(filepath, encoding="utf-8", xml_declaration=True)

def output_summary(result, loaded_modules, failed_imports, verbosity):
    """Output test results in human-readable format"""
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    # Overall stats
    print(f"Tests run: {result.testsRun}")
    print(f"✓ Passed: {len([r for r in result.test_results if r['status'] == 'PASSED'])}")
    print(f"✗ Failed: {len([r for r in result.test_results if r['status'] == 'FAILED'])}")
    print(f"⚠ Errors: {len([r for r in result.test_results if r['status'] == 'ERROR'])}")
    print(f"⏭ Skipped: {len([r for r in result.test_results if r['status'] == 'SKIPPED'])}")
    
    # Module breakdown
    if result.module_results:
        print("\nPER MODULE:")
        for module, stats in result.module_results.items():
            module_name = module.split('.')[-1]
            total = stats["passed"] + stats["failed"] + stats["error"] + stats["skipped"]
            print(f"  {module_name}: {stats['passed']}P {stats['failed']}F {stats['error']}E {stats['skipped']}S ({total} total)")
    
    # Show failures/errors if verbose
    if verbosity > 1:
        failed_tests = [r for r in result.test_results if r["status"] in ["FAILED", "ERROR"]]
        if failed_tests:
            print("\nFAILED/ERROR DETAILS:")
            for test_result in failed_tests:
                print(f"  {test_result['status']}: {test_result['test']}")
                if test_result['reason']:
                    # Truncate long error messages
                    reason = test_result['reason']
                    if len(reason) > 100:
                        reason = reason[:100] + "..."
                    print(f"    Reason: {reason}")
    
    # Show skipped tests if verbose
    if verbosity > 1:
        skipped_tests = [r for r in result.test_results if r["status"] == "SKIPPED"]
        if skipped_tests:
            print("\nSKIPPED DETAILS:")
            for test_result in skipped_tests:
                print(f"  {test_result['test']}: {test_result['reason']}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nRESULT: {'✓ PASSED' if success else '✗ FAILED'}")

def main():
    """Main entry point"""
    # Change to the parent directory (project root) to ensure imports work correctly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.chdir(project_root)
    
    parser = argparse.ArgumentParser(description='Run Eigen Ingenuity Python Library tests')
    parser.add_argument('target', nargs='?', default=None,
                       help='Test target: "all", "historian", "historianmulti", or specific test module')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output (show detailed errors)')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet output (minimal logging)')
    parser.add_argument('-j', '--json', action='store_true',
                       help='Output results in JSON format')
    parser.add_argument('-x', '--xml', action='store_true',
                       help='Output results in XML format (JUnit compatible)')
    parser.add_argument('--use-local', action='store_true',
                       help='Use local python-eigen-ingenuity instead of installed version')
    parser.add_argument('--list', action='store_true',
                       help='List available test modules')
    
    args = parser.parse_args()
    
    # Set up Python path based on user preference
    setup_python_path(use_local=args.use_local)
    
    # List available tests
    if args.list:
        print("Available test categories:")
        for category, modules in test_modules.items():
            print(f"\n{category}:")
            for module in modules:
                print(f"  - {module.split('.')[-1]}")
        return
    
    # Determine verbosity
    verbosity = 1  # Default
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    
    # JSON output mode
    json_output = args.json
    xml_output = args.xml
    
    # Validate output modes
    if json_output and xml_output:
        print("Error: Cannot specify both --json and --xml output modes")
        return 1
    
    # Determine which tests to run
    modules_to_run = None
    
    if args.target is None or args.target == 'all':
        # Run all tests
        modules_to_run = None
        if not json_output:
            print("Running ALL tests...")
        
    elif args.target in test_modules:
        # Run specific category
        modules_to_run = test_modules[args.target]
        if not json_output:
            print(f"Running {args.target} tests...")
        
    elif '.' in args.target:
        # Specific test module - handle different formats
        if args.target.startswith('tests.'):
            full_module_name = args.target
        else:
            # Support both formats: historian.getCurrentDataPoints and test_getCurrentDataPoints
            if args.target.count('.') == 1 and not args.target.startswith('test_'):
                category, test_name = args.target.split('.')
                if not test_name.startswith('test_'):
                    test_name = f"test_{test_name}"
                full_module_name = f"tests.{category}.{test_name}"
            else:
                full_module_name = f"tests.{args.target}"
        modules_to_run = [full_module_name]
        if not json_output:
            print(f"Running specific test: {full_module_name}")
        
    else:
        # Try to find partial matches
        matching_modules = []
        for category, modules in test_modules.items():
            for module in modules:
                if args.target in module:
                    matching_modules.append(module)
        
        if matching_modules:
            modules_to_run = matching_modules
            if not json_output:
                print(f"Running tests matching '{args.target}': {len(matching_modules)} tests")
        else:
            if not json_output:
                print(f"No tests found matching '{args.target}'")
                print("Use --list to see available tests")
            return 1
    
    # Run the tests
    success = run_tests(modules_to_run, verbosity, json_output, xml_output)
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
