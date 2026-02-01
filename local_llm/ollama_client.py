"""
Ollama Client for Local LLM Inference

Provides a simple interface to communicate with a local Ollama server
for code review tasks. No external API keys required.
"""

import requests
import json
import time
from typing import Optional, List, Dict, Any


class OllamaClient:
    """Client for interacting with local Ollama server."""
    
    def __init__(
        self,
        model: str = "deepseek-coder:6.7b",
        host: str = "http://localhost:11434",
        timeout: int = 300
    ):
        """
        Initialize Ollama client.
        
        Args:
            model: Model name to use (default: deepseek-coder:6.7b)
            host: Ollama server URL (default: http://localhost:11434)
            timeout: Request timeout in seconds (default: 300)
        """
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout
    
    def is_server_running(self) -> bool:
        """Check if Ollama server is running and accessible."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def list_models(self) -> List[str]:
        """List all available models on the server."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except requests.RequestException:
            return []
    
    def pull_model(self, model: Optional[str] = None) -> bool:
        """
        Pull a model from Ollama registry.
        
        Args:
            model: Model name to pull (default: use instance model)
            
        Returns:
            True if successful, False otherwise
        """
        model = model or self.model
        try:
            response = requests.post(
                f"{self.host}/api/pull",
                json={"name": model},
                timeout=600,  # Model downloads can take a while
                stream=True
            )
            response.raise_for_status()
            # Stream the response to handle progress
            for line in response.iter_lines():
                if line:
                    status = json.loads(line)
                    if status.get("status") == "success":
                        return True
            return True
        except requests.RequestException as e:
            print(f"Failed to pull model: {e}")
            return False
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> str:
        """
        Generate a completion using the local LLM.
        
        Args:
            prompt: User prompt/question
            system: System prompt (optional)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            
        Returns:
            Generated text response
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except requests.RequestException as e:
            return f"Error generating response: {e}"
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> str:
        """
        Chat completion using the local LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Assistant's response text
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except requests.RequestException as e:
            return f"Error in chat: {e}"
    
    def wait_for_server(self, max_wait: int = 60) -> bool:
        """
        Wait for Ollama server to become available.
        
        Args:
            max_wait: Maximum seconds to wait
            
        Returns:
            True if server is available, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < max_wait:
            if self.is_server_running():
                return True
            time.sleep(1)
        return False
