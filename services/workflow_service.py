"""
AEM Workflow Service
Handles workflow operations
"""
import requests
from requests.auth import HTTPBasicAuth
from typing import List, Dict
from config import Config


class WorkflowService:
    def __init__(self):
        self.host = Config.AEM_HOST
        self.auth = HTTPBasicAuth(Config.AEM_USERNAME, Config.AEM_PASSWORD)

    def list_workflows(self) -> Dict:
        """Get available workflow models"""
        try:
            url = f"{self.host}/etc/workflow/models.json"
            response = requests.get(url, auth=self.auth, timeout=10)

            if response.status_code == 200:
                workflows = []
                for item in response.json():
                    workflows.append({
                        'id': item.get('jcr:primaryType'),
                        'title': item.get('jcr:title', ''),
                        'path': item.get('path', '')
                    })
                return {'success': True, 'workflows': workflows}
            return {'success': False, 'error': 'Failed to fetch workflows'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def start_workflow(self, page_path: str, workflow_model: str) -> Dict:
        """Start workflow on a page"""
        try:
            url = f"{self.host}/etc/workflow/instances"

            payload = {
                'model': workflow_model,
                'payloadType': 'JCR_PATH',
                'payload': page_path
            }

            response = requests.post(url, auth=self.auth, data=payload, timeout=30)

            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'message': f'Workflow started on {page_path}'
                }
            return {'success': False, 'error': 'Failed to start workflow'}
        except Exception as e:
            return {'success': False, 'error': str(e)}