"""
Test configuration for Eigen Ingenuity Python Library Test Suite

This file contains configuration settings that can be easily modified
without changing individual test files.
"""

# Server configuration
TEST_SERVER = "demo-dev.eigen.co"
TEST_HISTORIAN = "Demo-influxdb"

# Test data configuration
TEST_TAGS = ["DEMO_02TI301.PV", "DEMO_02TI201.PV"]
TEST_CALC_TAG = "calc/ADD(1,2)"

# Test write tag prefix (for write operations)
TEST_WRITE_TAG_PREFIX = "eigen_manual_input/TEST_"

# Test time configuration (May 1, 2024 2:00:00 AM)
TEST_DATETIME_EPOCH = 1714525200

# Test limits and timeouts
DEFAULT_MAX_POINTS = 10
DEFAULT_TIMEOUT = 30  # seconds

# Test behavior settings
SKIP_WRITE_TESTS_ON_ERROR = True
SUPPRESS_SSL_WARNINGS = True
DISABLE_AZURE_AUTH = True
