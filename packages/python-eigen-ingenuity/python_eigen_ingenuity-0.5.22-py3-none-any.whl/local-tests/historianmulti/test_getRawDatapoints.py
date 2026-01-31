"""
Test getRawDatapoints function from historianmulti module
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tests.historianmulti.common_multi import BaseHistorianMultiTest
import unittest
from datetime import datetime, timedelta


class TestGetRawDataPointsMulti(BaseHistorianMultiTest):
    """Test cases for getRawDatapoints function in historianmulti"""
    
    def test_get_raw_single_tag(self):
        """Test getting raw data points for single tag"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_raw_multiple_tags(self):
        """Test getting raw data points for multiple tags"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags,
            start_time,
            end_time,
            maxpoints=10
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_raw_with_json_output(self):
        """Test getting raw data points with json output"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10,
            output="json"
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_raw_with_epoch_times(self):
        """Test getting raw data points with epoch timestamps"""
        end_time = 1714525200 + 3600  # May 1, 2024 3:00:00 AM
        start_time = 1714525200       # May 1, 2024 2:00:00 AM
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_raw_with_limit(self):
        """Test getting raw data points with maxpoints limit"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        max_points = 5
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=max_points
        )
        self.assertIsInstance(result, (dict, list))


if __name__ == '__main__':
    unittest.main()
