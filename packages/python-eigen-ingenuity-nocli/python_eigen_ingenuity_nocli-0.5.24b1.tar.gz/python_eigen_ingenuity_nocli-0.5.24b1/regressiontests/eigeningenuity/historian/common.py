"""
Common utilities and base classes for historian regression tests
"""

import unittest
import os

try:
    # Try local import first if LOCAL_TEST environment variable is set
    if os.getenv('LOCAL_TEST') == '1':
        from eigeningenuity.historian import Historian
    else:
        raise ImportError("Using pip version")
except ImportError:
    # Fall back to pip installed version
    from python_eigen_ingenuity.eigeningenuity.historian import Historian


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
        """Setup test environment"""
        # Setting debug to True to capture all output
        self.historian = Historian(debug=True)
        
        # Test credentials and configuration
        self.test_tag = "EIGEN.MEASUREMENT_1"
        self.test_calc_tag = "eigen_manual_input/CALC_TAG_1"
        
        # Valid output types for testing
        self.valid_output_types = ["raw", "json", "df", "csv", "string"]
