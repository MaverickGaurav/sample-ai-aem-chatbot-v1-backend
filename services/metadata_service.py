"""
Metadata Service for AEM Assets
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import Dict
from config import Config


class MetadataService:
    def __init__(self):
        self.host = Config.AEM_HOST
        self.auth = HTTPBasicAuth(Config.AEM_USERNAME, Config.AEM_PASSWORD)

    def get_metadata(self, asset_path: str) -> Dict:
        """Get asset metadata"""
        try:
            url = f"{self.host}{asset_path}/jcr:content/metadata.json"
            response = requests.get(url, auth=self.auth, timeout=10)

            if response.status_code == 200:
                return {
                    'success': True,
                    'metadata': response.json()
                }
            return {'success': False, 'error': 'Asset not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def update_metadata(self, asset_path: str, metadata: Dict) -> Dict:
        """Update asset metadata"""
        try:
            url = f"{self.host}{asset_path}/jcr:content/metadata"

            response = requests.post(
                url,
                auth=self.auth,
                data=metadata,
                timeout=30
            )

            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'message': 'Metadata updated successfully'
                }
            return {'success': False, 'error': 'Failed to update metadata'}
        except Exception as e:
            return {'success': False, 'error': str(e)}