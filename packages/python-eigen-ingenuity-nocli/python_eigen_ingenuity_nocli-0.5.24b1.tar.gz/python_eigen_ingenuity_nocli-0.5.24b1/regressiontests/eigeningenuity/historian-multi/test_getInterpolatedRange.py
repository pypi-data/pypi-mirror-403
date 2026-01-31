"""
Test getInterpolatedRange function from historianmulti module
"""

from regressiontests.eigeningenuity.common_multi import BaseHistorianMultiTest
import unittest
from datetime import datetime, timedelta
from eigeningenuity.util import EigenException

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
            count=10
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
            count=num_points
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
            count=5,
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
            count=3
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_interpolated_range_output_raw(self):
        """Test getInterpolatedRange with raw output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getInterpolatedRange(
            self.test_tags[0], start_time, end_time, count=5, output="raw"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_interpolated_range_output_json(self):
        """Test getInterpolatedRange with json output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getInterpolatedRange(
            self.test_tags[0], start_time, end_time, count=5, output="json"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_interpolated_range_output_df(self):
        """Test getInterpolatedRange with dataframe output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        try:
            import pandas as pd
            result = self.historian_multi.getInterpolatedRange(
                self.test_tags[0], start_time, end_time, count=5, output="df"
            )
            self.assertIsInstance(result, pd.DataFrame)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_interpolated_range_output_csv(self):
        """Test getInterpolatedRange with csv output format"""
        # TODO: CSV output not implemeted yet
        self.skipTest("CSV output not implemented yet")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # CSV output might return True/False instead of None
        result = self.historian_multi.getInterpolatedRange(
            self.test_tags[0], start_time, end_time, count=5, output="csv"
        )
        # Accept None, True, False, or other return values indicating success
        self.assertIsInstance(result, (type(None), bool, str))
        
    def test_get_interpolated_range_output_string(self):
        """Test getInterpolatedRange with string output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getInterpolatedRange(
            self.test_tags[0], start_time, end_time, count=5, output="string"
        )
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        
    def test_get_interpolated_range_invalid_output_type(self):
        """Test getInterpolatedRange with invalid output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        with self.assertRaises(EigenException):
            self.historian_multi.getInterpolatedRange(
                self.test_tags[0], start_time, end_time, count=5, output="invalid"
            )


if __name__ == '__main__':
    unittest.main()
