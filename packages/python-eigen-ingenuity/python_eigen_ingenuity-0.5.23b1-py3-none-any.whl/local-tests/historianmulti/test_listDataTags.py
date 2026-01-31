"""
Test listDataTags function from historianmulti module
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tests.historianmulti.common_multi import BaseHistorianMultiTest
import unittest


class TestListDataTagsMulti(BaseHistorianMultiTest):
    """Test cases for listDataTags function in historianmulti"""
    
    def test_list_data_tags_default(self):
        """Test listing data tags with default parameters"""
        result = self.historian_multi.listDataTags()
        self.assertIsInstance(result, (dict, list))
        
    def test_list_data_tags_with_historian(self):
        """Test listing data tags with specific historian"""
        result = self.historian_multi.listDataTags(historian=self.historian_name)
        self.assertIsInstance(result, (dict, list))
        
    def test_list_data_tags_with_match_pattern(self):
        """Test listing data tags with match pattern"""
        result = self.historian_multi.listDataTags(
            historian=self.historian_name,
            match="TI*"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_list_data_tags_with_limit(self):
        """Test listing data tags with limit"""
        result = self.historian_multi.listDataTags(
            historian=self.historian_name,
            limit=5
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_list_data_tags_specific_pattern(self):
        """Test listing data tags with specific pattern"""
        result = self.historian_multi.listDataTags(
            historian=self.historian_name,
            match="*301*"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_list_data_tags_no_matches(self):
        """Test listing data tags with pattern that has no matches"""
        result = self.historian_multi.listDataTags(
            historian=self.historian_name,
            match="NONEXISTENT_PATTERN_12345"
        )
        self.assertIsInstance(result, (dict, list))


if __name__ == '__main__':
    unittest.main()
