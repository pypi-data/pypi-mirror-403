#!/usr/bin/env python3

"""
Test script for JSON-LD serialization methods to diagnose CombinedProperty issues.

Tests:
1. GraphObject.to_jsonld_list() method
2. obj.to_jsonld() method  
3. Serialization of resulting objects
4. CombinedProperty handling diagnostics
"""

import sys
import os
import json
import traceback
from typing import List, Dict, Any

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from vital_ai_vitalsigns.model.GraphObject import GraphObject
from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns


def create_test_objects() -> List[GraphObject]:
    """Create test GraphObjects with various property types including CombinedProperty."""
    
    # Initialize VitalSigns
    vs = VitalSigns()
    
    objects = []
    
    # Create basic VITAL_Node objects
    for i in range(3):
        obj = VITAL_Node()
        obj.URI = f"http://example.com/node_{i}"
        obj.name = f"Test Node {i}"
        
        # Add some properties that might trigger CombinedProperty issues
        try:
            # Set actual VITAL_Node properties using correct short names
            obj.name = f"Test Node {i}"
            obj.active = True
            obj.timestamp = 1642723200000 + i * 1000  # Some timestamp
            obj.updateTime = 1642723200000 + i * 1000
            
        except Exception as e:
            print(f"Warning: Error setting properties on object {i}: {e}")
        
        objects.append(obj)
    
    # Test property assignment between objects (might trigger CombinedProperty issues)
    if len(objects) >= 2:
        try:
            print(f"Testing property assignment: objects[1].name = objects[0].name")
            objects[1].name = objects[0].name
            print(f"✓ Property assignment succeeded")
        except Exception as e:
            print(f"✗ Property assignment failed: {e}")
            print(f"  Error type: {type(e)}")
        
        # Test direct CombinedProperty assignment
        try:
            print(f"Testing direct CombinedProperty assignment...")
            name_prop_uri = 'http://vital.ai/ontology/vital-core#hasName'
            combined_prop = objects[0]._properties[name_prop_uri]
            print(f"  CombinedProperty type: {type(combined_prop)}")
            print(f"  CombinedProperty value: {combined_prop.value}")
            
            # Try to assign the CombinedProperty directly
            objects[1]._properties[name_prop_uri] = combined_prop
            print(f"✓ Direct CombinedProperty assignment succeeded")
            
        except Exception as e:
            print(f"✗ Direct CombinedProperty assignment failed: {e}")
            print(f"  Error type: {type(e)}")
            
        # Test iteration over CombinedProperty (string property - should iterate over characters)
        try:
            print(f"Testing CombinedProperty string iteration...")
            name_prop_uri = 'http://vital.ai/ontology/vital-core#hasName'
            combined_prop = objects[0]._properties[name_prop_uri]
            
            chars = []
            for item in combined_prop:
                chars.append(item)
            print(f"✓ String CombinedProperty iteration succeeded: {chars}")
            
        except Exception as e:
            print(f"✗ String CombinedProperty iteration failed: {e}")
            print(f"  Error type: {type(e)}")
            
        # Test iteration over non-iterable CombinedProperty (boolean - should fail)
        try:
            print(f"Testing CombinedProperty boolean iteration...")
            active_prop_uri = 'http://vital.ai/ontology/vital-core#isActive'
            combined_prop = objects[0]._properties[active_prop_uri]
            
            items = []
            for item in combined_prop:
                items.append(item)
            print(f"✗ Boolean iteration should have failed but succeeded: {items}")
            
        except TypeError as e:
            print(f"✓ Boolean CombinedProperty correctly not iterable: {e}")
        except Exception as e:
            print(f"✗ Unexpected error in boolean iteration: {e}")
            
        # Test iteration over numeric CombinedProperty (should fail)
        try:
            print(f"Testing CombinedProperty numeric iteration...")
            timestamp_prop_uri = 'http://vital.ai/ontology/vital-core#hasTimestamp'
            combined_prop = objects[0]._properties[timestamp_prop_uri]
            
            items = []
            for item in combined_prop:
                items.append(item)
            print(f"✗ Numeric iteration should have failed but succeeded: {items}")
            
        except TypeError as e:
            print(f"✓ Numeric CombinedProperty correctly not iterable: {e}")
        except Exception as e:
            print(f"✗ Unexpected error in numeric iteration: {e}")
    
    return objects


def test_individual_to_jsonld(objects: List[GraphObject]):
    """Test individual obj.to_jsonld() calls."""
    
    print("\n" + "="*60)
    print("TESTING INDIVIDUAL to_jsonld() CALLS")
    print("="*60)
    
    for i, obj in enumerate(objects):
        print(f"\n--- Testing object {i}: {obj.URI} ---")
        
        try:
            # Test to_jsonld()
            jsonld_result = obj.to_jsonld()
            print(f"✓ to_jsonld() succeeded")
            print(f"  Type: {type(jsonld_result)}")
            print(f"  Keys: {list(jsonld_result.keys()) if isinstance(jsonld_result, dict) else 'Not a dict'}")
            
            # Try to serialize the result
            try:
                json_str = json.dumps(jsonld_result, indent=2)
                print(f"✓ JSON serialization succeeded ({len(json_str)} chars)")
                
                # Show first 200 chars of result
                preview = json_str[:200] + "..." if len(json_str) > 200 else json_str
                print(f"  Preview: {preview}")
                
            except Exception as serialize_error:
                print(f"✗ JSON serialization failed: {serialize_error}")
                print(f"  Error type: {type(serialize_error)}")
                
                # Try to identify problematic values
                if isinstance(jsonld_result, dict):
                    for key, value in jsonld_result.items():
                        try:
                            json.dumps(value)
                        except Exception as val_error:
                            print(f"  Problematic key '{key}': {type(value)} - {val_error}")
                
        except Exception as e:
            print(f"✗ to_jsonld() failed: {e}")
            print(f"  Error type: {type(e)}")
            traceback.print_exc()
            
            # Check object properties for debugging
            print(f"  Object properties: {list(obj._properties.keys()) if hasattr(obj, '_properties') else 'No _properties'}")


