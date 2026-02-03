"""
Tag Service - AEM Tag Management
Handles creating, editing, and managing tags
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Optional
from config import Config


class TagService:
    def __init__(self):
        self.host = Config.AEM_HOST
        self.auth = HTTPBasicAuth(Config.AEM_USERNAME, Config.AEM_PASSWORD)
        self.timeout = Config.AEM_TIMEOUT

    def list_tags(
            self,
            namespace: str = "default",
            path: str = "/etc/tags"
    ) -> Dict:
        """
        List tags in a namespace

        Args:
            namespace: Tag namespace
            path: Tag path

        Returns:
            List of tags
        """
        try:
            url = f"{self.host}{path}/{namespace}.json"

            response = requests.get(url, auth=self.auth, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                tags = self._parse_tags(data)

                return {
                    'success': True,
                    'tags': tags,
                    'total': len(tags)
                }

            return {
                'success': False,
                'error': 'Failed to retrieve tags',
                'tags': []
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tags': []
            }

    def _parse_tags(self, data: Dict, parent_path: str = "") -> List[Dict]:
        """Recursively parse tag structure"""
        tags = []

        for key, value in data.items():
            if isinstance(value, dict) and not key.startswith('jcr:'):
                tag_id = value.get('jcr:title', key)
                tag_path = f"{parent_path}/{key}" if parent_path else key

                tag_info = {
                    'id': key,
                    'title': tag_id,
                    'path': tag_path,
                    'description': value.get('jcr:description', '')
                }

                tags.append(tag_info)

                # Recursively get child tags
                child_tags = self._parse_tags(value, tag_path)
                tags.extend(child_tags)

        return tags

    def create_tag(
            self,
            namespace: str,
            tag_id: str,
            title: str,
            description: Optional[str] = None
    ) -> Dict:
        """
        Create a new tag

        Args:
            namespace: Tag namespace
            tag_id: Tag ID
            title: Tag title
            description: Tag description

        Returns:
            Created tag info
        """
        try:
            url = f"{self.host}/etc/tags/{namespace}"

            payload = {
                './jcr:primaryType': 'cq:Tag',
                './jcr:title': title,
                ':name': tag_id,
                '_charset_': 'utf-8'
            }

            if description:
                payload['./jcr:description'] = description

            response = requests.post(
                url,
                auth=self.auth,
                data=payload,
                timeout=self.timeout
            )

            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'message': f'Tag {tag_id} created',
                    'tag_id': tag_id,
                    'title': title
                }

            return {
                'success': False,
                'error': 'Failed to create tag'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def update_tag(
            self,
            tag_path: str,
            title: Optional[str] = None,
            description: Optional[str] = None
    ) -> Dict:
        """
        Update tag properties

        Args:
            tag_path: Full tag path
            title: New title
            description: New description

        Returns:
            Update result
        """
        try:
            url = f"{self.host}{tag_path}"

            payload = {'_charset_': 'utf-8'}

            if title:
                payload['./jcr:title'] = title
            if description:
                payload['./jcr:description'] = description

            response = requests.post(
                url,
                auth=self.auth,
                data=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Tag updated successfully'
                }

            return {
                'success': False,
                'error': 'Failed to update tag'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def delete_tag(self, tag_path: str) -> Dict:
        """
        Delete a tag

        Args:
            tag_path: Full tag path

        Returns:
            Deletion result
        """
        try:
            url = f"{self.host}{tag_path}"

            payload = {
                ':operation': 'delete',
                '_charset_': 'utf-8'
            }

            response = requests.post(
                url,
                auth=self.auth,
                data=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Tag deleted successfully'
                }

            return {
                'success': False,
                'error': 'Failed to delete tag'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def search_tags(self, keyword: str) -> Dict:
        """
        Search for tags by keyword

        Args:
            keyword: Search term

        Returns:
            Matching tags
        """
        try:
            query_params = {
                'path': '/etc/tags',
                'type': 'cq:Tag',
                'fulltext': keyword,
                'p.limit': '50'
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
                        'title': hit.get('jcr:title', ''),
                        'description': hit.get('jcr:description', '')
                    })

                return {
                    'success': True,
                    'results': results,
                    'total': len(results)
                }

            return {
                'success': False,
                'error': 'Search failed',
                'results': []
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': []
            }