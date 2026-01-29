#!/usr/bin/env python3

"""
Debug script to check if multi-value properties are getting the wrong class inheritance.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
from vital_ai_vitalsigns.model.properties.MultiValueProperty import MultiValueProperty


def debug_class_inheritance():
    """Debug the class inheritance for CombinedProperty objects."""
    
    print("Debugging CombinedProperty Class Inheritance")
    print("=" * 60)
    
    vs = VitalSigns()
    obj = VITAL_Node()
    obj.URI = "http://example.com/debug_node"
    
    # Test single-value property
    print("\n--- Single-Value Property (name) ---")
    obj.name = "TestName"
    name_uri = 'http://vital.ai/ontology/vital-core#hasName'
    name_prop = obj._properties[name_uri]
    
    print(f"Property type: {type(name_prop)}")
    print(f"MRO: {type(name_prop).__mro__}")
    print(f"Is MultiValueProperty: {isinstance(name_prop, MultiValueProperty)}")
    print(f"Has __getattribute__: {hasattr(type(name_prop), '__getattribute__')}")
    
    # Check trait class
    name_trait = VitalSignsImpl.get_trait_class_from_uri(name_uri)
    print(f"Trait class: {name_trait}")
    print(f"Multiple values: {getattr(name_trait, 'multiple_values', 'N/A')}")
    
    # Test multi-value property
    print("\n--- Multi-Value Property (types) ---")
    obj.types = ["type1", "type2"]
    types_uri = 'http://vital.ai/ontology/vital-core#types'
    types_prop = obj._properties[types_uri]
    
    print(f"Property type: {type(types_prop)}")
    print(f"MRO: {type(types_prop).__mro__}")
    print(f"Is MultiValueProperty: {isinstance(types_prop, MultiValueProperty)}")
    print(f"Has __getattribute__: {hasattr(type(types_prop), '__getattribute__')}")
    
    # Check trait class
    types_trait = VitalSignsImpl.get_trait_class_from_uri(types_uri)
    print(f"Trait class: {types_trait}")
    print(f"Multiple values: {getattr(types_trait, 'multiple_values', 'N/A')}")
    
    # Test iteration behavior
    print(f"\n--- Iteration Behavior ---")
    
    print(f"Single-value (name):")
    print(f"  hasattr(__iter__): {hasattr(name_prop, '__iter__')}")
    try:
        name_items = list(name_prop)
        print(f"  Iteration: {name_items}")
    except Exception as e:
        print(f"  Iteration failed: {e}")
    
    print(f"Multi-value (types):")
    print(f"  hasattr(__iter__): {hasattr(types_prop, '__iter__')}")
    try:
        types_items = list(types_prop)
        print(f"  Iteration: {types_items}")
        print(f"  Expected: ['type1', 'type2']")
        print(f"  Match: {types_items == ['type1', 'type2']}")
        
        if types_items != ['type1', 'type2']:
            print(f"  ✗ BUG: Multi-value iteration is wrong!")
            print(f"  ✗ Got character iteration instead of list items")
    except Exception as e:
        print(f"  Iteration failed: {e}")
    
    # Test direct class creation
    print(f"\n--- Direct Class Creation Test ---")
    
    # Create single-value class
    name_prop_info = None
    types_prop_info = None
    
    for prop_info in obj.get_allowed_domain_properties():
        if prop_info['uri'] == name_uri:
            name_prop_info = prop_info
        elif prop_info['uri'] == types_uri:
            types_prop_info = prop_info
    
    if name_prop_info and types_prop_info:
        # Create single-value CombinedProperty class
        name_trait_class = VitalSignsImpl.get_trait_class_from_uri(name_uri)
        single_class = VitalSignsImpl.create_property_with_trait_class(
            name_prop_info['prop_class'], 
            name_trait_class
        )
        print(f"Single-value class: {single_class}")
        print(f"Single-value MRO: {single_class.__mro__}")
        print(f"Single-value multiple_values: {getattr(name_trait_class, 'multiple_values', 'N/A')}")
        
        # Create multi-value CombinedProperty class
        types_trait_class = VitalSignsImpl.get_trait_class_from_uri(types_uri)
        multi_class = VitalSignsImpl.create_property_with_trait_class(
            types_prop_info['prop_class'], 
            types_trait_class
        )
        print(f"Multi-value class: {multi_class}")
        print(f"Multi-value MRO: {multi_class.__mro__}")
        print(f"Multi-value multiple_values: {getattr(types_trait_class, 'multiple_values', 'N/A')}")
        
        # Check if multi-value class has the wrong __getattribute__
        single_has_getattr = '__getattribute__' in single_class.__dict__
        multi_has_getattr = '__getattribute__' in multi_class.__dict__
        
        print(f"Single-value has custom __getattribute__: {single_has_getattr}")
        print(f"Multi-value has custom __getattribute__: {multi_has_getattr}")
        
        if multi_has_getattr:
            print(f"✗ PROBLEM: Multi-value class should NOT have custom __getattribute__")


if __name__ == "__main__":
    debug_class_inheritance()
