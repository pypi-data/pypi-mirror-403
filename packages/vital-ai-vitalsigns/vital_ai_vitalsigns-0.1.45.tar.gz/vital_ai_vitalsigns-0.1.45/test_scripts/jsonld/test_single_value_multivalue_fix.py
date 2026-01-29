#!/usr/bin/env python3

"""
Test to verify that single values in multi-value properties are handled correctly.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from rdflib import Graph


def test_single_value_multivalue_fix():
    """Test that single values in multi-value properties work correctly."""
    
    print("Testing Single Value in Multi-Value Properties")
    print("=" * 50)
    
    vs = VitalSigns()
    
    # Test 1: Single value in multi-value property
    print("TEST 1: Single value in multi-value property")
    obj1 = VITAL_Node()
    obj1.URI = "http://example.com/test_single"
    obj1.name = "Test Single"
    
    # Set multi-value property with single value
    single_value = ["http://example.com/type/SingleValue"]
    obj1.types = single_value
    
    print(f"Original: {single_value}")
    print(f"Length: {len(single_value)} items")
    
    # Export to RDF
    rdf1 = obj1.to_rdf()
    print(f"RDF triples: {rdf1.count(chr(10))} lines")
    
    # Load back
    g1 = Graph()
    g1.parse(data=rdf1, format='nt')
    objs1 = GraphObject.from_triples_list(list(g1))
    loaded1 = objs1[0]
    
    val1 = list(loaded1.types.value)
    print(f"Loaded: {len(val1)} items")
    
    if len(val1) == 1:
        print(f"  Value: {val1[0]}")
        print("  ✓ PASS - Single value preserved")
        test1_pass = True
    else:
        print(f"  First 5: {val1[:5]}")
        print("  ✗ FAIL - Character split detected")
        test1_pass = False
    
    print()
    
    # Test 2: Multiple values in multi-value property
    print("TEST 2: Multiple values in multi-value property")
    obj2 = VITAL_Node()
    obj2.URI = "http://example.com/test_multiple"
    obj2.name = "Test Multiple"
    
    # Set multi-value property with multiple values
    multiple_values = [
        "http://example.com/type/Value1",
        "http://example.com/type/Value2"
    ]
    obj2.types = multiple_values
    
    print(f"Original: {multiple_values}")
    print(f"Length: {len(multiple_values)} items")
    
    # Export to RDF
    rdf2 = obj2.to_rdf()
    print(f"RDF triples: {rdf2.count(chr(10))} lines")
    
    # Load back
    g2 = Graph()
    g2.parse(data=rdf2, format='nt')
    objs2 = GraphObject.from_triples_list(list(g2))
    loaded2 = objs2[0]
    
    val2 = list(loaded2.types.value)
    print(f"Loaded: {len(val2)} items")
    
    if len(val2) == 2:
        print(f"  Values: {val2}")
        print("  ✓ PASS - Multiple values preserved")
        test2_pass = True
    else:
        print(f"  First 5: {val2[:5]}")
        print("  ✗ FAIL - Incorrect value count")
        test2_pass = False
    
    print()
    
    # Test 3: Empty multi-value property
    print("TEST 3: Empty multi-value property")
    obj3 = VITAL_Node()
    obj3.URI = "http://example.com/test_empty"
    obj3.name = "Test Empty"
    
    # Set multi-value property with empty list
    empty_values = []
    obj3.types = empty_values
    
    print(f"Original: {empty_values}")
    print(f"Length: {len(empty_values)} items")
    
    # Export to RDF
    rdf3 = obj3.to_rdf()
    print(f"RDF triples: {rdf3.count(chr(10))} lines")
    
    # Load back
    g3 = Graph()
    g3.parse(data=rdf3, format='nt')
    objs3 = GraphObject.from_triples_list(list(g3))
    loaded3 = objs3[0]
    
    # Check if types property exists
    if hasattr(loaded3, 'types') and loaded3.types is not None:
        val3 = list(loaded3.types.value)
        print(f"Loaded: {len(val3)} items")
        
        if len(val3) == 0:
            print("  ✓ PASS - Empty list preserved")
            test3_pass = True
        else:
            print(f"  Values: {val3}")
            print("  ✗ FAIL - Should be empty")
            test3_pass = False
    else:
        print("  No types property found (expected for empty list)")
        print("  ✓ PASS - Empty property correctly omitted")
        test3_pass = True
    
    print()
    
    # Summary
    print("=" * 50)
    print("SUMMARY:")
    print(f"  Test 1 (Single value): {'PASS' if test1_pass else 'FAIL'}")
    print(f"  Test 2 (Multiple values): {'PASS' if test2_pass else 'FAIL'}")
    print(f"  Test 3 (Empty list): {'PASS' if test3_pass else 'FAIL'}")
    
    all_pass = test1_pass and test2_pass and test3_pass
    print(f"  Overall: {'ALL TESTS PASS' if all_pass else 'SOME TESTS FAILED'}")
    
    return all_pass


if __name__ == "__main__":
    test_single_value_multivalue_fix()