def test_to_jsonld_list(objects: List[GraphObject]):
    """Test GraphObject.to_jsonld_list() method."""
    
    print("\n" + "="*60)
    print("TESTING to_jsonld_list() METHOD")
    print("="*60)
    
    try:
        # Test to_jsonld_list()
        print(f"Testing with {len(objects)} objects...")
        jsonld_list_result = GraphObject.to_jsonld_list(objects)
        
        print(f"✓ to_jsonld_list() succeeded")
        print(f"  Type: {type(jsonld_list_result)}")
        print(f"  Keys: {list(jsonld_list_result.keys()) if isinstance(jsonld_list_result, dict) else 'Not a dict'}")
        
        # Check @graph if present
        if isinstance(jsonld_list_result, dict) and '@graph' in jsonld_list_result:
            graph_items = jsonld_list_result['@graph']
            print(f"  @graph contains {len(graph_items)} items")
        
        # Try to serialize the result
        try:
            json_str = json.dumps(jsonld_list_result, indent=2)
            print(f"✓ JSON serialization succeeded ({len(json_str)} chars)")
            
            # Show first 300 chars of result
            preview = json_str[:300] + "..." if len(json_str) > 300 else json_str
            print(f"  Preview: {preview}")
            
        except Exception as serialize_error:
            print(f"✗ JSON serialization failed: {serialize_error}")
            print(f"  Error type: {type(serialize_error)}")
            
            # Try to identify problematic values
            if isinstance(jsonld_list_result, dict):
                for key, value in jsonld_list_result.items():
                    try:
                        json.dumps(value)
                    except Exception as val_error:
                        print(f"  Problematic key '{key}': {type(value)} - {val_error}")
                        
                        # If it's @graph, check individual items
                        if key == '@graph' and isinstance(value, list):
                            for idx, item in enumerate(value):
                                try:
                                    json.dumps(item)
                                except Exception as item_error:
                                    print(f"    Problematic @graph item {idx}: {type(item)} - {item_error}")
                                    
                                    # Check item properties
                                    if isinstance(item, dict):
                                        for item_key, item_value in item.items():
                                            try:
                                                json.dumps(item_value)
                                            except Exception as prop_error:
                                                print(f"      Problematic property '{item_key}': {type(item_value)} - {prop_error}")
            
    except Exception as e:
        print(f"✗ to_jsonld_list() failed: {e}")
        print(f"  Error type: {type(e)}")
        traceback.print_exc()


def diagnose_combined_property_issues(objects: List[GraphObject]):
    """Diagnose CombinedProperty-related issues."""
    
    print("\n" + "="*60)
    print("DIAGNOSING CombinedProperty ISSUES")
    print("="*60)
    
    for i, obj in enumerate(objects):
        print(f"\n--- Analyzing object {i}: {obj.URI} ---")
        
        # Check _properties dictionary
        if hasattr(obj, '_properties'):
            print(f"  _properties keys: {list(obj._properties.keys())}")
            
            for prop_key, prop_value in obj._properties.items():
                print(f"  Property '{prop_key}': {type(prop_value)} = {repr(prop_value)}")
                
                # Check if it's a CombinedProperty
                if hasattr(prop_value, '__class__') and 'CombinedProperty' in str(type(prop_value)):
                    print(f"    ⚠️  Found CombinedProperty!")
                    print(f"    CombinedProperty type: {type(prop_value)}")
                    
                    # Try to inspect CombinedProperty attributes
                    try:
                        if hasattr(prop_value, '__dict__'):
                            print(f"    CombinedProperty attributes: {prop_value.__dict__}")
                        if hasattr(prop_value, '__iter__'):
                            print(f"    CombinedProperty is iterable")
                            try:
                                items = list(prop_value)
                                print(f"    CombinedProperty items: {items}")
                            except Exception as iter_error:
                                print(f"    CombinedProperty iteration failed: {iter_error}")
                        else:
                            print(f"    CombinedProperty is NOT iterable")
                            
                    except Exception as inspect_error:
                        print(f"    CombinedProperty inspection failed: {inspect_error}")
                
                # Test JSON serialization of individual property
                try:
                    json.dumps(prop_value)
                    print(f"    ✓ Property is JSON serializable")
                except Exception as prop_error:
                    print(f"    ✗ Property is NOT JSON serializable: {prop_error}")


def main():
    """Main test function."""
    
    print("JSON-LD Serialization Test Script")
    print("=" * 60)
    
    try:
        # Create test objects
        print("Creating test objects...")
        objects = create_test_objects()
        print(f"Created {len(objects)} test objects")
        
        # Run diagnostics first
        diagnose_combined_property_issues(objects)
        
        # Test individual to_jsonld() calls
        test_individual_to_jsonld(objects)
        
        # Test to_jsonld_list() method
        test_to_jsonld_list(objects)
        
        print("\n" + "="*60)
        print("TEST COMPLETED")
        print("="*60)
        
    except Exception as e:
        print(f"Test script failed with error: {e}")
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
