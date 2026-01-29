#!/usr/bin/env python3

"""
Test specific scenarios that might cause multi-value properties to return
character iteration instead of list iteration.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl


def test_json_ld_context_multivalue():
    """Test multi-value properties in JSON-LD serialization context."""
    
    print("Testing Multi-Value Properties in JSON-LD Context")
    print("=" * 60)
    
    vs = VitalSigns()
    
    # Create objects with multi-value properties
    objects = []
    for i in range(3):
        obj = VITAL_Node()
        obj.URI = f"http://example.com/node_{i}"
        obj.name = f"Node {i}"
        obj.types = [f"Type{i}A", f"Type{i}B", f"Type{i}C"]
        objects.append(obj)
        
        print(f"Created object {i}: types = {obj.types}")
        
        # Test direct iteration on the CombinedProperty
        types_uri = 'http://vital.ai/ontology/vital-core#types'
        if types_uri in obj._properties:
            combined_prop = obj._properties[types_uri]
            items = list(combined_prop)
            print(f"  Direct iteration: {items}")
            expected = [f"Type{i}A", f"Type{i}B", f"Type{i}C"]
            if items != expected:
                print(f"  ✗ BUG: Expected {expected}, got {items}")
    
    # Test JSON-LD serialization
    print(f"\n--- Testing JSON-LD Serialization ---")
    try:
        # Test individual to_jsonld
        for i, obj in enumerate(objects):
            jsonld_result = obj.to_jsonld()
            print(f"Object {i} to_jsonld succeeded")
            
            # Check if types property is in the result
            types_key = 'http://vital.ai/ontology/vital-core#types'
            if types_key in jsonld_result:
                types_value = jsonld_result[types_key]
                print(f"  Types in JSON-LD: {types_value}")
        
        # Test to_jsonld_list
        from vital_ai_vitalsigns.model.GraphObject import GraphObject
        jsonld_list = GraphObject.to_jsonld_list(objects)
        print(f"to_jsonld_list succeeded")
        
    except Exception as e:
        print(f"JSON-LD serialization failed: {e}")
        import traceback
        traceback.print_exc()


def test_property_assignment_chains():
    """Test chains of property assignments that might cause issues."""
    
    print(f"\n" + "=" * 60)
    print("Testing Property Assignment Chains")
    print("=" * 60)
    
    vs = VitalSigns()
    
    # Create source object
    source = VITAL_Node()
    source.URI = "http://example.com/source"
    source.types = ["SourceType1", "SourceType2"]
    
    print(f"Source types: {source.types}")
    
    # Test multiple levels of assignment
    intermediate = VITAL_Node()
    intermediate.URI = "http://example.com/intermediate"
    intermediate.types = source.types  # First assignment
    
    print(f"Intermediate types: {intermediate.types}")
    
    target = VITAL_Node()
    target.URI = "http://example.com/target"
    target.types = intermediate.types  # Second assignment
    
    print(f"Target types: {target.types}")
    
    # Test iteration at each level
    types_uri = 'http://vital.ai/ontology/vital-core#types'
    
    for name, obj in [("Source", source), ("Intermediate", intermediate), ("Target", target)]:
        if types_uri in obj._properties:
            combined_prop = obj._properties[types_uri]
            items = list(combined_prop)
            print(f"{name} iteration: {items}")
            
            expected = ["SourceType1", "SourceType2"]
            if items != expected:
                print(f"  ✗ BUG in {name}: Expected {expected}, got {items}")
                print(f"  ✗ This looks like character iteration instead of list iteration")


def test_edge_cases():
    """Test edge cases that might trigger the bug."""
    
    print(f"\n" + "=" * 60)
    print("Testing Edge Cases")
    print("=" * 60)
    
    vs = VitalSigns()
    
    # Test 1: Single string in multi-value property
    print(f"\n--- Test 1: Single string in multi-value ---")
    obj1 = VITAL_Node()
    obj1.URI = "http://example.com/single_string"
    obj1.types = ["SingleType"]  # Single item list
    
    types_uri = 'http://vital.ai/ontology/vital-core#types'
    combined_prop = obj1._properties[types_uri]
    items = list(combined_prop)
    print(f"Single string in list: {items}")
    print(f"Expected: ['SingleType']")
    
    if items != ["SingleType"]:
        print(f"✗ BUG: Got {items} instead of ['SingleType']")
    
    # Test 2: Empty list
    print(f"\n--- Test 2: Empty list ---")
    obj2 = VITAL_Node()
    obj2.URI = "http://example.com/empty"
    obj2.types = []
    
    combined_prop2 = obj2._properties[types_uri]
    items2 = list(combined_prop2)
    print(f"Empty list: {items2}")
    print(f"Expected: []")
    
    # Test 3: Very long strings
    print(f"\n--- Test 3: Long strings ---")
    obj3 = VITAL_Node()
    obj3.URI = "http://example.com/long_strings"
    long_strings = ["VeryLongTypeNameThatMightCauseIssues", "AnotherLongTypeNameForTesting"]
    obj3.types = long_strings
    
    combined_prop3 = obj3._properties[types_uri]
    items3 = list(combined_prop3)
    print(f"Long strings: {items3}")
    print(f"Expected: {long_strings}")
    
    if items3 != long_strings:
        print(f"✗ BUG with long strings: Got {items3}")
        if len(items3) > len(long_strings):
            print(f"✗ This looks like character iteration - got {len(items3)} items instead of {len(long_strings)}")


def test_concurrent_access():
    """Test concurrent access patterns that might cause issues."""
    
    print(f"\n" + "=" * 60)
    print("Testing Concurrent Access Patterns")
    print("=" * 60)
    
    vs = VitalSigns()
    
    obj = VITAL_Node()
    obj.URI = "http://example.com/concurrent"
    obj.types = ["Type1", "Type2", "Type3"]
    
    types_uri = 'http://vital.ai/ontology/vital-core#types'
    combined_prop = obj._properties[types_uri]
    
    # Test multiple iterations
    print(f"Multiple iterations on same property:")
    for i in range(3):
        items = list(combined_prop)
        print(f"  Iteration {i+1}: {items}")
        
        expected = ["Type1", "Type2", "Type3"]
        if items != expected:
            print(f"  ✗ BUG in iteration {i+1}: Expected {expected}, got {items}")
    
    # Test mixed access patterns
    print(f"\nMixed access patterns:")
    print(f"  Via attribute: {obj.types}")
    print(f"  Via iteration: {list(combined_prop)}")
    print(f"  Via value: {combined_prop.value}")
    print(f"  Via get_value(): {combined_prop.get_value()}")


if __name__ == "__main__":
    test_json_ld_context_multivalue()
    test_property_assignment_chains()
    test_edge_cases()
    test_concurrent_access()
