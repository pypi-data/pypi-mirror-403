from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import os

class LLMBackend(ABC):
    """
    Abstract Base Class for LLM Providers.
    Allows StreamWish to be model-agnostic.
    """

    @abstractmethod
    def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs) -> str:
        """
        Generates text from the LLM.
        """
        pass

    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """
        Generates an embedding vector for the given text.
        """
        pass

class OpenAIAdapter(LLMBackend):
    """
    Adapter for OpenAI's API.
    """
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Please install openai package: pip install openai")
            
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content or ""

    def get_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

class MockLLMAdapter(LLMBackend):
    """
    Mock adapter for testing without API keys.
    """
    def generate(self, prompt: str, system_instruction: Optional[str] = None, **kwargs) -> str:
        return f"Mock response to: {prompt[:20]}..."

    def get_embedding(self, text: str) -> List[float]:
        return [0.1] * 1536  # Mock embedding vector

class ModelRegistry:
    _backends: Dict[str, LLMBackend] = {}

    @classmethod
    def register(cls, name: str, backend: LLMBackend):
        cls._backends[name] = backend

    @classmethod
    def get(cls, name: str) -> LLMBackend:
        if name not in cls._backends:
            # Default fallback or error
            raise ValueError(f"Model backend '{name}' not found.")
        return cls._backends[name]
