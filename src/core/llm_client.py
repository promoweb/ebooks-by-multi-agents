"""
LLM Client Abstraction for BookWriterAI.

This module provides a unified interface for interacting with different LLM providers
(OpenAI, Bailian/Qwen, custom endpoints) with built-in retry logic, rate limiting,
and error handling.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Install openai: pip install openai>=1.0.0")

try:
    import requests
except ImportError:
    raise ImportError("Install requests: pip install requests")

from src.core.config import Config, LLMConfig, Provider
from src.core.exceptions import (
    LLMError, 
    LLMConnectionError, 
    LLMRateLimitError, 
    LLMResponseError
)


logger = logging.getLogger("BookWriterAI")


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    raw_response: Any = None


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate text from the LLM."""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass


class OpenAIClient(BaseLLMClient):
    """
    Client for OpenAI-compatible APIs.
    
    Supports:
    - OpenAI native API
    - Bailian (OpenClaw/Coding Plan)
    - Any OpenAI-compatible endpoint
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = self._setup_client()
        self._encoding = self._setup_encoding()
    
    def _setup_client(self) -> OpenAI:
        """Set up the OpenAI client."""
        client_kwargs = {"api_key": self.config.api_key}
        
        base_url = self.config.get_base_url()
        if base_url:
            client_kwargs["base_url"] = base_url
        
        return OpenAI(**client_kwargs)
    
    def _setup_encoding(self):
        """Set up tiktoken encoding for token counting."""
        try:
            import tiktoken
            # Try to get model-specific encoding
            try:
                return tiktoken.encoding_for_model(self.config.model)
            except KeyError:
                # Fall back to cl100k_base (GPT-4 encoding)
                return tiktoken.get_encoding("cl100k_base")
        except ImportError:
            logger.warning("tiktoken not available, using approximate token counting")
            return None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken or approximation."""
        if self._encoding:
            return len(self._encoding.encode(text))
        # Approximate: 1 token ≈ 4 characters
        return len(text) // 4
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate text using OpenAI-compatible API."""
        max_tokens = max_tokens or self.config.max_tokens_per_call
        temperature = temperature if temperature is not None else self.config.temperature
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(self.config.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )
                
                return LLMResponse(
                    content=response.choices[0].message.content.strip(),
                    model=response.model,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    finish_reason=response.choices[0].finish_reason,
                    raw_response=response
                )
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check for rate limit
                if "rate limit" in error_str or "429" in error_str:
                    retry_after = self._extract_retry_after(e)
                    if attempt < self.config.max_retries - 1:
                        wait_time = retry_after or (self.config.retry_delay ** (attempt + 1))
                        logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise LLMRateLimitError(retry_after)
                
                # Check for connection errors
                if "connection" in error_str or "timeout" in error_str:
                    if attempt < self.config.max_retries - 1:
                        wait_time = self.config.retry_delay ** (attempt + 1)
                        logger.warning(f"Connection error, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise LLMConnectionError(f"Connection failed after {self.config.max_retries} attempts: {e}")
                
                # Other errors
                logger.error(f"LLM API error: {e}")
                raise LLMResponseError(f"LLM API error: {e}")
        
        raise LLMError("Max retries exceeded")
    
    def _extract_retry_after(self, error: Exception) -> Optional[int]:
        """Extract retry-after value from error if available."""
        # Try to extract from headers if available
        if hasattr(error, 'response') and hasattr(error.response, 'headers'):
            retry_after = error.response.headers.get('retry-after')
            if retry_after:
                try:
                    return int(retry_after)
                except ValueError:
                    pass
        return None


class QwenNativeClient(BaseLLMClient):
    """
    Client for Qwen/DashScope native API.
    
    Uses the DashScope text-generation API directly.
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        }
        self._encoding = self._setup_encoding()
    
    def _setup_encoding(self):
        """Set up token counting (approximation for Qwen models)."""
        # Qwen uses a different tokenizer, we approximate
        return None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens (approximation for Qwen models)."""
        # Qwen tokenizer approximation: ~1.5 characters per token for Chinese
        # For mixed content, use ~3 characters per token
        return len(text) // 3
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate text using DashScope native API."""
        max_tokens = max_tokens or self.config.max_tokens_per_call
        temperature = temperature if temperature is not None else self.config.temperature
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.config.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        }
        
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Parse DashScope response format
                output = data.get("output", {})
                usage = data.get("usage", {})
                
                return LLMResponse(
                    content=output.get("text", "").strip(),
                    model=self.config.model,
                    usage={
                        "prompt_tokens": usage.get("input_tokens", 0),
                        "completion_tokens": usage.get("output_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    },
                    finish_reason=output.get("finish_reason", "stop"),
                    raw_response=data
                )
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    retry_after = self._extract_retry_after(e.response)
                    if attempt < self.config.max_retries - 1:
                        wait_time = retry_after or (self.config.retry_delay ** (attempt + 1))
                        logger.warning(f"Rate limit hit, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    raise LLMRateLimitError(retry_after)
                raise LLMConnectionError(f"HTTP error: {e}")
                
            except requests.exceptions.ConnectionError as e:
                if attempt < self.config.max_retries - 1:
                    wait_time = self.config.retry_delay ** (attempt + 1)
                    logger.warning(f"Connection error, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                raise LLMConnectionError(f"Connection failed: {e}")
                
            except Exception as e:
                logger.error(f"DashScope API error: {e}")
                raise LLMResponseError(f"DashScope API error: {e}")
        
        raise LLMError("Max retries exceeded")
    
    def _extract_retry_after(self, response) -> Optional[int]:
        """Extract retry-after from response headers."""
        retry_after = response.headers.get('retry-after')
        if retry_after:
            try:
                return int(retry_after)
            except ValueError:
                pass
        return None


class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create(config: LLMConfig) -> BaseLLMClient:
        """Create appropriate LLM client based on provider."""
        if config.provider in [Provider.OPENAI, Provider.BAILIAN, Provider.CUSTOM]:
            return OpenAIClient(config)
        elif config.provider == Provider.QWEN:
            return QwenNativeClient(config)
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")


# =============================================================================
# Convenience Functions
# =============================================================================

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in text.
    
    This is a convenience function that doesn't require a full config.
    For accurate counting with model-specific tokenizers, use an LLMClient.
    """
    try:
        import tiktoken
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except ImportError:
        return len(text) // 4


def estimate_cost(tokens: int, model: str, input_tokens: bool = True) -> float:
    """
    Estimate cost for token usage.
    
    Note: Prices are approximate and may not be current.
    """
    # Approximate pricing per 1K tokens (as of 2024)
    pricing = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "qwen3.5-plus": {"input": 0.0004, "output": 0.0012},  # Approximate
        "qwen-max": {"input": 0.002, "output": 0.006},  # Approximate
    }
    
    model_pricing = pricing.get(model, {"input": 0.001, "output": 0.002})
    token_type = "input" if input_tokens else "output"
    price_per_1k = model_pricing[token_type]
    
    return (tokens / 1000) * price_per_1k