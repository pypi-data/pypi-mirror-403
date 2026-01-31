"""
Test getInterpolatedPoints function from historianmulti module
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tests.historianmulti.common_multi import BaseHistorianMultiTest
import unittest


class TestGetInterpolatedPointsMulti(BaseHistorianMultiTest):
    """Test cases for getInterpolatedPoints function in historianmulti"""
    
    def test_get_interpolated_single_tag_single_timestamp(self):
        """Test getting interpolated point for single tag at single timestamp"""
        result = self.historian_multi.getInterpolatedPoints(
            self.test_tags[0], 
            self.test_datetime
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_interpolated_single_tag_multiple_timestamps(self):
        """Test getting interpolated points for single tag at multiple timestamps"""
        timestamps = [self.test_datetime, 1718180259]
        result = self.historian_multi.getInterpolatedPoints(
            self.test_tags[0], 
            timestamps
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_interpolated_multiple_tags_single_timestamp(self):
        """Test getting interpolated points for multiple tags at single timestamp"""
        result = self.historian_multi.getInterpolatedPoints(
            self.test_tags, 
            self.test_datetime
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_interpolated_multiple_tags_multiple_timestamps(self):
        """Test getting interpolated points for multiple tags at multiple timestamps"""
        timestamps = [self.test_datetime, 1718180259]
        result = self.historian_multi.getInterpolatedPoints(
            self.test_tags, 
            timestamps
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_interpolated_with_json_output(self):
        """Test getting interpolated points with json output format"""
        result = self.historian_multi.getInterpolatedPoints(
            self.test_tags[0], 
            self.test_datetime,
            output="json"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_interpolated_with_epoch_timestamp(self):
        """Test getting interpolated points with epoch timestamp"""
        epoch_time = 1714525200  # May 1, 2024 2:00:00 AM
        result = self.historian_multi.getInterpolatedPoints(
            self.test_tags[0], 
            epoch_time
        )
        self.assertIsInstance(result, (dict, list))


if __name__ == '__main__':
    unittest.main()
