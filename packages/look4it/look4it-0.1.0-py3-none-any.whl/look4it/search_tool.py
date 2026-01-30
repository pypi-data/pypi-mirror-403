"""
Look4It - A simple web searching tool similar to Tavily
"""
import json
import re
from typing import List, Dict, Optional
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
    from ddgs import DDGS
except ImportError as e:
    missing_module = str(e).split("'")[1] if "'" in str(e) else "unknown"
    raise ImportError(
        f"\n\n❌ Missing required module: {missing_module}\n\n"
        f"Please install dependencies:\n"
        f"  pip install -e .\n"
        f"  OR\n"
        f"  pip install requests beautifulsoup4 ddgs lxml\n\n"
        f"If using a virtual environment, make sure it's activated.\n"
    ) from e


class Look4It:
    """A simple web search tool that provides structured search results."""
    
    def __init__(self, max_results: int = 5, timeout: int = 10):
        """
        Initialize the Look4It search tool.
        
        Args:
            max_results: Maximum number of search results to return
            timeout: Timeout for HTTP requests in seconds
        """
        self.max_results = max_results
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search(self, query: str, include_content: bool = True) -> Dict:
        """
        Search the web for a query and return structured results.
        
        Args:
            query: The search query string
            include_content: Whether to fetch and extract content from each result
        
        Returns:
            Dictionary containing search results with metadata
        """
        try:
            # Perform search using DuckDuckGo
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=self.max_results))
            
            # Process results
            processed_results = []
            for result in results:
                processed_result = {
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', ''),
                }
                
                # Fetch full content if requested
                if include_content:
                    content = self._extract_content(result.get('href', ''))
                    processed_result['content'] = content
                    processed_result['word_count'] = len(content.split()) if content else 0
                
                processed_results.append(processed_result)
            
            return {
                'query': query,
                'results': processed_results,
                'result_count': len(processed_results)
            }
            
        except Exception as e:
            return {
                'query': query,
                'results': [],
                'result_count': 0,
                'error': str(e)
            }
    
    def _extract_content(self, url: str) -> Optional[str]:
        """
        Extract main content from a webpage.
        
        Args:
            url: The URL to extract content from
        
        Returns:
            Extracted text content or None if extraction fails
        """
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()
            
            # Get text content
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Limit content length
            max_chars = 5000
            if len(text) > max_chars:
                text = text[:max_chars] + '...'
            
            return text
            
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    
    def search_and_summarize(self, query: str) -> str:
        """
        Search and return a formatted summary of results.
        
        Args:
            query: The search query string
        
        Returns:
            Formatted string with search results
        """
        results = self.search(query, include_content=False)
        
        if 'error' in results:
            return f"Error: {results['error']}"
        
        output = [f"Search Results for: {query}\n"]
        output.append(f"Found {results['result_count']} results\n")
        output.append("=" * 80 + "\n")
        
        for i, result in enumerate(results['results'], 1):
            output.append(f"\n{i}. {result['title']}")
            output.append(f"   URL: {result['url']}")
            output.append(f"   {result['snippet']}\n")
        
        return '\n'.join(output)
    
    def get_content(self, url: str) -> Dict:
        """
        Extract content from a specific URL.
        
        Args:
            url: The URL to extract content from
        
        Returns:
            Dictionary with URL, content, and metadata
        """
        content = self._extract_content(url)
        
        return {
            'url': url,
            'content': content,
            'word_count': len(content.split()) if content else 0,
            'domain': urlparse(url).netloc
        }
