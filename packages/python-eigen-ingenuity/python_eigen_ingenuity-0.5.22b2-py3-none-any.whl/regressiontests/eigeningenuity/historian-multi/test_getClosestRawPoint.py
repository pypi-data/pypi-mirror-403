"""
Test getClosestRawPoint function from historianmulti module
"""

from regressiontests.eigeningenuity.common_multi import BaseHistorianMultiTest
from eigeningenuity.util import EigenException
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

    def test_get_closest_raw_output_raw(self):
        """Test getClosestRawPoint with raw output format"""
        result = self.historian_multi.getClosestRawPoint(
            self.test_tags[0], self.test_datetime, before_or_after="AFTER", output="raw"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_closest_raw_output_json(self):
        """Test getClosestRawPoint with json output format"""
        result = self.historian_multi.getClosestRawPoint(
            self.test_tags[0], self.test_datetime, before_or_after="AFTER", output="json"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_closest_raw_output_df(self):
        """Test getClosestRawPoint with dataframe output format"""
        try:
            import pandas as pd
            result = self.historian_multi.getClosestRawPoint(
                self.test_tags[0], self.test_datetime, before_or_after="AFTER", output="df"
            )
            self.assertIsInstance(result, pd.DataFrame)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_closest_raw_output_csv(self):
        """Test getClosestRawPoint with csv output format"""
        # TODO: CSV not implemented yet
        self.skipTest("CSV output not implemented yet")
        # CSV output might return True/False instead of None
        result = self.historian_multi.getClosestRawPoint(
            self.test_tags[0], self.test_datetime, before_or_after="AFTER", output="csv"
        )
        # Accept None, True, False, or other return values indicating success
        self.assertIsInstance(result, (type(None), bool, str))
        
    def test_get_closest_raw_output_string(self):
        """Test getClosestRawPoint with string output format"""
        result = self.historian_multi.getClosestRawPoint(
            self.test_tags[0], self.test_datetime, before_or_after="AFTER", output="string"
        )
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        
    def test_get_closest_raw_invalid_output_type(self):
        """Test getClosestRawPoint with invalid output format"""
        with self.assertRaises(EigenException):
            self.historian_multi.getClosestRawPoint(
                self.test_tags[0], self.test_datetime, before_or_after="AFTER", output="invalid"
            )


if __name__ == '__main__':
    unittest.main()
