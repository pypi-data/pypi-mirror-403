#!/usr/bin/env python3

"""
Test script to verify multi-value properties with string values work correctly.
This tests the CombinedProperty iteration behavior for multi-value properties.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns


def test_multivalue_properties():
    """Test multi-value properties with string values."""
    
    print("Testing Multi-Value Properties with String Values")
    print("=" * 60)
    
    # Initialize VitalSigns
    vs = VitalSigns()
    
    # Create a new VITAL_Node
    obj = VITAL_Node()
    obj.URI = "http://example.com/test_multivalue_node"
    obj.name = "Test Multi-Value Node"
    
    print(f"Created object with URI: {obj.URI}")
    print(f"Object name: {obj.name}")
    
    # Find a multi-value property to test with
    # Let's check what properties are available and which ones support multiple values
    print(f"\nAnalyzing available properties...")
    
    domain_props = obj.get_allowed_domain_properties()
    multivalue_props = []
    
    for prop_info in domain_props:
        uri = prop_info['uri']
        prop_class = prop_info['prop_class']
        
        # Get the trait class to check if it supports multiple values
        from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
        trait_class = VitalSignsImpl.get_trait_class_from_uri(uri)
        
        if trait_class and hasattr(trait_class, 'multiple_values') and trait_class.multiple_values:
            multivalue_props.append({
                'uri': uri,
                'short_name': trait_class.get_short_name() if hasattr(trait_class, 'get_short_name') else 'unknown',
                'prop_class': prop_class,
                'trait_class': trait_class
            })
    
    print(f"Found {len(multivalue_props)} multi-value properties:")
    for prop in multivalue_props[:5]:  # Show first 5
        print(f"  - {prop['short_name']} ({prop['uri']})")
    
    if not multivalue_props:
        print("No multi-value properties found! Creating a test case manually...")
        return
    
    # Test with the first multi-value property
    test_prop = multivalue_props[0]
    print(f"\nTesting with property: {test_prop['short_name']} ({test_prop['uri']})")
    
    # Create a multi-value property with string values
    try:
        # Set multiple string values
        test_values = ["value1", "value2", "value3"]
        
        # Create the combined property directly
        combined_prop = VitalSignsImpl.create_property_with_trait(
            test_prop['prop_class'], 
            test_prop['uri'], 
            test_values
        )
        
        # Store it in the object
        obj._properties[test_prop['uri']] = combined_prop
        
        print(f"Created multi-value property with values: {test_values}")
        print(f"Property type: {type(combined_prop)}")
        print(f"Property value: {combined_prop.value}")
        print(f"Property value type: {type(combined_prop.value)}")
        
        # Test hasattr(__iter__)
        has_iter = hasattr(combined_prop, '__iter__')
        print(f"hasattr(__iter__): {has_iter}")
        
        # Test actual iteration
        print(f"Testing iteration...")
        try:
            items = []
            for item in combined_prop:
                items.append(item)
            print(f"✓ Iteration succeeded: {items}")
            print(f"  Expected: {test_values}")
            print(f"  Match: {items == test_values}")
            
            if items != test_values:
                print(f"  ✗ PROBLEM: Expected list of strings, got: {items}")
                print(f"  ✗ This suggests the iteration is going through string characters instead of list items")
                
        except Exception as e:
            print(f"✗ Iteration failed: {e}")
            print(f"  Error type: {type(e)}")
            
    except Exception as e:
        print(f"✗ Failed to create multi-value property: {e}")
        print(f"  Error type: {type(e)}")
        import traceback
        traceback.print_exc()


def test_single_vs_multivalue_comparison():
    """Compare single-value vs multi-value property behavior."""
    
    print(f"\n" + "=" * 60)
    print("COMPARING SINGLE-VALUE vs MULTI-VALUE BEHAVIOR")
    print("=" * 60)
    
    vs = VitalSigns()
    obj = VITAL_Node()
    obj.URI = "http://example.com/comparison_node"
    
    # Test single-value string property
    print(f"\n--- Single-Value String Property ---")
    obj.name = "TestString"
    name_prop_uri = 'http://vital.ai/ontology/vital-core#hasName'
    single_prop = obj._properties[name_prop_uri]
    
    print(f"Property type: {type(single_prop)}")
    print(f"Property value: '{single_prop.value}' (type: {type(single_prop.value)})")
    print(f"hasattr(__iter__): {hasattr(single_prop, '__iter__')}")
    
    try:
        items = list(single_prop)
        print(f"Iteration result: {items}")
    except Exception as e:
        print(f"Iteration failed: {e}")
    
    # Test multi-value property (if we can find one)
    print(f"\n--- Multi-Value Property ---")
    
    # Find a multi-value property
    domain_props = obj.get_allowed_domain_properties()
    from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
    
    multivalue_prop_info = None
    for prop_info in domain_props:
        trait_class = VitalSignsImpl.get_trait_class_from_uri(prop_info['uri'])
        if trait_class and hasattr(trait_class, 'multiple_values') and trait_class.multiple_values:
            multivalue_prop_info = prop_info
            break
    
    if multivalue_prop_info:
        test_values = ["item1", "item2", "item3"]
        multi_prop = VitalSignsImpl.create_property_with_trait(
            multivalue_prop_info['prop_class'],
            multivalue_prop_info['uri'],
            test_values
        )
        
        print(f"Property type: {type(multi_prop)}")
        print(f"Property value: {multi_prop.value} (type: {type(multi_prop.value)})")
        print(f"hasattr(__iter__): {hasattr(multi_prop, '__iter__')}")
        
        try:
            items = list(multi_prop)
            print(f"Iteration result: {items}")
            print(f"Expected: {test_values}")
            print(f"Match: {items == test_values}")
        except Exception as e:
            print(f"Iteration failed: {e}")
    else:
        print("No multi-value properties found for testing")


if __name__ == "__main__":
    test_multivalue_properties()
    test_single_vs_multivalue_comparison()
