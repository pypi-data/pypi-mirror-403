"""
Test getInterpolatedPoints function from historian module
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tests.common import BaseHistorianTest
import unittest


class TestGetInterpolatedPoints(BaseHistorianTest):
    """Test cases for getInterpolatedPoints function"""
    
    def test_get_interpolated_single_tag_single_timestamp(self):
        """Test getting interpolated point for single tag at single timestamp"""
        result = self.historian.getInterpolatedPoints(
            self.test_tags[0], 
            self.test_datetime
        )
        self.assertValidDataPoint(result)
        
    def test_get_interpolated_single_tag_multiple_timestamps(self):
        """Test getting interpolated points for single tag at multiple timestamps"""
        timestamps = [self.test_datetime, 1718180259]
        result = self.historian.getInterpolatedPoints(
            self.test_tags[0], 
            timestamps
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(timestamps))
        for dp in result:
            self.assertValidDataPoint(dp)
            
    def test_get_interpolated_multiple_tags_single_timestamp(self):
        """Test getting interpolated points for multiple tags at single timestamp"""
        result = self.historian.getInterpolatedPoints(
            self.test_tags, 
            self.test_datetime
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(self.test_tags))
        for dp in result:
            self.assertValidDataPoint(dp)
            
    def test_get_interpolated_multiple_tags_multiple_timestamps(self):
        """Test getting interpolated points for multiple tags at multiple timestamps"""
        timestamps = [self.test_datetime, 1718180259]
        result = self.historian.getInterpolatedPoints(
            self.test_tags, 
            timestamps
        )
        self.assertIsInstance(result, list)
        # Should return points for each tag at each timestamp
        expected_length = len(self.test_tags) * len(timestamps)
        self.assertEqual(len(result), expected_length)
        for dp in result:
            self.assertValidDataPoint(dp)
            
    def test_get_interpolated_with_json_output(self):
        """Test getting interpolated points with json output format"""
        result = self.historian.getInterpolatedPoints(
            self.test_tags[0], 
            self.test_datetime,
            output="json"
        )
        self.assertValidDataPoint(result)
        
    def test_get_interpolated_with_epoch_timestamp(self):
        """Test getting interpolated points with epoch timestamp"""
        epoch_time = 1714525200  # May 1, 2024 2:00:00 AM
        result = self.historian.getInterpolatedPoints(
            self.test_tags[0], 
            epoch_time
        )
        self.assertValidDataPoint(result)


if __name__ == '__main__':
    unittest.main()
