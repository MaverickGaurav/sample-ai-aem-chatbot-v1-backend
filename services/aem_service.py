"""
AEM Service - Handles all interactions with AEM
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from config import Config
import json


class AEMService:
    def __init__(self):
        self.host = Config.AEM_HOST
        self.username = Config.AEM_USERNAME
        self.password = Config.AEM_PASSWORD
        self.timeout = Config.AEM_TIMEOUT
        self.auth = HTTPBasicAuth(self.username, self.password)

    def query_pages(
            self,
            path: str = "/content",
            depth: int = 3,
            include_templates: Optional[List[str]] = None,
            exclude_templates: Optional[List[str]] = None
    ) -> Dict:
        """
        Query AEM pages under a given path using QueryBuilder API

        Args:
            path: Root path to search
            depth: Search depth
            include_templates: Templates to include
            exclude_templates: Templates to exclude

        Returns:
            Dictionary with page information
        """
        try:
            # Using AEM QueryBuilder API
            query_params = {
                'path': path,
                'type': 'cq:Page',
                'p.limit': '-1',
                'p.hits': 'full',
                '1_property': 'jcr:content/jcr:title',
                '1_property.operation': 'exists'
            }

            # Add depth
            if depth:
                query_params['p.guessTotal'] = 'true'

            url = f"{self.host}/bin/querybuilder.json"

            response = requests.get(
                url,
                params=query_params,
                auth=self.auth,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )

            if response.status_code == 200:
                data = response.json()
                hits = data.get('hits', [])

                pages = []
                for hit in hits:
                    page_path = hit.get('jcr:path', '')

                    # Filter by depth
                    path_depth = page_path.count('/') - path.count('/')
                    if path_depth > depth:
                        continue

                    # Get page properties
                    jcr_content = hit.get('jcr:content', {})
                    template = jcr_content.get('cq:template', '')

                    # Apply template filters
                    if include_templates and template not in include_templates:
                        continue
                    if exclude_templates and template in exclude_templates:
                        continue

                    page_info = {
                        'path': page_path,
                        'title': jcr_content.get('jcr:title', page_path.split('/')[-1]),
                        'last_modified': jcr_content.get('cq:lastModified', ''),
                        'template': template,
                        'has_content': True
                    }
                    pages.append(page_info)

                return {
                    'success': True,
                    'pages': pages,
                    'total_count': len(pages),
                    'query_path': path
                }
            else:
                return {
                    'success': False,
                    'error': f'AEM returned status code {response.status_code}',
                    'pages': [],
                    'total_count': 0
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Failed to connect to AEM: {str(e)}',
                'pages': [],
                'total_count': 0
            }

    def get_page_content(self, page_path: str) -> Dict:
        """
        Retrieve HTML content of an AEM page

        Args:
            page_path: Path to the AEM page

        Returns:
            Dictionary with page content
        """
        try:
            # Request page with .html extension
            url = f"{self.host}{page_path}.html"

            response = requests.get(
                url,
                auth=self.auth,
                timeout=self.timeout,
                headers={'Accept': 'text/html'}
            )

            if response.status_code == 200:
                html_content = response.text

                # Parse HTML to extract useful information
                soup = BeautifulSoup(html_content, 'html.parser')

                # Extract title
                title = soup.find('title')
                title_text = title.get_text() if title else page_path.split('/')[-1]

                # Extract meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                description = meta_desc.get('content', '') if meta_desc else ''

                return {
                    'success': True,
                    'path': page_path,
                    'title': title_text,
                    'description': description,
                    'html': html_content,
                    'content_length': len(html_content)
                }
            else:
                return {
                    'success': False,
                    'error': f'Page returned status code {response.status_code}',
                    'html': ''
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Failed to retrieve page: {str(e)}',
                'html': ''
            }

    def get_page_properties(self, page_path: str) -> Dict:
        """
        Get page properties via AEM JSON export

        Args:
            page_path: Path to the AEM page

        Returns:
            Dictionary with page properties
        """
        try:
            # Use infinity.json for full page data
            url = f"{self.host}{page_path}/jcr:content.json"

            response = requests.get(
                url,
                auth=self.auth,
                timeout=self.timeout
            )

            if response.status_code == 200:
                properties = response.json()
                return {
                    'success': True,
                    'properties': properties
                }
            else:
                return {
                    'success': False,
                    'error': f'Properties request returned {response.status_code}'
                }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Failed to get properties: {str(e)}'
            }

    def check_page_exists(self, page_path: str) -> bool:
        """
        Check if a page exists in AEM

        Args:
            page_path: Path to check

        Returns:
            True if page exists
        """
        try:
            url = f"{self.host}{page_path}.html"
            response = requests.head(
                url,
                auth=self.auth,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False

    def get_component_structure(self, page_path: str) -> Dict:
        """
        Extract AEM component structure from page

        Args:
            page_path: Path to the page

        Returns:
            Component structure information
        """
        content_result = self.get_page_content(page_path)

        if not content_result.get('success'):
            return {
                'success': False,
                'error': content_result.get('error'),
                'components': []
            }

        html = content_result.get('html', '')
        soup = BeautifulSoup(html, 'html.parser')

        # Find AEM components (elements with data-cq-* attributes)
        components = []
        for elem in soup.find_all(attrs={'data-cq-component': True}):
            component_info = {
                'type': elem.get('data-cq-component', 'unknown'),
                'path': elem.get('data-cq-path', ''),
                'tag': elem.name
            }
            components.append(component_info)

        return {
            'success': True,
            'components': components,
            'total_components': len(components)
        }

    def check_health(self) -> bool:
        """
        Check if AEM is accessible

        Returns:
            True if AEM is healthy
        """
        try:
            response = requests.get(
                f"{self.host}/libs/granite/core/content/login.html",
                timeout=5
            )
            return response.status_code in [200, 401, 403]  # 401/403 means server is up but needs auth
        except:
            return False

    def search_content(self, keyword: str, path: str = "/content") -> List[Dict]:
        """
        Search for content in AEM pages

        Args:
            keyword: Search keyword
            path: Path to search within

        Returns:
            List of matching pages
        """
        try:
            query_params = {
                'path': path,
                'type': 'cq:Page',
                'fulltext': keyword,
                'p.limit': '20'
            }

            url = f"{self.host}/bin/querybuilder.json"

            response = requests.get(
                url,
                params=query_params,
                auth=self.auth,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                hits = data.get('hits', [])

                results = []
                for hit in hits:
                    results.append({
                        'path': hit.get('path', ''),
                        'title': hit.get('jcr:content', {}).get('jcr:title', ''),
                        'excerpt': hit.get('excerpt', '')
                    })

                return results
            return []
        except:
            return []