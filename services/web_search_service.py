"""
Web Search Service V2 - Enhanced with multiple search engines
"""
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from services.ollama_service import OllamaService
from config import Config


class WebSearchService:
    def __init__(self):
        self.max_results = Config.MAX_SEARCH_RESULTS
        self.ollama_service = OllamaService()
        self.engines = {
            'duckduckgo': self._search_duckduckgo,
            'google': self._search_google,
            'bing': self._search_bing
        }

    def search(
            self,
            query: str,
            max_results: int = None,
            engine: str = 'duckduckgo'
    ) -> Dict:
        """
        Search the web using specified engine

        Args:
            query: Search query
            max_results: Maximum number of results
            engine: Search engine to use

        Returns:
            Dictionary with search results
        """
        max_results = max_results or self.max_results

        search_func = self.engines.get(engine, self._search_duckduckgo)
        return search_func(query, max_results)

    def _search_duckduckgo(self, query: str, max_results: int) -> Dict:
        """
        Search the web using DuckDuckGo HTML

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            Dictionary with search results
        """
        max_results = max_results or self.max_results

        try:
            # Use DuckDuckGo HTML search (no API key required)
            url = "https://html.duckduckgo.com/html/"
            params = {'q': query}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.post(url, data=params, headers=headers, timeout=10)

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Search failed with status {response.status_code}',
                    'results': []
                }

            # Parse HTML results
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # Find result divs
            result_divs = soup.find_all('div', class_='result')

            for div in result_divs[:max_results]:
                try:
                    # Extract title and link
                    title_tag = div.find('a', class_='result__a')
                    if not title_tag:
                        continue

                    title = title_tag.get_text(strip=True)
                    link = title_tag.get('href', '')

                    # Extract snippet
                    snippet_tag = div.find('a', class_='result__snippet')
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ''

                    if title and link:
                        results.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet
                        })
                except Exception as e:
                    continue

            return {
                'success': True,
                'query': query,
                'results': results,
                'count': len(results)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }

    def search_and_summarize(
            self,
            query: str,
            max_results: int = None,
            model: str = "gemma:2b"
    ) -> Dict:
        """
        Search the web and generate a summary using Ollama

        Args:
            query: Search query
            max_results: Maximum results to fetch
            model: Ollama model for summarization

        Returns:
            Dictionary with results and summary
        """
        # Perform search
        search_result = self.search(query, max_results)

        if not search_result.get('success'):
            return search_result

        results = search_result.get('results', [])

        if not results:
            return {
                'success': True,
                'query': query,
                'results': [],
                'summary': 'No results found for your query.',
                'sources': []
            }

        # Prepare content for summarization
        content = f"Search query: {query}\n\nSearch Results:\n\n"
        sources = []

        for i, result in enumerate(results, 1):
            content += f"{i}. {result['title']}\n"
            content += f"   {result['snippet']}\n"
            content += f"   Source: {result['link']}\n\n"
            sources.append(result['link'])

        # Generate summary using Ollama
        summary = self._generate_summary(content, query, model)

        return {
            'success': True,
            'query': query,
            'results': results,
            'summary': summary,
            'sources': sources
        }

    def _generate_summary(self, content: str, query: str, model: str) -> str:
        """
        Generate summary of search results using Ollama

        Args:
            content: Search results content
            query: Original query
            model: Model to use

        Returns:
            Summary text
        """
        system_message = """You are a helpful assistant that summarizes web search results.
Provide a clear, concise summary that answers the user's query based on the search results.
Cite specific sources when making claims."""

        user_message = f"""{content}

Based on these search results, please provide a comprehensive answer to the query: "{query}"

Include:
1. A direct answer to the query
2. Key information from the search results
3. Reference to sources where appropriate"""

        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': user_message}
        ]

        result = self.ollama_service.chat(messages, model=model, temperature=0.5)

        if result.get('success'):
            return result.get('message', 'Unable to generate summary')
        else:
            return f"Summary generation failed: {result.get('error', 'Unknown error')}"

    def fetch_page_content(self, url: str) -> Dict:
        """
        Fetch and extract text content from a web page

        Args:
            url: URL to fetch

        Returns:
            Dictionary with page content
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Failed to fetch page: Status {response.status_code}'
                }

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            # Get title
            title = soup.find('title')
            title_text = title.get_text() if title else url

            return {
                'success': True,
                'url': url,
                'title': title_text,
                'content': text[:5000],  # Limit content length
                'full_length': len(text)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to fetch page: {str(e)}'
            }