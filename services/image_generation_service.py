"""
Image Generation Service - Stable Diffusion / DALL-E Integration
Generates images from text prompts with style presets
"""
import os
import base64
import requests
from typing import Dict, Optional, List
from datetime import datetime
from config import Config
import json


class ImageGenerationService:
    def __init__(self):
        self.upload_folder = os.path.join(Config.UPLOAD_FOLDER, 'generated_images')
        os.makedirs(self.upload_folder, exist_ok=True)

        # Style presets
        self.style_presets = {
            'realistic': {
                'suffix': ', photorealistic, highly detailed, 8k, professional photography',
                'negative': 'cartoon, anime, painting, drawing, illustration'
            },
            'artistic': {
                'suffix': ', digital art, artstation, concept art, detailed, vibrant colors',
                'negative': 'photo, photograph, realistic'
            },
            'cartoon': {
                'suffix': ', cartoon style, animated, colorful, disney pixar style',
                'negative': 'realistic, photo, photograph'
            },
            'anime': {
                'suffix': ', anime style, manga, studio ghibli, detailed',
                'negative': 'realistic, photo, western cartoon'
            },
            'sketch': {
                'suffix': ', pencil sketch, hand drawn, detailed line art, graphite',
                'negative': 'color, colored, painting, digital'
            },
            'oil_painting': {
                'suffix': ', oil painting, fine art, textured brush strokes, masterpiece',
                'negative': 'digital, photo, cartoon'
            },
            'watercolor': {
                'suffix': ', watercolor painting, soft colors, artistic',
                'negative': 'digital, photo, sharp'
            },
            'cyberpunk': {
                'suffix': ', cyberpunk style, neon, futuristic, sci-fi, highly detailed',
                'negative': 'medieval, ancient, rustic'
            }
        }

    def generate_image_local(
            self,
            prompt: str,
            style: str = 'realistic',
            width: int = 512,
            height: int = 512,
            steps: int = 30
    ) -> Dict:
        """
        Generate image using local Stable Diffusion
        Requires Stable Diffusion WebUI running locally

        Args:
            prompt: Text description
            style: Style preset
            width: Image width
            height: Image height
            steps: Number of diffusion steps

        Returns:
            Generated image information
        """
        try:
            # Apply style preset
            style_config = self.style_presets.get(style, self.style_presets['realistic'])
            full_prompt = prompt + style_config['suffix']
            negative_prompt = style_config['negative']

            # Local Stable Diffusion WebUI API
            url = "http://127.0.0.1:7860/sdapi/v1/txt2img"

            payload = {
                "prompt": full_prompt,
                "negative_prompt": negative_prompt,
                "steps": steps,
                "width": width,
                "height": height,
                "cfg_scale": 7,
                "sampler_name": "DPM++ 2M Karras",
                "seed": -1
            }

            response = requests.post(url, json=payload, timeout=120)

            if response.status_code == 200:
                result = response.json()

                # Save image
                image_data = result['images'][0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"generated_{timestamp}.png"
                filepath = os.path.join(self.upload_folder, filename)

                # Decode and save
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(image_data))

                file_size = os.path.getsize(filepath)

                return {
                    'success': True,
                    'file_path': filepath,
                    'file_name': filename,
                    'size_bytes': file_size,
                    'prompt': prompt,
                    'full_prompt': full_prompt,
                    'style': style,
                    'width': width,
                    'height': height,
                    'provider': 'stable_diffusion_local'
                }
            else:
                return {
                    'success': False,
                    'error': 'Stable Diffusion not available. Please start SD WebUI on http://127.0.0.1:7860'
                }

        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Cannot connect to Stable Diffusion WebUI. Please ensure it is running on http://127.0.0.1:7860'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Image generation failed: {str(e)}'
            }

    def generate_image_replicate(
            self,
            prompt: str,
            style: str = 'realistic',
            width: int = 512,
            height: int = 512,
            api_key: Optional[str] = None
    ) -> Dict:
        """
        Generate image using Replicate API (SDXL)

        Args:
            prompt: Text description
            style: Style preset
            width: Image width
            height: Image height
            api_key: Replicate API key

        Returns:
            Generated image information
        """
        try:
            if not api_key:
                api_key = os.getenv('REPLICATE_API_KEY')

            if not api_key:
                return {
                    'success': False,
                    'error': 'Replicate API key not provided. Set REPLICATE_API_KEY environment variable.'
                }

            # Apply style preset
            style_config = self.style_presets.get(style, self.style_presets['realistic'])
            full_prompt = prompt + style_config['suffix']
            negative_prompt = style_config['negative']

            # Replicate SDXL API
            import replicate

            output = replicate.run(
                "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                input={
                    "prompt": full_prompt,
                    "negative_prompt": negative_prompt,
                    "width": width,
                    "height": height,
                    "num_outputs": 1
                }
            )

            # Download image
            if output and len(output) > 0:
                image_url = output[0]

                # Download and save
                response = requests.get(image_url)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"generated_{timestamp}.png"
                filepath = os.path.join(self.upload_folder, filename)

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                file_size = os.path.getsize(filepath)

                return {
                    'success': True,
                    'file_path': filepath,
                    'file_name': filename,
                    'size_bytes': file_size,
                    'prompt': prompt,
                    'full_prompt': full_prompt,
                    'style': style,
                    'width': width,
                    'height': height,
                    'provider': 'replicate_sdxl'
                }
            else:
                return {
                    'success': False,
                    'error': 'No image generated'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Image generation failed: {str(e)}'
            }

    def enhance_prompt(self, basic_prompt: str, model: str = "gemma:2b") -> str:
        """
        Use Ollama to enhance/expand a basic prompt into detailed one

        Args:
            basic_prompt: User's basic prompt
            model: Ollama model for enhancement

        Returns:
            Enhanced prompt
        """
        from services.ollama_service import OllamaService

        ollama = OllamaService()

        system_prompt = """You are an expert at writing prompts for image generation AI.
Given a basic description, expand it into a detailed, vivid prompt that will generate better images.
Include details about:
- Composition and framing
- Lighting and atmosphere
- Colors and mood
- Textures and materials
- Artistic style if appropriate

Keep the enhanced prompt under 200 words. Return ONLY the enhanced prompt, nothing else."""

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f'Enhance this prompt: {basic_prompt}'}
        ]

        result = ollama.chat(messages, model=model, temperature=0.7)

        if result.get('success'):
            return result.get('message', basic_prompt)
        else:
            return basic_prompt

    def get_style_presets(self) -> List[Dict]:
        """
        Get available style presets

        Returns:
            List of style preset information
        """
        return [
            {'id': 'realistic', 'name': 'Realistic', 'description': 'Photorealistic images'},
            {'id': 'artistic', 'name': 'Digital Art', 'description': 'Digital artwork style'},
            {'id': 'cartoon', 'name': 'Cartoon', 'description': 'Animated cartoon style'},
            {'id': 'anime', 'name': 'Anime', 'description': 'Japanese anime/manga style'},
            {'id': 'sketch', 'name': 'Sketch', 'description': 'Pencil sketch drawing'},
            {'id': 'oil_painting', 'name': 'Oil Painting', 'description': 'Classic oil painting'},
            {'id': 'watercolor', 'name': 'Watercolor', 'description': 'Watercolor painting'},
            {'id': 'cyberpunk', 'name': 'Cyberpunk', 'description': 'Futuristic cyberpunk style'}
        ]

    def generate_image(
            self,
            prompt: str,
            style: str = 'realistic',
            width: int = 512,
            height: int = 512,
            provider: str = 'local'
    ) -> Dict:
        """
        Main image generation method - tries local first, falls back to API

        Args:
            prompt: Text description
            style: Style preset
            width: Image width
            height: Image height
            provider: Preferred provider ('local' or 'replicate')

        Returns:
            Generated image information
        """
        if provider == 'local':
            result = self.generate_image_local(prompt, style, width, height)

            # If local fails, could fallback to Replicate
            # if not result.get('success'):
            #     result = self.generate_image_replicate(prompt, style, width, height)

            return result
        else:
            return self.generate_image_replicate(prompt, style, width, height)

    def check_health(self) -> Dict:
        """
        Check if image generation services are available

        Returns:
            Status of available services
        """
        status = {
            'local_sd': False,
            'replicate': False
        }

        # Check local SD
        try:
            response = requests.get('http://127.0.0.1:7860/sdapi/v1/sd-models', timeout=2)
            status['local_sd'] = response.status_code == 200
        except:
            pass

        # Check Replicate API key
        status['replicate'] = bool(os.getenv('REPLICATE_API_KEY'))

        return status