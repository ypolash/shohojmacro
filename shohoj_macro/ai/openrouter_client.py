import os
import httpx
from typing import List, Dict, Any, Optional
from shohoj_macro.core.settings_manager import SettingsManager

class OpenRouterClient:
    """Generic OpenRouter API client with configurable model selection."""
    
    def __init__(self, api_key: str = None, default_model: str = None):
        self.settings = SettingsManager()
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = default_model
        
    def _get_api_key(self) -> str:
        key = self.api_key or self.settings.get("ai", "openrouter_api_key", os.environ.get("OPENROUTER_API_KEY", ""))
        if not key:
            raise ValueError("OpenRouter API key is missing. Please configure it in Settings.")
        return key

    def _get_model(self, override_model: str = None) -> str:
        return override_model or self.default_model or self.settings.get("ai", "model", "google/gemini-flash-1.5")

    def chat_with_images(
        self,
        prompt: str,
        image_base64_list: List[str],
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 500,
    ) -> str:
        """Sends text + multiple images to OpenRouter vision model, returns text response."""
        api_key = self._get_api_key()
        use_model = self._get_model(model)
        
        # Prepare content payload
        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        
        for img_b64 in image_base64_list:
            # Assumes PNG, strip data prefix if present
            if img_b64.startswith("data:image"):
                img_b64 = img_b64.split(",")[1]
                
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_b64}"
                }
            })
            
        payload = {
            "model": use_model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://shohojmacro.com",
            "X-Title": "Shohoj Macro Operation System",
        }
        
        # Synchronous request for player thread compatibility
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API Error: {response.text}")
            
        data = response.json()
        return data["choices"][0]["message"]["content"]
        
    def chat_text(self, prompt: str, model: str = None) -> str:
        """Text-only chat completion."""
        api_key = self._get_api_key()
        use_model = self._get_model(model)
        
        payload = {
            "model": use_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://shohojmacro.com",
            "X-Title": "Shohoj Macro Operation System",
        }
        
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API Error: {response.text}")
            
        return response.json()["choices"][0]["message"]["content"]
