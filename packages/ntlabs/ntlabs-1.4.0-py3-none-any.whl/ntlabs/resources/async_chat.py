"""
Neural LAB - AI Solutions Platform
Async Chat Resource - LLM completions.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from collections.abc import AsyncIterator

from .chat import ChatCompletion


class AsyncChatResource:
    """
    Async chat completions resource.

    Usage:
        async with AsyncNeuralLabClient(api_key="nl_xxx") as client:
            response = await client.chat.complete(
                messages=[{"role": "user", "content": "Olá!"}],
                model="maritaca-sabia-3"
            )
            print(response.content)
    """

    def __init__(self, client):
        self._client = client

    async def complete(
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
        if system:
            messages = [{"role": "system", "content": system}] + messages

        response = await self._client.post(
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

    async def complete_stream(
        self,
        messages: list[dict[str, str]],
        model: str = "maritaca-sabia-3",
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Create a streaming chat completion.

        Args:
            messages: List of messages
            model: Model to use
            **kwargs: Additional parameters

        Yields:
            Content chunks as they arrive
        """
        # TODO: Implement true streaming when API supports SSE
        response = await self.complete(messages, model, **kwargs)
        yield response.content
