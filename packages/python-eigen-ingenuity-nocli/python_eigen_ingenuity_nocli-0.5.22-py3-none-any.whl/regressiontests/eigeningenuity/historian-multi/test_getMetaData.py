"""
Test getMetaData function from historianmulti module
"""

from regressiontests.eigeningenuity.common_multi import BaseHistorianMultiTest
import unittest


class TestGetMetaDataMulti(BaseHistorianMultiTest):
    """Test cases for getMetaData function in historianmulti"""
    
    def test_get_metadata_default(self):
        """Test getting metadata with default parameters"""
        result = self.historian_multi.getMetaData()
        self.assertIsInstance(result, (dict, list))
        
    def test_get_metadata_with_historian(self):
        """Test getting metadata with specific historian"""
        result = self.historian_multi.getMetaData(historian=self.historian_name)
        self.assertIsInstance(result, (dict, list))
        
    def test_get_metadata_with_match_pattern(self):
        """Test getting metadata with match pattern"""
        result = self.historian_multi.getMetaData(
            historian=self.historian_name,
            match="TI"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_metadata_with_limit(self):
        """Test getting metadata with limit"""
        result = self.historian_multi.getMetaData(
            historian=self.historian_name,
            limit=5
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_metadata_specific_pattern(self):
        """Test getting metadata with specific pattern"""
        result = self.historian_multi.getMetaData(
            historian=self.historian_name,
            match="*301*"
        )
        self.assertIsInstance(result, (dict, list))


if __name__ == '__main__':
    unittest.main()
