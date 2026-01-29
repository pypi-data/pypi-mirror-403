#!/usr/bin/env python3

"""
Simple test to reproduce multi-value property character iteration bug.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns


def test_multivalue_simple():
    """Simple test of multi-value property iteration."""
    
    print("Simple Multi-Value Property Test")
    print("=" * 40)
    
    vs = VitalSigns()
    
    # Create object with multi-value property
    obj = VITAL_Node()
    obj.URI = "http://example.com/test"
    
    # Set multi-value property with string values
    test_values = ["string1", "string2", "string3"]
    obj.types = test_values
    
    print(f"Set types to: {test_values}")
    print(f"obj.types returns: {obj.types}")
    
    # Get the CombinedProperty directly
    types_uri = 'http://vital.ai/ontology/vital-core#types'
    combined_prop = obj._properties[types_uri]
    
    print(f"CombinedProperty type: {type(combined_prop)}")
    print(f"CombinedProperty value: {combined_prop.value}")
    print(f"CombinedProperty value type: {type(combined_prop.value)}")
    
    # Test iteration
    print(f"\nTesting iteration:")
    items = list(combined_prop)
    print(f"Iteration result: {items}")
    print(f"Expected: {test_values}")
    print(f"Match: {items == test_values}")
    
    # Check if we got character iteration instead of list iteration
    if items != test_values:
        print(f"\n✗ BUG FOUND!")
        print(f"  Expected list of strings: {test_values}")
        print(f"  Got: {items}")
        
        # Check if it looks like character iteration
        if len(items) > len(test_values):
            all_chars = ''.join(test_values)
            if ''.join(items) == all_chars:
                print(f"  ✗ This appears to be character iteration from concatenated strings")
            else:
                print(f"  ✗ This appears to be character iteration from individual strings")
        
        return False
    
    print(f"\n✓ Multi-value property iteration working correctly")
    return True


if __name__ == "__main__":
    test_multivalue_simple()
