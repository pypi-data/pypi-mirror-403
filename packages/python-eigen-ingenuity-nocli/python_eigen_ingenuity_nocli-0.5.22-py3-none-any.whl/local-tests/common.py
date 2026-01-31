"""
Common test configuration and utilities for historian tests
"""
import sys
import os
import unittest
import warnings
from datetime import datetime

# Add the parent directory to the Python path to import local version
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import local version
from eigeningenuity import EigenServer, get_historian, disable_azure_auth
from urllib3.exceptions import InsecureRequestWarning

# Disable warnings and Azure auth for testing
warnings.simplefilter('ignore', InsecureRequestWarning)
disable_azure_auth()

class BaseHistorianTest(unittest.TestCase):
    """Base class for historian tests with common setup"""
    
    def setUp(self):
        """Common setup for all historian tests"""
        self.server = EigenServer("demo-dev.eigen.co")
        self.historian_name = "Demo-influxdb"
        self.historian = get_historian(self.historian_name, self.server)
        self.test_datetime = datetime(2024, 5, 1, 2, 0, 0)
        self.test_tags = ["DEMO_02TI301.PV", "DEMO_02TI201.PV"]
        self.test_tags_with_historian = [f"{self.historian_name}/DEMO_02TI301.PV", f"{self.historian_name}/DEMO_02TI201.PV"]
        self.calc_tag = "calc/ADD(1,2)"
        
    def assertValidDataPoint(self, data_point):
        """Assert that a data point has valid structure"""
        self.assertIsInstance(data_point, dict)
        self.assertIn('value', data_point)
        self.assertIn('timestamp', data_point)
        self.assertIn('status', data_point)
        
    def assertValidDataPointList(self, data_points):
        """Assert that a list of data points is valid"""
        self.assertIsInstance(data_points, list)
        for dp in data_points:
            self.assertValidDataPoint(dp)
