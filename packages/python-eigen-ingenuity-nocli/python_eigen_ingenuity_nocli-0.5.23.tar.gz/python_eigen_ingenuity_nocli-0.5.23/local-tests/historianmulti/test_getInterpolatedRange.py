"""
Test getInterpolatedRange function from historianmulti module
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from tests.historianmulti.common_multi import BaseHistorianMultiTest
import unittest
from datetime import datetime, timedelta


class TestGetInterpolatedRangeMulti(BaseHistorianMultiTest):
    """Test cases for getInterpolatedRange function in historianmulti"""
    
    def test_get_interpolated_range_single_tag(self):
        """Test getting interpolated range for single tag"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getInterpolatedRange(
            self.test_tags[0],
            start_time,
            end_time,
            num_points=10
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_interpolated_range_multiple_tags(self):
        """Test getting interpolated range for multiple tags"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        num_points = 5
        
        result = self.historian_multi.getInterpolatedRange(
            self.test_tags,
            start_time,
            end_time,
            num_points=num_points
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_interpolated_range_with_json_output(self):
        """Test getting interpolated range with json output"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getInterpolatedRange(
            self.test_tags[0],
            start_time,
            end_time,
            num_points=5,
            output="json"
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_interpolated_range_with_epoch_times(self):
        """Test getting interpolated range with epoch timestamps"""
        end_time = 1714525200 + 3600  # May 1, 2024 3:00:00 AM
        start_time = 1714525200       # May 1, 2024 2:00:00 AM
        
        result = self.historian_multi.getInterpolatedRange(
            self.test_tags[0],
            start_time,
            end_time,
            num_points=3
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_interpolated_range_single_point(self):
        """Test getting interpolated range with single point"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getInterpolatedRange(
            self.test_tags[0],
            start_time,
            end_time,
            num_points=1
        )
        self.assertIsInstance(result, (dict, list))


if __name__ == '__main__':
    unittest.main()
