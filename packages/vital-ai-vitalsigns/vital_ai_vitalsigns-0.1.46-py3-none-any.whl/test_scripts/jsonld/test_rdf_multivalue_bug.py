#!/usr/bin/env python3

"""
Reproduce the RDF deserialization bug with multi-value properties.
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


def test_rdf_multivalue_bug():
    """Test RDF round-trip with multi-value properties to reproduce the bug."""
    
    print("Testing RDF Multi-Value Property Bug")
    print("=" * 50)
    
    vs = VitalSigns()
    
    # Create object with multi-value property
    obj = VITAL_Node()
    obj.URI = "http://example.com/test_multivalue"
    obj.name = "Test Node"
    
    # Set multi-value property with proper URI values
    test_values = [
        "http://example.com/type/Value1", 
        "http://example.com/type/Value2", 
        "http://example.com/type/Value3"
    ]
    obj.types = test_values
    
    print(f"1. ORIGINAL VALUES:")
    print(f"   {test_values}")
    print(f"   Length: {len(test_values)} items")
    
    # Verify in-memory values
    in_memory = list(obj.types.value)
    print(f"\n2. IN-MEMORY (before RDF):")
    print(f"   {in_memory}")
    print(f"   ✓ Correct: {in_memory == test_values}")
    
    # Export to RDF
    print(f"\n3. EXPORTING TO RDF:")
    rdf_output = obj.to_rdf()
    print(f"   RDF N-Triples generated")
    
    # Count types triples
    types_lines = [line for line in rdf_output.split('\n') if 'types' in line and line.strip()]
    print(f"   Number of types triples: {len(types_lines)}")
    for line in types_lines:
        print(f"     {line}")
    
    # Load from RDF
    print(f"\n4. LOADING FROM RDF:")
    rdf_graph = Graph()
    rdf_graph.parse(data=rdf_output, format='nt')
    triples_list = list(rdf_graph)
    print(f"   Total triples: {len(triples_list)}")
    
    loaded_objects = GraphObject.from_triples_list(triples_list)
    print(f"   Loaded {len(loaded_objects)} graph objects")
    
    # Find the loaded object
    loaded_obj = None
    for obj_loaded in loaded_objects:
        if isinstance(obj_loaded, VITAL_Node) and obj_loaded.URI == "http://example.com/test_multivalue":
            loaded_obj = obj_loaded
            break
    
    if loaded_obj:
        print(f"   ✓ Found loaded VITAL_Node")
        
        # Get the types values
        loaded_types_raw = loaded_obj.types
        print(f"\n5. LOADED VALUES (raw):")
        print(f"   Type: {type(loaded_types_raw)}")
        print(f"   Value: {loaded_types_raw}")
        
        if hasattr(loaded_types_raw, 'value'):
            loaded_types = list(loaded_types_raw.value)
            print(f"\n6. LOADED VALUES (as list):")
            print(f"   Length: {len(loaded_types)} items")
            print(f"   Items:")
            for i, item in enumerate(loaded_types[:10]):
                print(f"     [{i}]: {repr(item)} (len={len(item)})")
            
            # Verification
            print(f"\n7. VERIFICATION:")
            print(f"   Expected: {len(test_values)} strings")
            print(f"   Actual: {len(loaded_types)} items")
            
            if loaded_types == test_values:
                print(f"   ✓ SUCCESS: Values match!")
                return True
            else:
                print(f"   ✗ BUG DETECTED: Values don't match!")
                print(f"   Expected: {test_values}")
                print(f"   Got: {loaded_types}")
                
                # Check if character-split
                if all(isinstance(item, str) and len(item) == 1 for item in loaded_types):
                    print(f"   ✗ Values are split into individual characters!")
                    reconstructed = ''.join(loaded_types)
                    print(f"   Reconstructed: {reconstructed}")
                
                return False
    else:
        print(f"   ✗ ERROR: Could not find loaded object")
        return False


if __name__ == "__main__":
    test_rdf_multivalue_bug()
