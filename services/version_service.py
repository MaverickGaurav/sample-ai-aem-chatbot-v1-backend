"""
Version Service - AEM Page Version Management
Handles version history and comparison
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Optional
from config import Config
from datetime import datetime


class VersionService:
    def __init__(self):
        self.host = Config.AEM_HOST
        self.auth = HTTPBasicAuth(Config.AEM_USERNAME, Config.AEM_PASSWORD)
        self.timeout = Config.AEM_TIMEOUT

    def get_versions(self, page_path: str) -> Dict:
        """
        Get version history for a page

        Args:
            page_path: Path to the page

        Returns:
            List of versions
        """
        try:
            # Get version storage
            url = f"{self.host}{page_path}.2.json"

            response = requests.get(url, auth=self.auth, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                jcr_content = data.get('jcr:content', {})

                versions = []

                # Look for version storage
                version_storage = jcr_content.get('versionStorage', {})

                for version_name, version_data in version_storage.items():
                    if isinstance(version_data, dict):
                        versions.append({
                            'name': version_name,
                            'created': version_data.get('jcr:created', ''),
                            'created_by': version_data.get('jcr:createdBy', ''),
                            'label': version_data.get('jcr:versionLabels', [])
                        })

                # Sort by creation date
                versions.sort(key=lambda x: x['created'], reverse=True)

                return {
                    'success': True,
                    'versions': versions,
                    'total': len(versions)
                }

            return {
                'success': False,
                'error': 'Failed to retrieve versions',
                'versions': []
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'versions': []
            }

    def get_version_content(
            self,
            page_path: str,
            version_name: str
    ) -> Dict:
        """
        Get content of a specific version

        Args:
            page_path: Page path
            version_name: Version identifier

        Returns:
            Version content
        """
        try:
            # Construct version URL
            url = f"{self.host}{page_path}.html?wcmmode=disabled&version={version_name}"

            response = requests.get(url, auth=self.auth, timeout=self.timeout)

            if response.status_code == 200:
                return {
                    'success': True,
                    'content': response.text,
                    'version': version_name
                }

            return {
                'success': False,
                'error': f'Version {version_name} not found'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def create_version(
            self,
            page_path: str,
            label: Optional[str] = None,
            comment: Optional[str] = None
    ) -> Dict:
        """
        Create a new version of a page

        Args:
            page_path: Page path
            label: Version label
            comment: Version comment

        Returns:
            Created version info
        """
        try:
            url = f"{self.host}/bin/wcmcommand"

            payload = {
                'cmd': 'createVersion',
                'path': page_path,
                '_charset_': 'utf-8'
            }

            if label:
                payload['label'] = label
            if comment:
                payload['comment'] = comment

            response = requests.post(
                url,
                auth=self.auth,
                data=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'message': f'Version created for {page_path}',
                    'label': label
                }

            return {
                'success': False,
                'error': 'Failed to create version'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def restore_version(
            self,
            page_path: str,
            version_name: str
    ) -> Dict:
        """
        Restore a page to a specific version

        Args:
            page_path: Page path
            version_name: Version to restore

        Returns:
            Restore result
        """
        try:
            url = f"{self.host}/bin/wcmcommand"

            payload = {
                'cmd': 'restoreVersion',
                'path': page_path,
                'version': version_name,
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
                    'message': f'Restored to version {version_name}'
                }

            return {
                'success': False,
                'error': 'Failed to restore version'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def compare_versions(
            self,
            page_path: str,
            version1: str,
            version2: str
    ) -> Dict:
        """
        Compare two versions of a page

        Args:
            page_path: Page path
            version1: First version
            version2: Second version

        Returns:
            Comparison results
        """
        try:
            # Get content for both versions
            content1 = self.get_version_content(page_path, version1)
            content2 = self.get_version_content(page_path, version2)

            if content1.get('success') and content2.get('success'):
                return {
                    'success': True,
                    'version1': {
                        'name': version1,
                        'content': content1.get('content', '')
                    },
                    'version2': {
                        'name': version2,
                        'content': content2.get('content', '')
                    }
                }

            return {
                'success': False,
                'error': 'Failed to retrieve version content'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }