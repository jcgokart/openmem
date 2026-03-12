"""
LLM Client - Support multiple providers
- trae: Current Trae context (default)
- ollama: Local free models
- deepseek: Cheap API
- openai: Standard API
"""

import json
import os
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    TRAE = "trae"
    OLLAMA = "ollama"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"


@dataclass
class LLMConfig:
    provider: str = "trae"
    model: str = "default"
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class LLMClient:
    """LLM Client"""

    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig()

    def chat(self, prompt: str, system_prompt: str = None) -> str:
        """Call LLM"""
        provider = self.config.provider

        if provider == "trae":
            return self._chat_trae(prompt, system_prompt)
        elif provider == "ollama":
            return self._chat_ollama(prompt, system_prompt)
        elif provider == "deepseek":
            return self._chat_deepseek(prompt, system_prompt)
        elif provider == "openai":
            return self._chat_openai(prompt, system_prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _chat_trae(self, prompt: str, system_prompt: str = None) -> str:
        """Trae mode: Generate prompt for user to copy to Trae"""
        return f"""
Please help me summarize the following conversation:

{prompt}

Please output in JSON format:
{{"decisions": [], "todos": [], "records": []}}
"""

    def _chat_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """Ollama local model"""
        base_url = self.config.base_url or "http://localhost:11434"
        model = self.config.model or "qwen2.5:3b"

        url = f"{base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are a meeting notes assistant."},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()

        return response.json()["message"]["content"]

    def _chat_deepseek(self, prompt: str, system_prompt: str = None) -> str:
        """DeepSeek API"""
        api_key = self.config.api_key or os.getenv("DEEPSEEK_API_KEY")
        base_url = self.config.base_url or "https://api.deepseek.com"

        url = f"{base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config.model or "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt or "You are a meeting notes assistant."},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]

    def _chat_openai(self, prompt: str, system_prompt: str = None) -> str:
        """OpenAI API"""
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        base_url = self.config.base_url or "https://api.openai.com/v1"

        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.config.model or "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt or "You are a meeting notes assistant."},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]


def get_llm_client(provider: str = None, model: str = None, api_key: str = None) -> LLMClient:
    """Get LLM client"""
    config = LLMConfig(
        provider=provider or "trae",
        model=model,
        api_key=api_key
    )
    return LLMClient(config)


if __name__ == "__main__":
    client = get_llm_client("trae")
    print(client.chat("Test conversation content"))
