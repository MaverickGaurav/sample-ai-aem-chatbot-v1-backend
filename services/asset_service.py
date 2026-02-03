"""
AEM Asset Service - DAM Asset Operations
Handles browsing, searching, and managing AEM DAM assets
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Optional
from config import Config
import json


class AssetService:
    def __init__(self):
        self.host = Config.AEM_HOST
        self.username = Config.AEM_USERNAME
        self.password = Config.AEM_PASSWORD
        self.timeout = Config.AEM_TIMEOUT
        self.auth = HTTPBasicAuth(self.username, self.password)

    def browse_assets(
            self,
            path: str = "/content/dam",
            depth: int = 1,
            limit: int = 100
    ) -> Dict:
        """
        Browse assets in DAM

        Args:
            path: DAM path to browse
            depth: Folder depth
            limit: Maximum assets to return

        Returns:
            Dictionary with asset list
        """
        try:
            # Use AEM QueryBuilder to find assets
            query_params = {
                'path': path,
                'type': 'dam:Asset',
                'p.limit': str(limit),
                'p.hits': 'full',
                'orderby': '@jcr:content/jcr:lastModified',
                'orderby.sort': 'desc'
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

                assets = []
                for hit in hits:
                    asset_path = hit.get('path', '')

                    # Check depth
                    path_depth = asset_path.count('/') - path.count('/')
                    if path_depth > depth:
                        continue

                    jcr_content = hit.get('jcr:content', {})
                    metadata = jcr_content.get('metadata', {})

                    asset_info = {
                        'path': asset_path,
                        'name': asset_path.split('/')[-1],
                        'title': metadata.get('dc:title', asset_path.split('/')[-1]),
                        'format': metadata.get('dc:format', ''),
                        'size': jcr_content.get('jcr:data', {}).get('jcr:size', 0),
                        'modified': metadata.get('dam:lastModified', ''),
                        'type': self._get_asset_type(metadata.get('dc:format', '')),
                        'thumbnail': f"{asset_path}/_jcr_content/renditions/cq5dam.thumbnail.319.319.png"
                    }
                    assets.append(asset_info)

                return {
                    'success': True,
                    'assets': assets,
                    'total': len(assets),
                    'path': path
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to browse assets: {response.status_code}',
                    'assets': []
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'assets': []
            }

    def search_assets(
            self,
            keyword: str,
            path: str = "/content/dam",
            file_type: Optional[str] = None
    ) -> Dict:
        """
        Search for assets by keyword

        Args:
            keyword: Search term
            path: DAM path to search within
            file_type: Filter by file type (image, video, document)

        Returns:
            Search results
        """
        try:
            query_params = {
                'path': path,
                'type': 'dam:Asset',
                'fulltext': keyword,
                'p.limit': '50',
                'orderby': '@jcr:score',
                'orderby.sort': 'desc'
            }

            # Add file type filter if specified
            if file_type:
                mime_types = {
                    'image': 'image/%',
                    'video': 'video/%',
                    'document': 'application/%'
                }
                if file_type in mime_types:
                    query_params['property'] = 'jcr:content/metadata/dc:format'
                    query_params['property.value'] = mime_types[file_type]
                    query_params['property.operation'] = 'like'

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
                    metadata = hit.get('jcr:content', {}).get('metadata', {})
                    results.append({
                        'path': hit.get('path', ''),
                        'title': metadata.get('dc:title', ''),
                        'format': metadata.get('dc:format', ''),
                        'score': hit.get('jcr:score', 0)
                    })

                return {
                    'success': True,
                    'results': results,
                    'total': len(results)
                }

            return {'success': False, 'error': 'Search failed', 'results': []}

        except Exception as e:
            return {'success': False, 'error': str(e), 'results': []}

    def get_asset_info(self, asset_path: str) -> Dict:
        """
        Get detailed asset information

        Args:
            asset_path: Path to the asset

        Returns:
            Asset details
        """
        try:
            url = f"{self.host}{asset_path}/_jcr_content/metadata.json"

            response = requests.get(url, auth=self.auth, timeout=self.timeout)

            if response.status_code == 200:
                metadata = response.json()

                return {
                    'success': True,
                    'path': asset_path,
                    'metadata': metadata,
                    'preview': f"{asset_path}/_jcr_content/renditions/cq5dam.web.1280.1280.png"
                }

            return {'success': False, 'error': 'Asset not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_renditions(self, asset_path: str) -> Dict:
        """
        Get available renditions for an asset

        Args:
            asset_path: Asset path

        Returns:
            List of renditions
        """
        try:
            url = f"{self.host}{asset_path}/_jcr_content/renditions.json"

            response = requests.get(url, auth=self.auth, timeout=self.timeout)

            if response.status_code == 200:
                renditions_data = response.json()

                renditions = []
                for key, value in renditions_data.items():
                    if isinstance(value, dict):
                        renditions.append({
                            'name': key,
                            'path': f"{asset_path}/_jcr_content/renditions/{key}",
                            'size': value.get('jcr:data', {}).get('jcr:size', 0)
                        })

                return {
                    'success': True,
                    'renditions': renditions
                }

            return {'success': False, 'error': 'No renditions found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_asset_type(self, mime_type: str) -> str:
        """Determine asset type from MIME type"""
        if not mime_type:
            return 'unknown'

        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('application/pdf'):
            return 'document'
        elif mime_type.startswith('application/'):
            return 'document'
        else:
            return 'file'

    def check_health(self) -> bool:
        """Check if DAM is accessible"""
        try:
            response = requests.get(
                f"{self.host}/content/dam.json",
                auth=self.auth,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False