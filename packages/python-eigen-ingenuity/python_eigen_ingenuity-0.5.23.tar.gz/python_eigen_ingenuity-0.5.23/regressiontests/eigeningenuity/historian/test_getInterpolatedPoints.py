"""
Test getInterpolatedPoints function from historian module
"""

from regressiontests.eigeningenuity.common import BaseHistorianTest
import unittest


class TestGetInterpolatedPoints(BaseHistorianTest):
    """Test cases for getInterpolatedPoints function"""
    
    def test_get_interpolated_single_tag_single_timestamp(self):
        """Test getting interpolated point for single tag at single timestamp"""
        result = self.historian.getInterpolatedPoints(
            self.test_tags[0], 
            self.test_datetime
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertValidDataPoint(result[0])

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
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result.keys()), len(self.test_tags))
        for dp in result.values():
            self.assertEqual(len(dp), 1)
            self.assertValidDataPoint(dp[0])

    def test_get_interpolated_multiple_tags_multiple_timestamps(self):
        """Test getting interpolated points for multiple tags at multiple timestamps"""
        timestamps = [self.test_datetime, 1718180259]
        result = self.historian.getInterpolatedPoints(
            self.test_tags, 
            timestamps
        )
        self.assertIsInstance(result, dict)
        # Should return points for each tag at each timestamp
        self.assertEqual(len(result.keys()), len(self.test_tags))
        for tag, data_points in result.items():
            self.assertIn(tag, self.test_tags)
            self.assertEqual(len(data_points), len(timestamps))
            for dp in data_points:
                self.assertValidDataPoint(dp)

    def test_get_interpolated_with_json_output(self):
        """Test getting interpolated points with json output format"""
        result = self.historian.getInterpolatedPoints(
            self.test_tags[0], 
            self.test_datetime,
            output="json"
        )
        self.assertValidDataPoint(result[0])
        
    def test_get_interpolated_with_epoch_timestamp(self):
        """Test getting interpolated points with epoch timestamp"""
        epoch_time = 1714525200  # May 1, 2024 2:00:00 AM
        result = self.historian.getInterpolatedPoints(
            self.test_tags[0], 
            epoch_time
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertValidDataPoint(result[0])

    # Output type tests
    def test_get_interpolated_output_raw(self):
        """Test getInterpolatedPoints with raw output format"""
        result = self.historian.getInterpolatedPoints(
            self.test_tags[0],
            self.test_datetime,
            output="raw"
        )
        # Raw output should be the unprocessed API response
        self.assertIsInstance(result, dict)
        self.assertIn('items', result)
        
    def test_get_interpolated_output_json(self):
        """Test getInterpolatedPoints with json output format"""
        result = self.historian.getInterpolatedPoints(
            self.test_tags[0],
            self.test_datetime,
            output="json"
        )
        self.assertIsInstance(result, list)
        
    def test_get_interpolated_output_df(self):
        """Test getInterpolatedPoints with dataframe output format"""
        try:
            import pandas as pd
            result = self.historian.getInterpolatedPoints(
                self.test_tags[0],
                self.test_datetime,
                output="df"
            )
            self.assertIsInstance(result, pd.DataFrame)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_interpolated_output_csv(self):
        """Test getInterpolatedPoints with csv output format"""
        import os
        import tempfile
        
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            csv_filepath = tmp_file.name
        
        try:
            result = self.historian.getInterpolatedPoints(
                self.test_tags[0],
                self.test_datetime,
                output="csv",
                filepath=csv_filepath
            )
            
            # Assert the function returns True (indicating success)
            self.assertTrue(result)
            
            # Assert the file was created
            self.assertTrue(os.path.exists(csv_filepath), "CSV file was not created")
            
            # Assert the file is not empty
            file_size = os.path.getsize(csv_filepath)
            self.assertGreater(file_size, 0, "CSV file is empty")
            
            # Optional: Check file contains expected content
            with open(csv_filepath, 'r') as f:
                content = f.read()
                self.assertGreater(len(content.strip()), 0, "CSV file has no content")
                # Verify it looks like CSV (has commas or proper headers)
                self.assertTrue(',' in content or '\t' in content, "File doesn't appear to be CSV format")
                
        finally:
            # Clean up the temporary file
            if os.path.exists(csv_filepath):
                os.unlink(csv_filepath)
        
    def test_get_interpolated_output_string(self):
        """Test getInterpolatedPoints with string output format"""
        result = self.historian.getInterpolatedPoints(
            self.test_tags[0],
            self.test_datetime,
            output="string"
        )
        self.assertIsInstance(result, str)
        
    def test_get_interpolated_invalid_output_type(self):
        """Test getInterpolatedPoints with invalid output type"""
        with self.assertRaises(ValueError):
            self.historian.getInterpolatedPoints(
                self.test_tags[0],
                self.test_datetime,
                output="invalid"
            )


if __name__ == '__main__':
    unittest.main()
