"""
Test getRawDatapoints function from historianmulti module
"""

from regressiontests.eigeningenuity.common_multi import BaseHistorianMultiTest
from eigeningenuity.util import EigenException
import unittest
from datetime import datetime, timedelta


class TestGetRawDataPointsMulti(BaseHistorianMultiTest):
    """Test cases for getRawDatapoints function in historianmulti"""
    
    def test_get_raw_single_tag(self):
        """Test getting raw data points for single tag"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_raw_multiple_tags(self):
        """Test getting raw data points for multiple tags"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags,
            start_time,
            end_time,
            maxpoints=10
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_raw_with_json_output(self):
        """Test getting raw data points with json output"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10,
            output="json"
        )
        self.assertIsInstance(result, (dict, list))
            
    def test_get_raw_with_epoch_times(self):
        """Test getting raw data points with epoch timestamps"""
        end_time = 1714525200 + 3600  # May 1, 2024 3:00:00 AM
        start_time = 1714525200       # May 1, 2024 2:00:00 AM
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=10
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_raw_with_limit(self):
        """Test getting raw data points with maxpoints limit"""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=1)
        max_points = 5
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0],
            start_time,
            end_time,
            maxpoints=max_points
        )
        self.assertIsInstance(result, (dict, list))

    def test_get_raw_output_raw(self):
        """Test getRawDatapoints with raw output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0], start_time, end_time, maxpoints=10, output="raw"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_raw_output_json(self):
        """Test getRawDatapoints with json output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0], start_time, end_time, maxpoints=10, output="json"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_raw_output_df(self):
        """Test getRawDatapoints with dataframe output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        try:
            import pandas as pd
            result = self.historian_multi.getRawDatapoints(
                self.test_tags[0], start_time, end_time, maxpoints=10, output="df"
            )
            self.assertIsInstance(result, pd.DataFrame)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_raw_output_csv(self):
        """Test getRawDatapoints with csv output format"""
        # TODO: CSV not implemented yet
        self.skipTest("CSV output not implemented yet")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        # CSV output might return True/False instead of None
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0], start_time, end_time, maxpoints=10, output="csv"
        )
        # Accept None, True, False, or other return values indicating success
        self.assertIsInstance(result, (type(None), bool, str))
        
    def test_get_raw_output_string(self):
        """Test getRawDatapoints with string output format"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=24)
        
        result = self.historian_multi.getRawDatapoints(
            self.test_tags[0], start_time, end_time, maxpoints=10, output="string"
        )
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        
    def test_get_raw_invalid_output_type(self):
        """Test getRawDatapoints with invalid output format"""
        with self.assertRaises(EigenException):
            self.historian_multi.getRawDatapoints(
                self.test_tags[0], 
                self.start_time, 
                self.end_time,
                output="invalid"
            )


if __name__ == '__main__':
    unittest.main()
