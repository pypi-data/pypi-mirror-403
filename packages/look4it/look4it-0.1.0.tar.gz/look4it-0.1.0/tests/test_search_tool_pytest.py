"""
Pytest-style tests for Look4It
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestLook4ItPytest:
    """Pytest-style test class for Look4It"""
    
    def test_initialization_with_custom_values(self, searcher):
        """Test initialization with custom values"""
        assert searcher.max_results == 3
        assert searcher.timeout == 5
        assert 'User-Agent' in searcher.headers
    
    def test_initialization_defaults(self):
        """Test default initialization"""
        from look4it import Look4It
        searcher = Look4It()
        assert searcher.max_results == 5
        assert searcher.timeout == 10
    
    @patch('look4it.search_tool.DDGS')
    def test_search_returns_correct_structure(self, mock_ddgs_class, searcher, mock_search_results):
        """Test that search returns correct data structure"""
        # Setup mock
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=False)
        mock_ddgs.text = Mock(return_value=mock_search_results)
        mock_ddgs_class.return_value = mock_ddgs
        
        # Execute
        results = searcher.search("test query", include_content=False)
        
        # Assertions
        assert 'query' in results
        assert 'results' in results
        assert 'result_count' in results
        assert results['query'] == "test query"
        assert results['result_count'] == 2
        assert len(results['results']) == 2
    
    @patch('look4it.search_tool.DDGS')
    @patch('look4it.search_tool.requests.get')
    def test_search_with_content_extraction(self, mock_get, mock_ddgs_class, 
                                            searcher, mock_search_results, mock_response):
        """Test search with content extraction enabled"""
        # Setup mocks
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=False)
        mock_ddgs.text = Mock(return_value=mock_search_results)
        mock_ddgs_class.return_value = mock_ddgs
        mock_get.return_value = mock_response
        
        # Execute
        results = searcher.search("test", include_content=True)
        
        # Assertions
        assert results['result_count'] == 2
        for result in results['results']:
            assert 'content' in result
            assert 'word_count' in result
            assert isinstance(result['word_count'], int)
    
    @patch('look4it.search_tool.requests.get')
    def test_extract_content_removes_unwanted_elements(self, mock_get, searcher, mock_response):
        """Test that content extraction removes scripts, styles, nav, etc."""
        mock_get.return_value = mock_response
        
        content = searcher._extract_content("https://example.com")
        
        assert "Main Content" in content
        assert "console.log" not in content
        assert "color: red" not in content
        assert "Navigation" not in content
        assert "Footer" not in content
    
    @patch('look4it.search_tool.requests.get')
    def test_extract_content_handles_exceptions(self, mock_get, searcher):
        """Test content extraction error handling"""
        mock_get.side_effect = Exception("Network error")
        
        content = searcher._extract_content("https://example.com")
        
        assert "Error extracting content" in content
        assert "Network error" in content
    
    @patch('look4it.search_tool.DDGS')
    def test_search_handles_exceptions(self, mock_ddgs_class, searcher):
        """Test search error handling"""
        mock_ddgs_class.side_effect = Exception("Search failed")
        
        results = searcher.search("test")
        
        assert results['result_count'] == 0
        assert 'error' in results
        assert "Search failed" in results['error']
    
    @patch('look4it.search_tool.requests.get')
    def test_get_content_returns_complete_structure(self, mock_get, searcher, mock_response):
        """Test get_content method returns all required fields"""
        mock_get.return_value = mock_response
        
        result = searcher.get_content("https://example.com/test")
        
        assert result['url'] == "https://example.com/test"
        assert result['domain'] == "example.com"
        assert 'content' in result
        assert 'word_count' in result
        assert result['word_count'] > 0
    
    @patch('look4it.search_tool.DDGS')
    def test_search_and_summarize_format(self, mock_ddgs_class, searcher, mock_search_results):
        """Test search_and_summarize output format"""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=False)
        mock_ddgs.text = Mock(return_value=mock_search_results)
        mock_ddgs_class.return_value = mock_ddgs
        
        summary = searcher.search_and_summarize("test query")
        
        assert "test query" in summary
        assert "Found 2 results" in summary
        assert "Test Result 1" in summary
        assert "https://example.com/page1" in summary
    
    @patch('look4it.search_tool.requests.get')
    def test_content_truncation(self, mock_get, searcher):
        """Test that long content is truncated"""
        long_html = f"<html><body><p>{'word ' * 10000}</p></body></html>"
        mock_response = Mock()
        mock_response.content = long_html.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        content = searcher._extract_content("https://example.com")
        
        assert len(content) <= 5003  # 5000 + "..."
        assert content.endswith("...")
    
    def test_user_agent_in_headers(self, searcher):
        """Test that User-Agent header is present"""
        assert 'User-Agent' in searcher.headers
        assert len(searcher.headers['User-Agent']) > 0
        assert 'Mozilla' in searcher.headers['User-Agent']


@pytest.mark.parametrize("max_results,timeout", [
    (1, 5),
    (5, 10),
    (10, 15),
    (100, 30),
])
def test_initialization_with_various_parameters(max_results, timeout):
    """Test initialization with various parameter combinations"""
    from look4it import Look4It
    searcher = Look4It(max_results=max_results, timeout=timeout)
    assert searcher.max_results == max_results
    assert searcher.timeout == timeout


@pytest.mark.parametrize("query", [
    "Python programming",
    "machine learning basics",
    "web development tutorial",
    "data science tools",
])
@patch('look4it.search_tool.DDGS')
def test_search_with_various_queries(mock_ddgs_class, query):
    """Test search with various query strings"""
    from look4it import Look4It
    
    mock_ddgs = MagicMock()
    mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
    mock_ddgs.__exit__ = Mock(return_value=False)
    mock_ddgs.text = Mock(return_value=[])
    mock_ddgs_class.return_value = mock_ddgs
    
    searcher = Look4It()
    results = searcher.search(query, include_content=False)
    
    assert results['query'] == query
    assert 'results' in results
    assert 'result_count' in results
