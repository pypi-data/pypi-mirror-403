import libcst as cst
from typing import Union, Optional

class PatchTransformer(cst.CSTTransformer):
    """
    A LibCST transformer that replaces a specific function or class definition
    with a new one, while preserving the surrounding file structure (comments, imports).
    """
    def __init__(self, target_name: str, new_node: Union[cst.FunctionDef, cst.ClassDef]):
        self.target_name = target_name
        self.new_node = new_node
        self.found = False

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        if original_node.name.value == self.target_name:
            self.found = True
            # We return the new node.
            # Preserve leading comments/lines from the original node
            preserved_node = self.new_node.with_changes(leading_lines=original_node.leading_lines)
            return preserved_node
        return updated_node

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        if original_node.name.value == self.target_name:
            self.found = True
            return self.new_node
        return updated_node
