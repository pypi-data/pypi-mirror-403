"""
Test getCurrentDataPoints function from historianmulti module
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tests.historianmulti.common_multi import BaseHistorianMultiTest
import unittest


class TestGetCurrentDataPointsMulti(BaseHistorianMultiTest):
    """Test cases for getCurrentDataPoints function in historianmulti"""
    
    def test_get_current_single_tag_default(self):
        """Test getting current data point for single tag with default output"""
        result = self.historian_multi.getCurrentDataPoints(self.test_tags[0])
        self.assertIsInstance(result, (dict, list))
        
    def test_get_current_single_tag_json(self):
        """Test getting current data point for single tag with json output"""
        result = self.historian_multi.getCurrentDataPoints(self.test_tags[0], output="json")
        self.assertIsInstance(result, (dict, list))
        
    def test_get_current_multiple_tags(self):
        """Test getting current data points for multiple tags"""
        result = self.historian_multi.getCurrentDataPoints(self.test_tags)
        self.assertIsInstance(result, (dict, list))
            
    def test_get_current_with_historian_prefix(self):
        """Test getting current data point with historian prefix"""
        result = self.historian_multi.getCurrentDataPoints(self.test_tags_with_historian)
        self.assertIsInstance(result, (dict, list))
        
    def test_get_current_calc_tag(self):
        """Test getting current data point for calculation tag"""
        result = self.historian_multi.getCurrentDataPoints(self.calc_tag)
        self.assertIsInstance(result, (dict, list))
        
    def test_get_current_mixed_tags(self):
        """Test getting current data points with mixed historian sources"""
        mixed_tags = [self.test_tags[0], self.calc_tag]
        result = self.historian_multi.getCurrentDataPoints(mixed_tags)
        self.assertIsInstance(result, (dict, list))
        
    def test_get_current_empty_tag_list(self):
        """Test behavior with empty tag list"""
        result = self.historian_multi.getCurrentDataPoints([])
        self.assertIsInstance(result, (dict, list))


if __name__ == '__main__':
    unittest.main()
