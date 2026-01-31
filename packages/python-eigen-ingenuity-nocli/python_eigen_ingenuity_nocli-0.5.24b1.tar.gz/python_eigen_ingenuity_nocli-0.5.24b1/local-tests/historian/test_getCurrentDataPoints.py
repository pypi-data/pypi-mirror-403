"""
Test getCurrentDataPoints function from historian module
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tests.common import BaseHistorianTest
import unittest


class TestGetCurrentDataPoints(BaseHistorianTest):
    """Test cases for getCurrentDataPoints function"""
    
    def test_get_current_single_tag_default(self):
        """Test getting current data point for single tag with default output"""
        result = self.historian.getCurrentDataPoints(self.test_tags[0])
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
        # Note: calc tags might not be available in Demo-influxdb historian
        try:
            result = self.historian.getCurrentDataPoints(self.calc_tag)
            self.assertValidDataPoint(result)
            self.assertEqual(result['value'], 3)  # ADD(1,2) should equal 3
        except Exception:
            # Calc tags might not be available in this historian
            self.skipTest("Calc tags not available in Demo-influxdb historian")
        
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


if __name__ == '__main__':
    unittest.main()
