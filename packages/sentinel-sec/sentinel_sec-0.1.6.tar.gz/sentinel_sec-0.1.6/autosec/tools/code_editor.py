import libcst as cst
from typing import Optional
from autosec.tools.cst_transformer import PatchTransformer

def apply_patch(source_code: str, target_name: str, new_code: str) -> str:
    """
    Applies a patch to the source code by replacing the target function/class
    with the new code definition.
    
    Args:
        source_code: The original file content.
        target_name: The name of the function/class to replace.
        new_code: The new function/class definition (valid Python code).
        
    Returns:
        The modified source code with comments/formatting preserved.
    """
    try:
        # 1. Parse original source
        source_tree = cst.parse_module(source_code)
        
        # 2. Parse new code to get the node
        # We assume new_code is a valid partial module (e.g. "def foo(): ...")
        new_tree = cst.parse_module(new_code)
        
        new_node = None
        # Find the first FunctionDef or ClassDef in the new code
        for node in new_tree.body:
            if isinstance(node, (cst.FunctionDef, cst.ClassDef)):
                new_node = node
                break
        
        if not new_node:
            raise ValueError("No function or class definition found in the new code.")
            
        # 3. Apply transformation
        transformer = PatchTransformer(target_name, new_node)
        modified_tree = source_tree.visit(transformer)
        
        if not transformer.found:
            # If target not found, we might want to append it? 
            # For this strict version, we raise an error or return original.
            # Let's return original with a warning printed (or raise).
            print(f"Warning: Target '{target_name}' not found in source.")
            return source_code
            
        return modified_tree.code
        
    except Exception as e:
        print(f"Error applying patch: {e}")
        return source_code
