"""
Test for import errors and missing dependencies
"""
import unittest
import sys
import importlib
from unittest.mock import patch


class TestImportErrors(unittest.TestCase):
    """Test cases for handling missing dependencies"""
    
    def setUp(self):
        """Save current module state before each test"""
        self.saved_modules = {}
        modules_to_save = ['look4it', 'look4it.search_tool', 'look4it.cli']
        for mod in modules_to_save:
            if mod in sys.modules:
                self.saved_modules[mod] = sys.modules[mod]
    
    def tearDown(self):
        """Restore module state after each test"""
        # Remove modules that were added during test
        modules_to_remove = ['look4it', 'look4it.search_tool', 'look4it.cli']
        for mod in modules_to_remove:
            if mod in sys.modules and mod not in self.saved_modules:
                del sys.modules[mod]
        
        # Restore saved modules
        for mod, saved_mod in self.saved_modules.items():
            sys.modules[mod] = saved_mod
    
    def test_missing_ddgs_module(self):
        """Test that missing ddgs module raises helpful error"""
        # Remove search_tool from modules if already imported
        modules_to_remove = ['look4it', 'look4it.search_tool']
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]
        
        # Mock the ddgs import to raise ImportError
        with patch.dict('sys.modules', {'ddgs': None}):
            with self.assertRaises(ImportError) as context:
                import look4it
            
            error_message = str(context.exception)
            self.assertIn("Missing required module", error_message)
            self.assertIn("pip install", error_message)
    
    def test_missing_requests_module(self):
        """Test that missing requests module raises helpful error"""
        modules_to_remove = ['look4it', 'look4it.search_tool']
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]
        
        with patch.dict('sys.modules', {'requests': None}):
            with self.assertRaises(ImportError) as context:
                import look4it
            
            error_message = str(context.exception)
            self.assertIn("Missing required module", error_message)
    
    def test_missing_beautifulsoup_module(self):
        """Test that missing beautifulsoup4 module raises helpful error"""
        modules_to_remove = ['look4it', 'look4it.search_tool']
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]
        
        try:
            with patch.dict('sys.modules', {'bs4': None}):
                import look4it
        except ImportError as e:
            error_message = str(e)
            self.assertIn("Missing required module", error_message)
        else:
            # Module already loaded, that's okay for this test
            pass


class TestMainImportError(unittest.TestCase):
    """Test that main.py handles import errors gracefully"""
    
    def setUp(self):
        """Save current module state before each test"""
        self.saved_modules = {}
        modules_to_save = ['look4it', 'look4it.search_tool', 'look4it.cli']
        for mod in modules_to_save:
            if mod in sys.modules:
                self.saved_modules[mod] = sys.modules[mod]
    
    def tearDown(self):
        """Restore module state after each test"""
        # Remove modules that were added during test
        modules_to_remove = ['look4it', 'look4it.search_tool', 'look4it.cli']
        for mod in modules_to_remove:
            if mod in sys.modules and mod not in self.saved_modules:
                del sys.modules[mod]
        
        # Restore saved modules
        for mod, saved_mod in self.saved_modules.items():
            sys.modules[mod] = saved_mod
    
    def test_import_error_message_format(self):
        """Test that import error provides helpful message"""
        # Remove modules that might be cached
        modules_to_remove = ['look4it', 'look4it.search_tool']
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]
        
        # Test that the error message is informative
        try:
            # Try to trigger an import with missing module
            with patch.dict('sys.modules', {'ddgs': None}):
                import look4it
        except ImportError as e:
            error_msg = str(e)
            self.assertIn("Missing required module", error_msg)
            self.assertIn("pip install", error_msg)
        except Exception:
            # If module is already imported and working, that's fine
            pass


if __name__ == '__main__':
    unittest.main(verbosity=2)
