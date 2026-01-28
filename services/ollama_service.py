"""
Ollama Service - Handles all interactions with Ollama API
"""
import requests
import json
from typing import List, Dict, Optional
from config import Config


class OllamaService:
    def __init__(self):
        self.base_url = Config.OLLAMA_HOST
        self.default_model = Config.DEFAULT_MODEL
        self.timeout = Config.OLLAMA_TIMEOUT

    def chat(
            self,
            messages: List[Dict[str, str]],
            model: Optional[str] = None,
            temperature: float = 0.7,
            stream: bool = False
    ) -> Dict:
        """
        Send chat messages to Ollama

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: gemma:2b)
            temperature: Temperature for generation
            stream: Whether to stream the response

        Returns:
            Response from Ollama
        """
        model = model or self.default_model

        payload = {
            'model': model,
            'messages': messages,
            'stream': stream,
            'options': {
                'temperature': temperature,
                'num_predict': 2048
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            if stream:
                return response
            else:
                data = response.json()
                return {
                    'success': True,
                    'message': data.get('message', {}).get('content', ''),
                    'model': model,
                    'done': data.get('done', False)
                }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': f'Failed to connect to Ollama at {self.base_url}'
            }

    def generate(
            self,
            prompt: str,
            model: Optional[str] = None,
            temperature: float = 0.7,
            system: Optional[str] = None
    ) -> Dict:
        """
        Generate text completion from Ollama

        Args:
            prompt: Input prompt
            model: Model name
            temperature: Temperature for generation
            system: System message

        Returns:
            Generated response
        """
        model = model or self.default_model

        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temperature
            }
        }

        if system:
            payload['system'] = system

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'response': data.get('response', ''),
                'model': model
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'response': ''
            }

    def analyze_html(
            self,
            html_content: str,
            check_prompt: str,
            model: Optional[str] = None
    ) -> Dict:
        """
        Analyze HTML content using Ollama

        Args:
            html_content: HTML content to analyze
            check_prompt: Specific compliance check prompt
            model: Model to use

        Returns:
            Analysis results
        """
        system_message = """You are an expert web developer and accessibility auditor. 
Analyze the provided HTML and answer the specific compliance question.
Provide clear, actionable feedback. Format your response as:
- Status: PASS or FAIL
- Issues: List specific issues found (or "None" if passed)
- Recommendations: Specific improvements needed"""

        # Truncate HTML if too long
        max_html_length = 4000
        if len(html_content) > max_html_length:
            html_content = html_content[:max_html_length] + "\n...[content truncated]"

        prompt = f"""HTML Content:
```html
{html_content}
```

Compliance Check: {check_prompt}

Provide your analysis:"""

        messages = [
            {'role': 'system', 'content': system_message},
            {'role': 'user', 'content': prompt}
        ]

        result = self.chat(messages, model=model, temperature=0.3)

        if result.get('success'):
            response_text = result.get('message', '')
            return self._parse_compliance_response(response_text)
        else:
            return {
                'passed': False,
                'issues': [f"Analysis failed: {result.get('error', 'Unknown error')}"],
                'recommendations': ['Retry the analysis']
            }

    def _parse_compliance_response(self, response: str) -> Dict:
        """
        Parse Ollama's compliance check response

        Args:
            response: Raw response text

        Returns:
            Structured compliance result
        """
        response_lower = response.lower()

        # Determine if check passed
        passed = 'pass' in response_lower and 'fail' not in response_lower

        # Extract issues
        issues = []
        recommendations = []

        lines = response.split('\n')
        current_section = None

        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            line_lower = line_clean.lower()

            if 'issue' in line_lower or 'problem' in line_lower:
                current_section = 'issues'
            elif 'recommendation' in line_lower or 'suggest' in line_lower or 'improve' in line_lower:
                current_section = 'recommendations'
            elif line_clean.startswith('-') or line_clean.startswith('•'):
                item = line_clean.lstrip('-•').strip()
                if current_section == 'issues':
                    issues.append(item)
                elif current_section == 'recommendations':
                    recommendations.append(item)

        # If no structured data found, use the whole response
        if not issues and not passed:
            issues = ['Review the detailed analysis below']
        if not recommendations:
            recommendations = [response[:200]] if len(response) > 200 else [response]

        return {
            'passed': passed,
            'issues': issues if issues else ['None'],
            'recommendations': recommendations
        }

    def check_health(self) -> bool:
        """
        Check if Ollama service is available

        Returns:
            True if service is healthy
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> List[str]:
        """
        List available Ollama models

        Returns:
            List of model names
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                return [model.get('name', '') for model in models]
            return []
        except:
            return []