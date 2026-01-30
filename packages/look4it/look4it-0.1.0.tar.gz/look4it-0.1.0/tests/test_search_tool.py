"""
Unit tests for Look4It search tool
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from look4it import Look4It


class TestLook4It(unittest.TestCase):
    """Test cases for Look4It class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.searcher = Look4It(max_results=3, timeout=5)
        
        # Sample mock data
        self.mock_search_results = [
            {
                'title': 'Test Result 1',
                'href': 'https://example.com/page1',
                'body': 'This is a test snippet for result 1'
            },
            {
                'title': 'Test Result 2',
                'href': 'https://example.com/page2',
                'body': 'This is a test snippet for result 2'
            }
        ]
        
        self.mock_html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <nav>Navigation</nav>
                <header>Header</header>
                <main>
                    <h1>Main Content</h1>
                    <p>This is the main content of the page.</p>
                    <p>It has multiple paragraphs.</p>
                </main>
                <script>console.log('test');</script>
                <style>.test { color: red; }</style>
                <footer>Footer</footer>
            </body>
        </html>
        """
    
    def test_initialization(self):
        """Test Look4It initialization"""
        searcher = Look4It(max_results=10, timeout=15)
        self.assertEqual(searcher.max_results, 10)
        self.assertEqual(searcher.timeout, 15)
        self.assertIsNotNone(searcher.headers)
        self.assertIn('User-Agent', searcher.headers)
    
    def test_initialization_defaults(self):
        """Test Look4It initialization with defaults"""
        searcher = Look4It()
        self.assertEqual(searcher.max_results, 5)
        self.assertEqual(searcher.timeout, 10)
    
    @patch('look4it.search_tool.DDGS')
    def test_search_without_content(self, mock_ddgs_class):
        """Test search without content extraction"""
        # Setup mock
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=False)
        mock_ddgs.text = Mock(return_value=self.mock_search_results)
        mock_ddgs_class.return_value = mock_ddgs
        
        # Execute
        results = self.searcher.search("test query", include_content=False)
        
        # Verify
        self.assertEqual(results['query'], "test query")
        self.assertEqual(results['result_count'], 2)
        self.assertEqual(len(results['results']), 2)
        
        # Check first result
        first_result = results['results'][0]
        self.assertEqual(first_result['title'], 'Test Result 1')
        self.assertEqual(first_result['url'], 'https://example.com/page1')
        self.assertEqual(first_result['snippet'], 'This is a test snippet for result 1')
        self.assertNotIn('content', first_result)
        self.assertNotIn('word_count', first_result)
    
    @patch('look4it.search_tool.DDGS')
    @patch('look4it.search_tool.requests.get')
    def test_search_with_content(self, mock_get, mock_ddgs_class):
        """Test search with content extraction"""
        # Setup DDGS mock
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=False)
        mock_ddgs.text = Mock(return_value=self.mock_search_results)
        mock_ddgs_class.return_value = mock_ddgs
        
        # Setup requests mock
        mock_response = Mock()
        mock_response.content = self.mock_html.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Execute
        results = self.searcher.search("test query", include_content=True)
        
        # Verify
        self.assertEqual(results['query'], "test query")
        self.assertEqual(results['result_count'], 2)
        self.assertEqual(len(results['results']), 2)
        
        # Check content was extracted
        first_result = results['results'][0]
        self.assertIn('content', first_result)
        self.assertIn('word_count', first_result)
        self.assertGreater(first_result['word_count'], 0)
    
    @patch('look4it.search_tool.DDGS')
    def test_search_with_exception(self, mock_ddgs_class):
        """Test search handles exceptions gracefully"""
        # Setup mock to raise exception
        mock_ddgs_class.side_effect = Exception("Network error")
        
        # Execute
        results = self.searcher.search("test query")
        
        # Verify error handling
        self.assertEqual(results['query'], "test query")
        self.assertEqual(results['result_count'], 0)
        self.assertEqual(len(results['results']), 0)
        self.assertIn('error', results)
        self.assertEqual(results['error'], "Network error")
    
    @patch('look4it.search_tool.requests.get')
    def test_extract_content_success(self, mock_get):
        """Test successful content extraction"""
        # Setup mock
        mock_response = Mock()
        mock_response.content = self.mock_html.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Execute
        content = self.searcher._extract_content("https://example.com")
        
        # Verify
        self.assertIsInstance(content, str)
        self.assertIn("Main Content", content)
        self.assertIn("main content of the page", content)
        # Should not contain script or style content
        self.assertNotIn("console.log", content)
        self.assertNotIn("color: red", content)
        # Should not contain nav/header/footer
        self.assertNotIn("Navigation", content)
    
    @patch('look4it.search_tool.requests.get')
    def test_extract_content_failure(self, mock_get):
        """Test content extraction handles failures"""
        # Setup mock to raise exception
        mock_get.side_effect = Exception("Connection error")
        
        # Execute
        content = self.searcher._extract_content("https://example.com")
        
        # Verify error message
        self.assertIsInstance(content, str)
        self.assertIn("Error extracting content", content)
        self.assertIn("Connection error", content)
    
    @patch('look4it.search_tool.requests.get')
    def test_extract_content_truncation(self, mock_get):
        """Test content is truncated when too long"""
        # Create very long HTML content
        long_html = f"<html><body><p>{'word ' * 10000}</p></body></html>"
        mock_response = Mock()
        mock_response.content = long_html.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Execute
        content = self.searcher._extract_content("https://example.com")
        
        # Verify truncation
        self.assertLessEqual(len(content), 5003)  # 5000 + "..."
        self.assertTrue(content.endswith("..."))
    
    @patch('look4it.search_tool.DDGS')
    def test_search_and_summarize(self, mock_ddgs_class):
        """Test search_and_summarize method"""
        # Setup mock
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=False)
        mock_ddgs.text = Mock(return_value=self.mock_search_results)
        mock_ddgs_class.return_value = mock_ddgs
        
        # Execute
        summary = self.searcher.search_and_summarize("test query")
        
        # Verify
        self.assertIsInstance(summary, str)
        self.assertIn("test query", summary)
        self.assertIn("Found 2 results", summary)
        self.assertIn("Test Result 1", summary)
        self.assertIn("Test Result 2", summary)
        self.assertIn("https://example.com/page1", summary)
    
    @patch('look4it.search_tool.DDGS')
    def test_search_and_summarize_with_error(self, mock_ddgs_class):
        """Test search_and_summarize handles errors"""
        # Setup mock to raise exception
        mock_ddgs_class.side_effect = Exception("Search failed")
        
        # Execute
        summary = self.searcher.search_and_summarize("test query")
        
        # Verify error message
        self.assertIn("Error:", summary)
        self.assertIn("Search failed", summary)
    
    @patch('look4it.search_tool.requests.get')
    def test_get_content(self, mock_get):
        """Test get_content method"""
        # Setup mock
        mock_response = Mock()
        mock_response.content = self.mock_html.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Execute
        result = self.searcher.get_content("https://example.com/test")
        
        # Verify
        self.assertEqual(result['url'], "https://example.com/test")
        self.assertEqual(result['domain'], "example.com")
        self.assertIn('content', result)
        self.assertIn('word_count', result)
        self.assertGreater(result['word_count'], 0)
    
    @patch('look4it.search_tool.DDGS')
    def test_max_results_respected(self, mock_ddgs_class):
        """Test that max_results parameter is respected"""
        # Setup mock with more results than max
        many_results = [
            {'title': f'Result {i}', 'href': f'https://example.com/{i}', 'body': f'Snippet {i}'}
            for i in range(10)
        ]
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=False)
        mock_ddgs.text = Mock(return_value=many_results[:self.searcher.max_results])
        mock_ddgs_class.return_value = mock_ddgs
        
        # Execute
        results = self.searcher.search("test", include_content=False)
        
        # Verify max_results is passed to DDGS
        mock_ddgs.text.assert_called_once_with("test", max_results=3)
    
    def test_headers_contain_user_agent(self):
        """Test that headers contain User-Agent"""
        self.assertIn('User-Agent', self.searcher.headers)
        self.assertTrue(len(self.searcher.headers['User-Agent']) > 0)
    
    @patch('look4it.search_tool.requests.get')
    def test_extract_content_whitespace_cleanup(self, mock_get):
        """Test that whitespace is properly cleaned"""
        messy_html = """
        <html><body>
            <p>Text   with    multiple    spaces</p>
            <p>
                Text
                with
                newlines
            </p>
        </body></html>
        """
        mock_response = Mock()
        mock_response.content = messy_html.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Execute
        content = self.searcher._extract_content("https://example.com")
        
        # Verify no excessive whitespace
        self.assertNotIn("   ", content)
        self.assertNotIn("\n", content)


class TestLook4itIntegration(unittest.TestCase):
    """Integration tests for Look4It"""
    
    @patch('look4it.search_tool.DDGS')
    @patch('look4it.search_tool.requests.get')
    def test_full_search_workflow(self, mock_get, mock_ddgs_class):
        """Test complete search workflow from query to results"""
        # Setup mocks
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=False)
        mock_ddgs.text = Mock(return_value=[
            {
                'title': 'Python Tutorial',
                'href': 'https://example.com/python',
                'body': 'Learn Python programming'
            }
        ])
        mock_ddgs_class.return_value = mock_ddgs
        
        mock_response = Mock()
        mock_response.content = b"<html><body><h1>Python Tutorial</h1><p>Content here</p></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Execute complete workflow
        searcher = Look4It(max_results=5, timeout=10)
        results = searcher.search("Python tutorial", include_content=True)
        
        # Verify complete result structure
        self.assertIn('query', results)
        self.assertIn('results', results)
        self.assertIn('result_count', results)
        self.assertEqual(results['result_count'], 1)
        
        result = results['results'][0]
        self.assertIn('title', result)
        self.assertIn('url', result)
        self.assertIn('snippet', result)
        self.assertIn('content', result)
        self.assertIn('word_count', result)


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestLook4It))
    suite.addTests(loader.loadTestsFromTestCase(TestLook4itIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    result = run_tests()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        exit(1)
