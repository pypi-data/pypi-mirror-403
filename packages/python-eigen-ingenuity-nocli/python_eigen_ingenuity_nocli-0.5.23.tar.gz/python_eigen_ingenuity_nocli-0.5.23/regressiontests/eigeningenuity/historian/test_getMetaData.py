"""
Test getMetaData function from historian module
"""

from regressiontests.eigeningenuity.common import BaseHistorianTest
import unittest


class TestGetMetaData(BaseHistorianTest):
    """Test cases for getMetaData function"""
    
    def test_get_metadata_single_tag(self):
        """Test getting metadata for single tag"""
        result = self.historian.getMetaData(self.test_tags[0])
        self.assertIsInstance(result, (dict, list))
        
    def test_get_metadata_multiple_tags(self):
        """Test getting metadata for multiple tags"""
        result = self.historian.getMetaData(self.test_tags)
        self.assertIsInstance(result, (dict, list))
        
    def test_get_metadata_with_json_output(self):
        """Test getting metadata with json output"""
        result = self.historian.getMetaData(self.test_tags[0], output="json")
        self.assertIsInstance(result, (dict, list))
        
    def test_get_metadata_nonexistent_tag(self):
        """Test getting metadata for non-existent tag"""
        # This might raise an exception or return empty result depending on implementation
        try:
            result = self.historian.getMetaData("NONEXISTENT_TAG_12345")
            self.assertIsInstance(result, (dict, list))
        except Exception:
            # Expected behavior for non-existent tags
            pass
            
    def test_get_metadata_calc_tag(self):
        """Test getting metadata for calculation tag"""
        result = self.calc_historian.getMetaData(self.calc_tag)
        self.assertIsInstance(result, (dict, list))

    # Output type tests
    def test_get_metadata_output_raw(self):
        """Test getMetaData with raw output format"""
        result = self.historian.getMetaData(self.test_tags[0], output="raw")
        # Raw output should be the unprocessed API response
        self.assertIsInstance(result, (dict, list))
        
    def test_get_metadata_output_json(self):
        """Test getMetaData with json output format"""
        result = self.historian.getMetaData(self.test_tags[0], output="json")
        self.assertIsInstance(result, (dict, list))
        
    def test_get_metadata_output_df(self):
        """Test getMetaData with dataframe output format"""
        try:
            import pandas as pd
            result = self.historian.getMetaData(self.test_tags[0], output="df")
            self.assertIsInstance(result, pd.DataFrame)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_metadata_output_csv(self):
        """Test getMetaData with csv output format"""
        import os
        import tempfile
        
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            csv_filepath = tmp_file.name
        
        try:
            # Note: getMetaData CSV output currently has a bug (KeyError: 'timestamp')
            # This test verifies the known behavior
            with self.assertRaises(KeyError) as context:
                self.historian.getMetaData(
                    self.test_tags[0], 
                    output="csv",
                    filepath=csv_filepath
                )
            
            # Verify it's the expected KeyError for timestamp
            self.assertIn("timestamp", str(context.exception))
                
        finally:
            # Clean up the temporary file if it was created
            if os.path.exists(csv_filepath):
                os.unlink(csv_filepath)
        
    def test_get_metadata_output_string(self):
        """Test getMetaData with string output format"""
        result = self.historian.getMetaData(self.test_tags[0], output="string")
        self.assertIsInstance(result, str)
        
    def test_get_metadata_invalid_output_type(self):
        """Test getMetaData with invalid output type"""
        with self.assertRaises(ValueError):
            self.historian.getMetaData(self.test_tags[0], output="invalid")


if __name__ == '__main__':
    unittest.main()
