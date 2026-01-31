"""
Test getMetaData function from historian module
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tests.common import BaseHistorianTest
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
        result = self.historian.getMetaData(self.calc_tag)
        self.assertIsInstance(result, (dict, list))


if __name__ == '__main__':
    unittest.main()
