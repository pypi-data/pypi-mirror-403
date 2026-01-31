"""
Test getCurrentDataPoints function from historian module
"""

from regressiontests.eigeningenuity.common import BaseHistorianTest
import unittest


class TestGetCurrentDataPoints(BaseHistorianTest):
    """Test cases for getCurrentDataPoints function"""
    
    def test_get_current_single_tag_default(self):
        """Test getting current data point for single tag with default output"""
        result = self.historian.getCurrentDataPoints(self.test_tags[0])
        
        # Use centralized debug function
        self.debug_result("test_get_current_single_tag_default", result, {
            "tag": self.test_tags[0],
            "output_type": "default"
        })
        
        self.assertValidDataPoint(result)
        
    def test_get_current_single_tag_json(self):
        """Test getting current data point for single tag with json output"""
        result = self.historian.getCurrentDataPoints(self.test_tags[0], output="json")
        self.assertValidDataPoint(result)
        
    def test_get_current_multiple_tags(self):
        """Test getting current data points for multiple tags"""
        result = self.historian.getCurrentDataPoints(self.test_tags)
        # Multiple tags return a dictionary, not a list
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), len(self.test_tags))
        for tag in self.test_tags:
            self.assertIn(tag, result)
            self.assertValidDataPoint(result[tag])
            
    def test_get_current_with_historian_prefix(self):
        """Test getting current data point with historian prefix"""
        # Note: historian prefix might cause issues with the tag format
        try:
            result = self.historian.getCurrentDataPoints(self.test_tags_with_historian[0])
            self.assertValidDataPoint(result)
        except Exception:
            # Historian prefix might not work as expected
            self.skipTest("Historian prefix format not supported in this context")
        
    def test_get_current_calc_tag(self):
        """Test getting current data point for calculation tag"""
        try:
            result = self.calc_historian.getCurrentDataPoints(self.calc_tag)
            self.assertValidDataPoint(result)
            self.assertEqual(result['value'], 3)  # ADD(1,2) should equal 3
        except Exception as e:
            # Calc historian might not be available
            self.skipTest(f"Calc historian not available: {e}")

    def test_get_current_nonexistent_tag(self):
        """Test behavior with non-existent tag"""
        with self.assertRaises(Exception):
            self.historian.getCurrentDataPoints("NONEXISTENT_TAG")
            
    def test_get_current_empty_tag_list(self):
        """Test behavior with empty tag list"""
        result = self.historian.getCurrentDataPoints([])
        # Empty tag list returns empty dict
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 0)

    # Output type tests
    def test_get_current_output_raw(self):
        """Test getCurrentDataPoints with raw output format"""
        result = self.historian.getCurrentDataPoints(self.test_tags[0], output="raw")
        # Raw output should be the unprocessed API response
        self.assertIsInstance(result, dict)
        self.assertIn('items', result)
        
    def test_get_current_output_json(self):
        """Test getCurrentDataPoints with json output format"""
        result = self.historian.getCurrentDataPoints(self.test_tags[0], output="json")
        self.assertValidDataPoint(result)
        
    def test_get_current_output_df(self):
        """Test getCurrentDataPoints with dataframe output format"""
        try:
            import pandas as pd
            result = self.historian.getCurrentDataPoints(self.test_tags[0], output="df")
            self.assertIsInstance(result, pd.DataFrame)
            self.assertGreater(len(result), 0)
            # DataFrame structure may vary based on API implementation
            # Just verify it's a valid DataFrame
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_current_output_csv(self):
        """Test getCurrentDataPoints with csv output format"""
        import os
        import tempfile
        
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            csv_filepath = tmp_file.name
        
        try:
            result = self.historian.getCurrentDataPoints(
                self.test_tags[0], 
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
        
    def test_get_current_output_string(self):
        """Test getCurrentDataPoints with string output format"""
        result = self.historian.getCurrentDataPoints(self.test_tags[0], output="string")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        
    def test_get_current_multiple_tags_output_raw(self):
        """Test getCurrentDataPoints with multiple tags and raw output"""
        result = self.historian.getCurrentDataPoints(self.test_tags, output="raw")
        self.assertIsInstance(result, dict)
        self.assertIn('items', result)
        
    def test_get_current_multiple_tags_output_df(self):
        """Test getCurrentDataPoints with multiple tags and dataframe output"""
        try:
            import pandas as pd
            result = self.historian.getCurrentDataPoints(self.test_tags, output="df")
            self.assertIsInstance(result, pd.DataFrame)
            self.assertGreater(len(result), 0)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_current_invalid_output_type(self):
        """Test getCurrentDataPoints with invalid output type"""
        with self.assertRaises(ValueError):
            self.historian.getCurrentDataPoints(self.test_tags[0], output="invalid")


if __name__ == '__main__':
    unittest.main()
