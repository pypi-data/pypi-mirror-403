"""
Test getClosestRawPoint function from historianmulti module
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tests.historianmulti.common_multi import BaseHistorianMultiTest
import unittest


class TestGetClosestRawPointMulti(BaseHistorianMultiTest):
    """Test cases for getClosestRawPoint function in historianmulti"""
    
    def test_get_closest_raw_single_tag_single_timestamp(self):
        """Test getting closest raw point for single tag at single timestamp"""
        result = self.historian_multi.getClosestRawPoint(
            self.test_tags[0], 
            self.test_datetime,
            before_or_after="AFTER"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_closest_raw_single_tag_multiple_timestamps(self):
        """Test getting closest raw points for single tag at multiple timestamps"""
        timestamps = [self.test_datetime, 1718180259]
        result = self.historian_multi.getClosestRawPoint(
            self.test_tags[0], 
            timestamps,
            before_or_after="AFTER"
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_closest_raw_multiple_tags_single_timestamp(self):
        """Test getting closest raw points for multiple tags at single timestamp"""
        result = self.historian_multi.getClosestRawPoint(
            self.test_tags, 
            self.test_datetime,
            before_or_after="AFTER"
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_closest_raw_multiple_tags_multiple_timestamps(self):
        """Test getting closest raw points for multiple tags at multiple timestamps"""
        timestamps = [self.test_datetime, 1718180259]
        result = self.historian_multi.getClosestRawPoint(
            self.test_tags, 
            timestamps,
            before_or_after="AFTER"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_closest_raw_before(self):
        """Test getting closest raw point before timestamp"""
        result = self.historian_multi.getClosestRawPoint(
            self.test_tags[0], 
            self.test_datetime,
            before_or_after="BEFORE"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_closest_raw_with_epoch_timestamp(self):
        """Test getting closest raw point with epoch timestamp"""
        epoch_time = 1714525200  # May 1, 2024 2:00:00 AM
        result = self.historian_multi.getClosestRawPoint(
            self.test_tags[0], 
            epoch_time,
            before_or_after="AFTER"
        )
        self.assertIsInstance(result, (dict, list))


if __name__ == '__main__':
    unittest.main()
