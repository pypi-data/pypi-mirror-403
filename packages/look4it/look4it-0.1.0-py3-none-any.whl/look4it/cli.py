"""
Look4It - CLI interface
"""
import sys
import json
from look4it import Look4It


def main():
    """Main entry point for the CLI"""
    if len(sys.argv) < 2:
        print("Usage: look4it <search_query>")
        print("       python -m look4it <search_query>")
        print("Example: look4it 'What is Python?'")
        return 1
    
    # Get query from command line arguments
    query = ' '.join(sys.argv[1:])
    
    # Initialize search tool
    print(f"🔍 Searching for: {query}\n")
    searcher = Look4It(max_results=5)
    
    # Perform search
    results = searcher.search(query, include_content=True)
    
    # Display results
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return 1
    
    print(f"✅ Found {results['result_count']} results\n")
    print("=" * 80)
    
    for i, result in enumerate(results['results'], 1):
        print(f"\n{i}. {result['title']}")
        print(f"   📎 URL: {result['url']}")
        print(f"   📝 Snippet: {result['snippet']}")
        if 'word_count' in result:
            print(f"   📊 Content length: {result['word_count']} words")
        print()
    
    # Optionally save to JSON file
    with open('search_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n💾 Full results saved to search_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
