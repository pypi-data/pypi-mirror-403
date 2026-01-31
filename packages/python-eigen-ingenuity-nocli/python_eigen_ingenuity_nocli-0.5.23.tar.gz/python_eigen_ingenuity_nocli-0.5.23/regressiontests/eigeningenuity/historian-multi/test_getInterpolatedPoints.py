"""
Test getInterpolatedPoints function from historianmulti module
"""

from regressiontests.eigeningenuity.common_multi import BaseHistorianMultiTest
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

    # Output type tests
    def test_get_interpolated_output_raw(self):
        """Test getInterpolatedPoints with raw output format"""
        result = self.historian_multi.getInterpolatedPoints(
            self.test_tags[0],
            self.test_datetime,
            output="raw"
        )
        # Raw output should be the unprocessed API response
        self.assertIsInstance(result, (dict, list))
        
    def test_get_interpolated_output_json(self):
        """Test getInterpolatedPoints with json output format"""
        result = self.historian_multi.getInterpolatedPoints(
            self.test_tags[0],
            self.test_datetime,
            output="json"
        )
        self.assertIsInstance(result, (dict, list))
        
    def test_get_interpolated_output_df(self):
        """Test getInterpolatedPoints with dataframe output format"""
        try:
            import pandas as pd
            result = self.historian_multi.getInterpolatedPoints(
                self.test_tags[0],
                self.test_datetime,
                output="df"
            )
            self.assertIsInstance(result, pd.DataFrame)
        except ImportError:
            self.skipTest("pandas not available for dataframe testing")
            
    def test_get_interpolated_output_csv(self):
        """Test getInterpolatedPoints with csv output format"""
        # TODO: CSV not implemented yet
        self.skipTest("CSV output not implemented yet")
        
        from eigeningenuity.util import EigenException
        with self.assertRaises(EigenException):
            self.historian_multi.getInterpolatedPoints(
                self.test_tags[0], self.test_datetime, output="csv"
            )
        
    def test_get_interpolated_output_string(self):
        """Test getInterpolatedPoints with string output format"""
        result = self.historian_multi.getInterpolatedPoints(
            self.test_tags[0], self.test_datetime, output="string"
        )
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_get_interpolated_invalid_output_type(self):
        """Test getInterpolatedPoints with invalid output format"""
        from eigeningenuity.util import EigenException
        with self.assertRaises(EigenException):
            self.historian_multi.getInterpolatedPoints(
                self.test_tags[0], self.test_datetime, output="invalid"
            )
if __name__ == '__main__':
    unittest.main()
