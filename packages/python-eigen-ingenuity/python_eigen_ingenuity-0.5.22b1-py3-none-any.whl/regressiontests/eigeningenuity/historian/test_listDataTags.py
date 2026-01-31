"""
Test listDataTags function from historian module
"""

from regressiontests.eigeningenuity.common import BaseHistorianTest
import unittest


class TestListDataTags(BaseHistorianTest):
    """Test cases for listDataTags function"""
    
    def test_list_data_tags_no_wildcard(self):
        """Test listing data tags without wildcard"""
        result = self.historian.listDataTags("*")
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        
    def test_list_data_tags_with_wildcard(self):
        """Test listing data tags with wildcard pattern"""
        result = self.historian.listDataTags("*TI*")
        self.assertIsInstance(result, list)
        # Check that all returned tags contain "TI"
        for tag in result:
            self.assertIn("TI", tag)
            
    def test_list_data_tags_specific_pattern(self):
        """Test listing data tags with specific pattern"""
        result = self.historian.listDataTags("DEMO_02TI301*")
        self.assertIsInstance(result, list)
        # Should find the test tag
        tag_found = any("DEMO_02TI301" in tag for tag in result)
        self.assertTrue(tag_found)
        
    def test_list_data_tags_no_matches(self):
        """Test listing data tags with pattern that has no matches"""
        result = self.historian.listDataTags("NONEXISTENT_PATTERN_12345")
        self.assertIsInstance(result, list)
        # May be empty or may return empty list depending on implementation
        
    def test_list_data_tags_empty_pattern(self):
        """Test listing data tags with empty pattern"""
        result = self.historian.listDataTags("")
        self.assertIsInstance(result, list)
        # Should return all available tags


if __name__ == '__main__':
    unittest.main()
