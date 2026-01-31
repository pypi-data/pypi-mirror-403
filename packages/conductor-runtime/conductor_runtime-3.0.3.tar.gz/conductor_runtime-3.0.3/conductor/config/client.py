"""
Model client factory for Conductor.
Creates LLM clients from configuration.
"""
import os
from typing import Optional, Any
from conductor.config.models import ModelConfig, ConductorConfig


def create_model_client(config: ModelConfig) -> Optional[Any]:
    """
    Create an OpenAI-compatible client for Gemini.
    
    Returns None if API key is not set.
    """
    api_key = config.get_api_key()
    
    if not api_key:
        return None
    
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=config.base_url,
        )
        
        # Wrap to match expected interface
        return ModelClientWrapper(client, config)
        
    except ImportError:
        print("Warning: openai package not installed. pip install openai")
        return None
    except Exception as e:
        print(f"Warning: Failed to create model client: {e}")
        return None


class ModelClientWrapper:
    """
    Wrapper that provides a consistent interface for LLM calls.
    Uses OpenAI-compatible API for Gemini.
    """
    
    def __init__(self, client: Any, config: ModelConfig):
        self.client = client
        self.config = config
        self.model = config.model_name
    
    async def create(self, messages: list[dict], **kwargs) -> Any:
        """
        Create a chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
        
        Returns:
            OpenAI-compatible response object
        """
        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )


def create_clients_for_roles(config: ConductorConfig) -> dict[str, Optional[Any]]:
    """
    Create model clients for all agent roles.
    
    Returns a dict mapping role names to clients.
    """
    return {
        "planner": create_model_client(config.planner_model),
        "executor": create_model_client(config.executor_model),
        "reviewer": create_model_client(config.reviewer_model),
        "verifier": create_model_client(config.reviewer_model),  # Use reviewer config
        "repair": create_model_client(config.planner_model),    # Use planner config
    }
