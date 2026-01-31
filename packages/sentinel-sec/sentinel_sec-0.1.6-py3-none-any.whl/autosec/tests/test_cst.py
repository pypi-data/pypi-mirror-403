import sys
import os
import unittest
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from autosec.tools.code_editor import apply_patch

class TestLibCST(unittest.TestCase):
    def test_replace_function_preserve_comments(self):
        source = """
import os

# This is a critical function
# Do not touch the whitespace!
def vulnerable_function(x):
    # Some internal logic
    return x + 1

def other_function():
    pass
"""
        new_code = """
def vulnerable_function(x):
    # Patched logic
    if x is None:
        return 0
    return x + 1
"""
        expected_substring = "# This is a critical function"
        
        modified = apply_patch(source, "vulnerable_function", new_code)
        
        # assertions
        self.assertIn(expected_substring, modified)
        self.assertIn("if x is None:", modified)
        self.assertIn("def other_function():", modified)
        
        print("\n--- Original ---\n", source)
        print("\n--- Modified ---\n", modified)

    def test_target_not_found(self):
        source = "def foo(): pass"
        new_code = "def bar(): pass"
        modified = apply_patch(source, "baz", new_code)
        self.assertEqual(source, modified)

if __name__ == "__main__":
    unittest.main()
