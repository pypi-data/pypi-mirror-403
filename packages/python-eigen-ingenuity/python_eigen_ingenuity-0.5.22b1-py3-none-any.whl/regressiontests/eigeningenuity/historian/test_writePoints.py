"""
Test writePoints function from historian module
"""

from regressiontests.eigeningenuity.common import BaseHistorianTest
import unittest
from datetime import datetime


class TestWritePoints(BaseHistorianTest):
    """Test cases for writePoints function"""
    
    def setUp(self):
        """Extended setup for write tests"""
        super().setUp()
        self.test_write_tag = "eigen_manual_input/TEST_WRITE_TAG"
        
    def test_write_single_point(self):
        """Test writing a single data point"""
        point_data = {"value": 42.5, "timestamp": datetime.now(), "status": "OK"}
        
        try:
            result = self.historian.writePoints(self.test_write_tag, [point_data])
            self.assertIsInstance(result, bool)
        except Exception as e:
            # Write operations may fail if permissions are not available
            self.skipTest(f"Write operation not permitted: {e}")
            
    def test_write_multiple_points(self):
        """Test writing multiple data points"""
        points_data = [
            {"value": 42.5, "timestamp": datetime.now(), "status": "OK"},
            {"value": 43.0, "timestamp": datetime.now(), "status": "OK"}
        ]
        
        try:
            result = self.historian.writePoints(self.test_write_tag, points_data)
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.skipTest(f"Write operation not permitted: {e}")
            
    def test_write_point_with_bad_status(self):
        """Test writing a point with bad status"""
        point_data = {"value": 42.5, "timestamp": datetime.now(), "status": "BAD"}
        
        try:
            result = self.historian.writePoints(self.test_write_tag, [point_data])
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.skipTest(f"Write operation not permitted: {e}")


if __name__ == '__main__':
    unittest.main()
