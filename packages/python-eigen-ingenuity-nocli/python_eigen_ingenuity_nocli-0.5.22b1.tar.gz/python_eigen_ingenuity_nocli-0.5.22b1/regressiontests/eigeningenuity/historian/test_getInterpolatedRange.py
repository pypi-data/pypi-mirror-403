"""
Test getInterpolatedRange function from historian module
"""

from regressiontests.eigeningenuity.common import BaseHistorianTest
import unittest
from datetime import datetime, timedelta


class TestGetInterpolatedRange(BaseHistorianTest):
    """Test cases for getInterpolatedRange function"""
    
    def test_get_interpolated_range_single_tag(self):
        """Test getting interpolated range for single tag"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getInterpolatedRange(
            self.test_tags[0],
            start_time,
            end_time,
            count=10
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 10)
        for dp in result:
            self.assertValidDataPoint(dp)
            
    def test_get_interpolated_range_multiple_tags(self):
        """Test getting interpolated range for multiple tags"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        num_points = 5
        
        result = self.historian.getInterpolatedRange(
            self.test_tags,
            start_time,
            end_time,
            count=num_points
        )
        self.assertIsInstance(result, dict)
        # Should return num_points for each tag
        self.assertEqual(len(result.keys()), len(self.test_tags))
        for dp in result.values():
            self.assertEqual(len(dp), num_points)
            self.assertValidDataPointList(dp)
            
    def test_get_interpolated_range_with_json_output(self):
        """Test getting interpolated range with json output"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getInterpolatedRange(
            self.test_tags[0],
            start_time,
            end_time,
            count=5,
            output="json"
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 5)
        for dp in result:
            self.assertValidDataPoint(dp)
            
    def test_get_interpolated_range_with_epoch_times(self):
        """Test getting interpolated range with epoch timestamps"""
        end_time = 1714525200 + 3600  # May 1, 2024 3:00:00 AM
        start_time = 1714525200       # May 1, 2024 2:00:00 AM
        
        result = self.historian.getInterpolatedRange(
            self.test_tags[0],
            start_time,
            end_time,
            count=3
        )
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 3)

    # Output type tests
    def test_get_interpolated_range_output_raw(self):
        """Test getInterpolatedRange with raw output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getInterpolatedRange(
            self.test_tags[0],
            start_time,
            end_time,
            count=5,
            output="raw"
        )
        # Raw output should be the unprocessed API response
        self.assertIsInstance(result, dict)
        self.assertIn('items', result)
        
    def test_get_interpolated_range_output_json(self):
        """Test getInterpolatedRange with json output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getInterpolatedRange(
            self.test_tags[0],
            start_time,
            end_time,
            count=5,
            output="json"
        )
        self.assertIsInstance(result, list)
        
    def test_get_interpolated_range_output_df(self):
        """Test getInterpolatedRange with dataframe output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        try:
            import pandas as pd
            result = self.historian.getInterpolatedRange(
                self.test_tags[0],
                start_time,
                end_time,
                count=5,
                output="df"
            )
            self.assertIsInstance(result, pd.DataFrame)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_interpolated_range_output_csv(self):
        """Test getInterpolatedRange with csv output format"""
        import os
        import tempfile
        from datetime import datetime, timedelta
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            csv_filepath = tmp_file.name
        
        try:
            result = self.historian.getInterpolatedRange(
                self.test_tags[0],
                start_time,
                end_time,
                count=5,
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
        
    def test_get_interpolated_range_output_string(self):
        """Test getInterpolatedRange with string output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian.getInterpolatedRange(
            self.test_tags[0],
            start_time,
            end_time,
            count=5,
            output="string"
        )
        self.assertIsInstance(result, str)
        
    def test_get_interpolated_range_invalid_output_type(self):
        """Test getInterpolatedRange with invalid output type"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        with self.assertRaises(ValueError):
            self.historian.getInterpolatedRange(
                self.test_tags[0],
                start_time,
                end_time,
                count=5,
                output="invalid"
            )


if __name__ == '__main__':
    unittest.main()
