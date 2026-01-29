#!/usr/bin/env python3

"""
Test script to reproduce the specific multi-value property bug where
iteration returns characters instead of the list of string values.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl


def test_multivalue_property_scenarios():
    """Test various scenarios that might trigger the multi-value bug."""
    
    print("Testing Multi-Value Property Bug Scenarios")
    print("=" * 60)
    
    vs = VitalSigns()
    
    # Scenario 1: Direct property assignment via attribute
    print("\n--- Scenario 1: Direct attribute assignment ---")
    obj1 = VITAL_Node()
    obj1.URI = "http://example.com/node1"
    
    # Try to set a multi-value property via attribute (if possible)
    try:
        # The 'types' property supports multiple values
        obj1.types = ["type1", "type2", "type3"]
        print(f"Set types via attribute: {obj1.types}")
        
        # Get the actual CombinedProperty
        types_uri = 'http://vital.ai/ontology/vital-core#types'
        if types_uri in obj1._properties:
            combined_prop = obj1._properties[types_uri]
            print(f"CombinedProperty type: {type(combined_prop)}")
            print(f"CombinedProperty value: {combined_prop.value}")
            print(f"CombinedProperty value type: {type(combined_prop.value)}")
            
            # Test iteration
            items = list(combined_prop)
            print(f"Iteration result: {items}")
            print(f"Expected: ['type1', 'type2', 'type3']")
            print(f"Match: {items == ['type1', 'type2', 'type3']}")
            
            if items != ['type1', 'type2', 'type3']:
                print(f"✗ BUG FOUND: Expected list of strings, got character iteration")
        
    except Exception as e:
        print(f"Failed to set types: {e}")
    
    # Scenario 2: Property assignment between objects
    print("\n--- Scenario 2: Property assignment between objects ---")
    obj2 = VITAL_Node()
    obj2.URI = "http://example.com/node2"
    obj3 = VITAL_Node()
    obj3.URI = "http://example.com/node3"
    
    try:
        # Set multi-value property on obj2
        obj2.types = ["sourceType1", "sourceType2"]
        print(f"obj2.types: {obj2.types}")
        
        # Assign property from obj2 to obj3
        obj3.types = obj2.types
        print(f"obj3.types after assignment: {obj3.types}")
        
        # Test iteration on both
        types_uri = 'http://vital.ai/ontology/vital-core#types'
        
        if types_uri in obj2._properties:
            prop2 = obj2._properties[types_uri]
            items2 = list(prop2)
            print(f"obj2 iteration: {items2}")
        
        if types_uri in obj3._properties:
            prop3 = obj3._properties[types_uri]
            items3 = list(prop3)
            print(f"obj3 iteration: {items3}")
            
            if items3 != ["sourceType1", "sourceType2"]:
                print(f"✗ BUG FOUND in property assignment scenario")
        
    except Exception as e:
        print(f"Failed property assignment test: {e}")
        import traceback
        traceback.print_exc()
    
    # Scenario 3: Direct CombinedProperty creation and assignment
    print("\n--- Scenario 3: Direct CombinedProperty creation ---")
    try:
        obj4 = VITAL_Node()
        obj4.URI = "http://example.com/node4"
        
        # Get property info for types
        domain_props = obj4.get_allowed_domain_properties()
        types_prop_info = None
        
        for prop_info in domain_props:
            if prop_info['uri'] == 'http://vital.ai/ontology/vital-core#types':
                types_prop_info = prop_info
                break
        
        if types_prop_info:
            # Create CombinedProperty directly
            test_values = ["directType1", "directType2", "directType3"]
            combined_prop = VitalSignsImpl.create_property_with_trait(
                types_prop_info['prop_class'],
                types_prop_info['uri'],
                test_values
            )
            
            print(f"Created CombinedProperty with values: {test_values}")
            print(f"Property value: {combined_prop.value}")
            
            # Store in object
            obj4._properties[types_prop_info['uri']] = combined_prop
            
            # Test iteration
            items = list(combined_prop)
            print(f"Direct iteration: {items}")
            
            # Test via object attribute
            obj_types = obj4.types
            print(f"Via object attribute: {obj_types}")
            
            if items != test_values:
                print(f"✗ BUG FOUND in direct CombinedProperty scenario")
                print(f"  Expected: {test_values}")
                print(f"  Got: {items}")
        
    except Exception as e:
        print(f"Failed direct CombinedProperty test: {e}")
        import traceback
        traceback.print_exc()
    
    # Scenario 4: Test with different multi-value property types
    print("\n--- Scenario 4: Different property types ---")
    
    # Find other multi-value properties
    domain_props = obj1.get_allowed_domain_properties()
    multivalue_props = []
    
    for prop_info in domain_props:
        trait_class = VitalSignsImpl.get_trait_class_from_uri(prop_info['uri'])
        if trait_class and hasattr(trait_class, 'multiple_values') and trait_class.multiple_values:
            multivalue_props.append(prop_info)
    
    print(f"Testing {len(multivalue_props)} multi-value properties:")
    
    for i, prop_info in enumerate(multivalue_props[:3]):  # Test first 3
        try:
            trait_class = VitalSignsImpl.get_trait_class_from_uri(prop_info['uri'])
            short_name = trait_class.get_short_name() if hasattr(trait_class, 'get_short_name') else 'unknown'
            
            print(f"\n  Property {i+1}: {short_name} ({prop_info['uri']})")
            
            test_values = [f"value{j}" for j in range(1, 4)]
            combined_prop = VitalSignsImpl.create_property_with_trait(
                prop_info['prop_class'],
                prop_info['uri'],
                test_values
            )
            
            items = list(combined_prop)
            print(f"    Values: {test_values}")
            print(f"    Iteration: {items}")
            print(f"    Match: {items == test_values}")
            
            if items != test_values:
                print(f"    ✗ BUG FOUND with property {short_name}")
        
        except Exception as e:
            print(f"    Failed to test property: {e}")


if __name__ == "__main__":
    test_multivalue_property_scenarios()
