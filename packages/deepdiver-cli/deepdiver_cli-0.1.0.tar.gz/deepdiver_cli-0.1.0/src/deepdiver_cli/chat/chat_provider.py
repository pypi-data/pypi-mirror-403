"""
Abstract interface for chat providers.

This module defines the ChatProvider interface that all LLM providers
must implement. The interface provides a single `generate` method that
returns a stream of LLMResponse objects (both deltas and complete types).

Note: The old `chat` and `stream_chat` methods are deprecated and will
be removed in a future version. New providers should only implement `generate`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from .chat_model import LLMProviderConfig, LLMRequest
from .response_types import LLMResponse


class ChatProvider(ABC):
    """
    Abstract base class for all LLM chat providers.

    Providers implement this interface to support different LLM APIs
    (OpenRouter, DeepSeek, AliBaBa, etc.) with a unified streaming interface.
    """

    def __init__(self, provider_config: LLMProviderConfig):
        self.provider_config = provider_config

    @abstractmethod
    async def generate(self, request: LLMRequest) -> AsyncIterator[LLMResponse]:
        """
        Generate LLM response as a stream of response objects.

        This is the primary method that all providers must implement.
        It returns a stream of LLMResponse objects, which can be either
        delta types (incremental updates) or complete types.

        Args:
            request: LLM request containing model, messages, parameters

        Yields:
            LLMResponse: Stream of response objects

        Raises:
            ProviderError: For provider-specific errors
            TimeoutError: If request times out
        """
        raise NotImplementedError

