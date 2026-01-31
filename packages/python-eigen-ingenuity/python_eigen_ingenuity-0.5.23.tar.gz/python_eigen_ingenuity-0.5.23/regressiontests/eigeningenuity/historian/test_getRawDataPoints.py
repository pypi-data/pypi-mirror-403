"""
Test getRawDataPoints function from historian module
"""

from regressiontests.eigeningenuity.common import BaseHistorianTest
import unittest
from datetime import datetime, timedelta


class TestGetRawDataPoints(BaseHistorianTest):
    """Test cases for getRawDataPoints function"""
    
    def test_get_raw_single_tag(self):
        """Test getting raw data points for single tag"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getRawDataPoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10
        )
        self.assertIsInstance(result, list)
        for dp in result:
            self.assertValidDataPoint(dp)
            
    def test_get_raw_multiple_tags(self):
        """Test getting raw data points for multiple tags"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getRawDataPoints(
            self.test_tags,
            start_time,
            end_time,
            maxpoints=10
        )
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result.keys()), len(self.test_tags))
        for dp in result.values():
            self.assertIsInstance(dp, list)
            self.assertEqual(len(dp), 10)
            self.assertValidDataPointList(dp)
            
    def test_get_raw_with_json_output(self):
        """Test getting raw data points with json output"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getRawDataPoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10,
            output="json"
        )
        self.assertIsInstance(result, list)
        for dp in result:
            self.assertValidDataPoint(dp)
            
    def test_get_raw_with_epoch_times(self):
        """Test getting raw data points with epoch timestamps"""
        end_time = 1714525200 + 3600  # May 1, 2024 3:00:00 AM
        start_time = 1714525200       # May 1, 2024 2:00:00 AM
        
        result = self.historian.getRawDataPoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10
        )
        self.assertIsInstance(result, list)
        
    def test_get_raw_with_limit(self):
        """Test getting raw data points with maxpoints limit"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        max_points = 5
        
        result = self.historian.getRawDataPoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=max_points
        )
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), max_points)

    # Output type tests
    def test_get_raw_output_raw(self):
        """Test getRawDataPoints with raw output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getRawDataPoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10,
            output="raw"
        )
        # Raw output should be the unprocessed API response
        self.assertIsInstance(result, dict)
        self.assertIn('items', result)
        
    def test_get_raw_output_json(self):
        """Test getRawDataPoints with json output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getRawDataPoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10,
            output="json"
        )
        self.assertIsInstance(result, list)
        
    def test_get_raw_output_df(self):
        """Test getRawDataPoints with dataframe output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        try:
            import pandas as pd
            result = self.historian.getRawDataPoints(
                self.test_tags[0],
                start_time,
                end_time,
                maxpoints=10,
                output="df"
            )
            self.assertIsInstance(result, pd.DataFrame)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_raw_output_csv(self):
        """Test getRawDataPoints with csv output format"""
        import os
        import tempfile
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            csv_filepath = tmp_file.name
        
        try:
            result = self.historian.getRawDataPoints(
                self.test_tags[0],
                start_time,
                end_time,
                maxpoints=10,
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
        
    def test_get_raw_output_string(self):
        """Test getRawDataPoints with string output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getRawDataPoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10,
            output="string"
        )
        self.assertIsInstance(result, str)
        
    def test_get_raw_invalid_output_type(self):
        """Test getRawDataPoints with invalid output type"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        with self.assertRaises(ValueError):
            self.historian.getRawDataPoints(
                self.test_tags[0],
                start_time,
                end_time,
                maxpoints=10,
                output="invalid"
            )


if __name__ == '__main__':
    unittest.main()
