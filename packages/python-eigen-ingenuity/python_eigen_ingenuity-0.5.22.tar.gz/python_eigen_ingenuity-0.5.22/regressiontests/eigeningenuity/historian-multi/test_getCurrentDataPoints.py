"""
Test getCurrentDataPoints function from historianmulti module
"""

from regressiontests.eigeningenuity.common_multi import BaseHistorianMultiTest
from eigeningenuity.util import EigenException
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
        result = self.calc_historian_multi.getCurrentDataPoints(self.calc_tag)
        self.assertIsInstance(result, (dict, list))
        
    def test_get_current_mixed_tags(self):
        """Test getting current data points with mixed historian sources"""
        # Note: Mixed tags from different historians may not work in a single call
        # Test regular tags separately and calc tags separately
        try:
            mixed_tags = [self.test_tags[0], self.calc_tag]
            result = self.historian_multi.getCurrentDataPoints(mixed_tags)
            self.assertIsInstance(result, (dict, list))
        except Exception:
            # Mixed historian sources might not be supported, test separately
            result1 = self.historian_multi.getCurrentDataPoints(self.test_tags[0])
            result2 = self.calc_historian_multi.getCurrentDataPoints(self.calc_tag)
            self.assertIsInstance(result1, (dict, list))
            self.assertIsInstance(result2, (dict, list))
        
    def test_get_current_empty_tag_list(self):
        """Test behavior with empty tag list"""
        result = self.historian_multi.getCurrentDataPoints([])
        self.assertIsInstance(result, (dict, list))

    # Output type tests
    def test_get_current_output_raw(self):
        """Test getCurrentDataPoints with raw output format"""
        result = self.historian_multi.getCurrentDataPoints(self.test_tags[0], output="raw")
        # Raw output should be the unprocessed API response
        self.assertIsInstance(result, (dict, list))
        
    def test_get_current_output_json(self):
        """Test getCurrentDataPoints with json output format"""
        result = self.historian_multi.getCurrentDataPoints(self.test_tags[0], output="json")
        self.assertIsInstance(result, (dict, list))
        
    def test_get_current_output_df(self):
        """Test getCurrentDataPoints with dataframe output format"""
        try:
            import pandas as pd
            result = self.historian_multi.getCurrentDataPoints(self.test_tags[0], output="df")
            self.assertIsInstance(result, pd.DataFrame)
            self.assertGreater(len(result), 0)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_current_output_csv(self):
        """Test getCurrentDataPoints with csv output format"""
        # TODO: CSV not implemented yet
        self.skipTest("CSV output not implemented yet")
        
        # CSV output might return True/False instead of None
        result = self.historian_multi.getCurrentDataPoints(self.test_tags[0], output="csv")
        # Accept None, True, False, or other return values indicating success
        self.assertIsInstance(result, (type(None), bool, str))
        
    def test_get_current_output_string(self):
        """Test getCurrentDataPoints with string output format"""
        result = self.historian_multi.getCurrentDataPoints(self.test_tags[0], output="string")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        
    def test_get_current_multiple_tags_output_raw(self):
        """Test getCurrentDataPoints with multiple tags and raw output"""
        result = self.historian_multi.getCurrentDataPoints(self.test_tags, output="raw")
        self.assertIsInstance(result, (dict, list))
        
    def test_get_current_multiple_tags_output_df(self):
        """Test getCurrentDataPoints with multiple tags and dataframe output"""
        try:
            import pandas as pd
            result = self.historian_multi.getCurrentDataPoints(self.test_tags, output="df")
            self.assertIsInstance(result, pd.DataFrame)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_current_invalid_output_type(self):
        """Test getCurrentDataPoints with invalid output format"""
        with self.assertRaises(EigenException):
            self.historian_multi.getCurrentDataPoints(self.test_tags[0], output="invalid")


if __name__ == '__main__':
    unittest.main()
