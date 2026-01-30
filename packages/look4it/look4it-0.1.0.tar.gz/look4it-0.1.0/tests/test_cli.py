"""
Tests for main.py CLI interface
"""
import unittest
from unittest.mock import patch, Mock, MagicMock
import sys
import os
from io import StringIO

# Add examples directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'examples'))


class TestMainCLI(unittest.TestCase):
    """Test cases for main.py CLI interface"""
    
    @patch('sys.argv', ['main.py'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_no_arguments(self, mock_stdout):
        """Test main with no arguments shows usage"""
        from look4it.cli import main
        
        main()
        output = mock_stdout.getvalue()
        
        self.assertIn("Usage:", output)
        self.assertIn("search_query", output)
    
    @patch('sys.argv', ['main.py', 'test', 'query'])
    @patch('look4it.cli.Look4It')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_with_search_query(self, mock_stdout, mock_open, mock_look4it_class):
        """Test main with search query"""
        # Setup mock
        mock_searcher = Mock()
        mock_searcher.search.return_value = {
            'query': 'test query',
            'result_count': 1,
            'results': [
                {
                    'title': 'Test Result',
                    'url': 'https://example.com',
                    'snippet': 'Test snippet',
                    'word_count': 100
                }
            ]
        }
        mock_look4it_class.return_value = mock_searcher
        
        from look4it.cli import main
        main()
        
        output = mock_stdout.getvalue()
        
        # Verify output
        self.assertIn("Searching for: test query", output)
        self.assertIn("Found 1 results", output)
        self.assertIn("Test Result", output)
        self.assertIn("https://example.com", output)
    
    @patch('sys.argv', ['main.py', 'error', 'query'])
    @patch('look4it.cli.Look4It')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_with_error(self, mock_stdout, mock_look4it_class):
        """Test main handles search errors"""
        # Setup mock to return error
        mock_searcher = Mock()
        mock_searcher.search.return_value = {
            'query': 'error query',
            'error': 'Search failed',
            'result_count': 0,
            'results': []
        }
        mock_look4it_class.return_value = mock_searcher
        
        from look4it.cli import main
        main()
        
        output = mock_stdout.getvalue()
        
        self.assertIn("Error:", output)
        self.assertIn("Search failed", output)


class TestExampleScript(unittest.TestCase):
    """Test cases for example.py"""
    
    @patch('example.Look4It')
    @patch('sys.stdout', new_callable=StringIO)
    def test_example_basic_search(self, mock_stdout, mock_look4it_class):
        """Test example basic search function"""
        from example import example_basic_search
        
        # Setup mock
        mock_searcher = Mock()
        mock_searcher.search.return_value = {
            'query': 'test',
            'result_count': 0,
            'results': []
        }
        mock_look4it_class.return_value = mock_searcher
        
        example_basic_search()
        
        output = mock_stdout.getvalue()
        self.assertIn("Example 1", output)
    
    @patch('example.Look4It')
    @patch('sys.stdout', new_callable=StringIO)
    def test_example_search_with_content(self, mock_stdout, mock_look4it_class):
        """Test example search with content"""
        from example import example_search_with_content
        
        # Setup mock
        mock_searcher = Mock()
        mock_searcher.search.return_value = {
            'query': 'test',
            'result_count': 1,
            'results': [
                {
                    'title': 'Test',
                    'url': 'https://example.com',
                    'word_count': 100,
                    'content': 'Test content'
                }
            ]
        }
        mock_look4it_class.return_value = mock_searcher
        
        example_search_with_content()
        
        output = mock_stdout.getvalue()
        self.assertIn("Example 2", output)
    
    @patch('example.Look4It')
    @patch('sys.stdout', new_callable=StringIO)
    def test_example_formatted_summary(self, mock_stdout, mock_look4it_class):
        """Test example formatted summary"""
        from example import example_formatted_summary
        
        # Setup mock
        mock_searcher = Mock()
        mock_searcher.search_and_summarize.return_value = "Test summary"
        mock_look4it_class.return_value = mock_searcher
        
        example_formatted_summary()
        
        output = mock_stdout.getvalue()
        self.assertIn("Example 3", output)
    
    @patch('example.Look4It')
    @patch('sys.stdout', new_callable=StringIO)
    def test_example_extract_url_content(self, mock_stdout, mock_look4it_class):
        """Test example URL content extraction"""
        from example import example_extract_url_content
        
        # Setup mock
        mock_searcher = Mock()
        mock_searcher.get_content.return_value = {
            'url': 'https://www.python.org',
            'domain': 'www.python.org',
            'word_count': 100,
            'content': 'Test content'
        }
        mock_look4it_class.return_value = mock_searcher
        
        example_extract_url_content()
        
        output = mock_stdout.getvalue()
        self.assertIn("Example 4", output)


class TestQuickStart(unittest.TestCase):
    """Test cases for quick_start.py"""
    
    @patch('quick_start.Look4It')
    @patch('sys.stdout', new_callable=StringIO)
    def test_quick_demo(self, mock_stdout, mock_look4it_class):
        """Test quick_start demo function"""
        from quick_start import quick_demo
        
        # Setup mock
        mock_searcher = Mock()
        mock_searcher.search.return_value = {
            'query': 'test',
            'result_count': 1,
            'results': [
                {
                    'title': 'Test',
                    'url': 'https://example.com',
                    'snippet': 'Test snippet',
                    'word_count': 100,
                    'content': 'Test content'
                }
            ]
        }
        mock_searcher.search_and_summarize.return_value = "Test summary"
        mock_look4it_class.return_value = mock_searcher
        
        quick_demo()
        
        output = mock_stdout.getvalue()
        self.assertIn("Look4It Quick Demo", output)
        self.assertIn("Demo complete", output)


if __name__ == '__main__':
    unittest.main(verbosity=2)
