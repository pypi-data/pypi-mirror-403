#!/usr/bin/env python3

"""
Debug RDF deserialization to understand why multi-value properties aren't working.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from vital_ai_vitalsigns.model.VITAL_Node import VITAL_Node
from vital_ai_vitalsigns.vitalsigns import VitalSigns
from vital_ai_vitalsigns.model.GraphObject import GraphObject
from rdflib import Graph, URIRef, Literal


def debug_rdf_deserialization():
    """Debug RDF deserialization step by step."""
    
    print("Debug RDF Deserialization")
    print("=" * 40)
    
    vs = VitalSigns()
    
    # Create object with multi-value property
    obj = VITAL_Node()
    obj.URI = "http://example.com/test_multivalue"
    obj.name = "Test Node"
    
    test_values = [
        "http://example.com/type/Value1", 
        "http://example.com/type/Value2", 
        "http://example.com/type/Value3"
    ]
    obj.types = test_values
    
    print(f"Original values: {test_values}")
    
    # Export to RDF
    rdf_output = obj.to_rdf()
    print(f"\nRDF Output:")
    print(rdf_output)
    
    # Parse RDF manually to see what triples we get
    print(f"\nParsing RDF manually:")
    g = Graph()
    g.parse(data=rdf_output, format='nt')
    
    types_uri = 'http://vital.ai/ontology/vital-core#types'
    subject_uri = URIRef("http://example.com/test_multivalue")
    
    print(f"Looking for triples with predicate: {types_uri}")
    types_triples = list(g.triples((subject_uri, URIRef(types_uri), None)))
    print(f"Found {len(types_triples)} types triples:")
    
    for i, (s, p, o) in enumerate(types_triples):
        print(f"  {i+1}: {s} {p} {o}")
        print(f"      Object type: {type(o)}")
        if isinstance(o, URIRef):
            print(f"      Object as string: '{str(o)}'")
    
    # Now test the deserialization logic manually
    print(f"\nTesting deserialization logic:")
    
    # Get trait class for types property
    registry = vs.get_registry()
    trait_cls = registry.vitalsigns_property_classes.get(types_uri, None)
    
    if trait_cls:
        print(f"Trait class: {trait_cls}")
        print(f"Multiple values: {trait_cls.multiple_values}")
        
        if trait_cls.multiple_values:
            print(f"Processing as multi-value property...")
            
            value_list = []
            for multi_value_subject, multi_value_predicate, multi_obj_value in g.triples((subject_uri, URIRef(types_uri), None)):
                print(f"  Processing triple: {multi_value_subject} {multi_value_predicate} {multi_obj_value}")
                print(f"    Object type: {type(multi_obj_value)}")
                
                # Convert RDFLib objects to Python values
                if isinstance(multi_obj_value, Literal):
                    converted_value = multi_obj_value.toPython()
                    print(f"    Converted Literal: {converted_value}")
                    value_list.append(converted_value)
                elif isinstance(multi_obj_value, URIRef):
                    converted_value = str(multi_obj_value)
                    print(f"    Converted URIRef: {converted_value}")
                    value_list.append(converted_value)
                else:
                    print(f"    Other type: {multi_obj_value}")
                    value_list.append(multi_obj_value)
            
            print(f"Final value_list: {value_list}")
            print(f"Length: {len(value_list)}")
            
            # Test creating the property manually
            print(f"\nTesting manual property creation:")
            
            # Get property info
            domain_props = obj.get_allowed_domain_properties()
            types_prop_info = None
            for prop_info in domain_props:
                if prop_info['uri'] == types_uri:
                    types_prop_info = prop_info
                    break
            
            if types_prop_info:
                print(f"Property class: {types_prop_info['prop_class']}")
                
                from vital_ai_vitalsigns.impl.vitalsigns_impl import VitalSignsImpl
                
                # Create the property manually
                manual_prop = VitalSignsImpl.create_property_with_trait(
                    types_prop_info['prop_class'],
                    types_uri,
                    value_list
                )
                
                print(f"Manual property type: {type(manual_prop)}")
                print(f"Manual property value: {manual_prop.value}")
                print(f"Manual property value type: {type(manual_prop.value)}")
                
                # Test iteration
                try:
                    manual_items = list(manual_prop)
                    print(f"Manual property iteration: {manual_items}")
                    print(f"Manual iteration length: {len(manual_items)}")
                except Exception as e:
                    print(f"Manual property iteration failed: {e}")
    
    # Now test full deserialization
    print(f"\nTesting full deserialization:")
    loaded_objects = GraphObject.from_triples_list(list(g))
    print(f"Loaded {len(loaded_objects)} objects")
    
    if loaded_objects:
        loaded_obj = loaded_objects[0]
        print(f"Loaded object type: {type(loaded_obj)}")
        print(f"Loaded object URI: {loaded_obj.URI}")
        
        if hasattr(loaded_obj, 'types'):
            loaded_types = loaded_obj.types
            print(f"Loaded types: {loaded_types}")
            print(f"Loaded types type: {type(loaded_types)}")
            print(f"Loaded types value: {loaded_types.value}")
            print(f"Loaded types value type: {type(loaded_types.value)}")
            
            try:
                loaded_items = list(loaded_types)
                print(f"Loaded types iteration: {loaded_items}")
                print(f"Loaded iteration length: {len(loaded_items)}")
            except Exception as e:
                print(f"Loaded types iteration failed: {e}")


if __name__ == "__main__":
    debug_rdf_deserialization()
