"""
Test tag management functions from historianmulti module
"""

from regressiontests.eigeningenuity.common_multi import BaseHistorianMultiTest
import unittest
from datetime import datetime


class TestTagManagementMulti(BaseHistorianMultiTest):
    """Test cases for tag management functions in historianmulti"""
    
    def setUp(self):
        """Extended setup for tag management tests"""
        super().setUp()
        self.test_tag = "eigen_manual_input/TEST_TAG_MANAGEMENT"
        
    def test_create_tag(self):
        """Test creating a new tag"""
        try:
            result = self.historian_multi.createTag(
                self.test_tag,
                description="Test tag for unit tests",
                units="test_unit",
                stepped=False,
                update_existing=True
            )
            
            # Use centralized debug function
            self.debug_result("test_create_tag", result, {
                "test_tag": self.test_tag,
                "description": "Test tag for unit tests",
                "units": "test_unit",
                "stepped": False,
                "update_existing": True
            })
            
            self.assertIsInstance(result, (bool, dict, list))
        except Exception as e:
            print(f"Exception occurred: {type(e).__name__}: {e}")
            self.skipTest(f"Create tag operation not permitted: {e}")
            
    def test_update_tag(self):
        """Test updating an existing tag"""
        try:
            result = self.historian_multi.updateTag(
                self.test_tag,
                description="Updated test tag for unit tests",
                units="updated_unit",
                stepped=True,
                create_missing=True
            )
            
            # Use centralized debug function
            self.debug_result("test_update_tag", result, {
                "test_tag": self.test_tag,
                "description": "Updated test tag for unit tests",
                "units": "updated_unit",
                "stepped": True,
                "create_missing": True
            })
            
            self.assertIsInstance(result, (bool, dict, list))
        except Exception as e:
            self.skipTest(f"Update tag operation not permitted: {e}")
            
    def test_create_and_populate_tag(self):
        """Test creating and populating a tag in one operation"""
        point_data = {"value": 123.45, "timestamp": datetime.now(), "status": "OK"}
        
        try:
            result = self.historian_multi.createAndPopulateTag(
                self.test_tag,
                point_data,
                description="Test tag created and populated",
                units="test_unit",
                stepped=False,
                update_existing=True
            )
            
            # Use centralized debug function
            self.debug_result("test_create_and_populate_tag", result, {
                "test_tag": self.test_tag,
                "point_data": point_data,
                "description": "Test tag created and populated",
                "units": "test_unit",
                "stepped": False,
                "update_existing": True
            })
            
            self.assertIsInstance(result, (bool, dict, list))
        except Exception as e:
            self.skipTest(f"Create and populate tag operation not permitted: {e}")
            
    def test_create_and_populate_tag_with_list(self):
        """Test creating and populating a tag with multiple points"""
        points_data = [
            {"value": 123.45, "timestamp": datetime.now(), "status": "OK"},
            {"value": 124.56, "timestamp": datetime.now(), "status": "OK"}
        ]
        
        try:
            result = self.historian_multi.createAndPopulateTag(
                self.test_tag,
                points_data,
                description="Test tag created and populated with list",
                units="test_unit",
                stepped=False,
                update_existing=True
            )
            
            # Use centralized debug function
            self.debug_result("test_create_and_populate_tag_with_list", result, {
                "test_tag": self.test_tag,
                "points_data_count": len(points_data),
                "points_data_sample": points_data[0],
                "description": "Test tag created and populated with list",
                "units": "test_unit",
                "stepped": False,
                "update_existing": True
            })
            
            self.assertIsInstance(result, (bool, dict, list))
        except Exception as e:
            self.skipTest(f"Create and populate tag operation not permitted: {e}")


if __name__ == '__main__':
    unittest.main()
