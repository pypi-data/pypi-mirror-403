"""
Common test configuration and utilities for historian tests
"""
import sys
import os
import unittest
import warnings
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Check if we should use local development version
USE_LOCAL = os.environ.get('USE_LOCAL_EIGENINGENUITY', 'false').lower() == 'true'

if USE_LOCAL:
    # Add the parent directory to the Python path to import local version
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    print("REGRESSION TESTS: Using LOCAL development version")
else:
    print("REGRESSION TESTS: Using PIP-INSTALLED version")

# Import eigeningenuity (will use local or installed based on path setup above)
from eigeningenuity import EigenServer, get_historian, disable_azure_auth

# Disable warnings and Azure auth for testing
warnings.simplefilter('ignore', InsecureRequestWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore', category=InsecureRequestWarning)
disable_azure_auth()

class BaseHistorianTest(unittest.TestCase):
    """Base class for historian tests with common setup"""
    
    def debug_result(self, test_name, result, additional_info=None):
        """Centralized debug function for test results
        
        Args:
            test_name (str): Name of the test method
            result: The result object to debug
            additional_info (dict, optional): Additional context information
        """
        print(f"\n{'='*60}")
        print(f"DEBUG: {test_name}")
        print('='*60)
        
        if additional_info:
            print("Additional Info:")
            for key, value in additional_info.items():
                print(f"  {key}: {value}")
            print()
        
        print(f"Result Type: {type(result)}")
        print(f"Result Content: {result}")
        
        if isinstance(result, dict):
            print("\nDict Analysis:")
            print(f"  Keys: {list(result.keys())}")
            print(f"  Number of keys: {len(result)}")
            
            for key, value in result.items():
                print(f"  [{key}]: {value} (type: {type(value)})")
                
                # Handle nested dictionaries
                if isinstance(value, dict) and value:
                    print(f"    Nested dict keys: {list(value.keys())}")
                    for nested_key, nested_value in value.items():
                        print(f"      {nested_key}: {nested_value}")
                
                # Handle lists
                elif isinstance(value, list):
                    print(f"    List length: {len(value)}")
                    if value:
                        print(f"    First item: {value[0]}")
                        if len(value) > 1:
                            print(f"    Last item: {value[-1]}")
                            
        elif isinstance(result, list):
            print("\nList Analysis:")
            print(f"  Length: {len(result)}")
            
            if result:
                print(f"  First item: {result[0]} (type: {type(result[0])})")
                if len(result) > 1:
                    print(f"  Last item: {result[-1]} (type: {type(result[-1])})")
                
                # Show sample of items if they're dicts
                for i, item in enumerate(result[:3]):
                    if isinstance(item, dict):
                        print(f"  Item[{i}] keys: {list(item.keys())}")
                
                if len(result) > 3:
                    print(f"  ... and {len(result) - 3} more items")
                    
        elif isinstance(result, bool):
            print(f"\nBoolean Value: {result}")
            
        elif isinstance(result, str):
            print("\nString Analysis:")
            print(f"  Length: {len(result)}")
            print(f"  First 100 chars: {result[:100]}")
            if len(result) > 100:
                print(f"  ... (truncated, total length: {len(result)})")
                
        elif result is None:
            print("\nResult is None")
            
        else:
            print("\nOther type analysis:")
            print(f"  String representation: {str(result)}")
            if hasattr(result, '__len__'):
                print(f"  Length: {len(result)}")
        
        print('='*60)
    
    def setUp(self):
        """Common setup for all historian tests"""
        self.server = EigenServer("demo-dev.eigen.co")
        self.historian_name = "Demo-influxdb"
        self.historian = get_historian(self.historian_name, self.server)
        self.calc_historian = get_historian("calc", self.server)
        self.test_datetime = datetime(2024, 5, 1, 2, 0, 0)
        self.test_tags = ["DEMO_02TI301.PV", "DEMO_02TI201.PV"]
        self.test_tags_with_historian = [f"{self.historian_name}/DEMO_02TI301.PV", f"{self.historian_name}/DEMO_02TI201.PV"]
        self.calc_tag = "ADD(1,2)"
        
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
