"""
Neural LAB - AI Solutions Platform
Chat Resource - LLM completions.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from collections.abc import Iterator
from dataclasses import dataclass

from ..base import DataclassMixin


@dataclass
class ChatMessage(DataclassMixin):
    """Chat message."""

    role: str  # system, user, assistant
    content: str


@dataclass
class ChatCompletion(DataclassMixin):
    """Chat completion response."""

    id: str
    content: str
    model: str
    usage: dict[str, int]
    finish_reason: str


class ChatResource:
    """
    Chat completions resource.

    Usage:
        response = client.chat.complete(
            messages=[{"role": "user", "content": "Olá!"}],
            model="maritaca-sabia-3"
        )
        print(response.content)
    """

    def __init__(self, client):
        self._client = client

    def complete(
        self,
        messages: list[dict[str, str]],
        model: str = "maritaca-sabia-3",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system: str | None = None,
        **kwargs,
    ) -> ChatCompletion:
        """
        Create a chat completion.

        Args:
            messages: List of messages [{"role": "user", "content": "..."}]
            model: Model to use (maritaca-sabia-3, claude-sonnet, claude-opus)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)
            system: System prompt (optional)
            **kwargs: Additional parameters

        Returns:
            ChatCompletion with response
        """
        # Prepend system message if provided
        if system:
            messages = [{"role": "system", "content": system}] + messages

        response = self._client.post(
            "/v1/llm/completions",
            json={
                "messages": messages,
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                **kwargs,
            },
        )

        return ChatCompletion(
            id=response.get("id", ""),
            content=response.get("choices", [{}])[0]
            .get("message", {})
            .get("content", ""),
            model=response.get("model", model),
            usage=response.get("usage", {}),
            finish_reason=response.get("choices", [{}])[0].get("finish_reason", "stop"),
        )

    def complete_stream(
        self,
        messages: list[dict[str, str]],
        model: str = "maritaca-sabia-3",
        **kwargs,
    ) -> Iterator[str]:
        """
        Create a streaming chat completion.

        Args:
            messages: List of messages
            model: Model to use
            **kwargs: Additional parameters

        Yields:
            Content chunks as they arrive
        """
        # TODO: Implement streaming when API supports it
        response = self.complete(messages, model, **kwargs)
        yield response.content
