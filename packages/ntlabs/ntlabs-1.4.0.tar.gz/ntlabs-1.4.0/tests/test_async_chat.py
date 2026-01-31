"""
NTLabs SDK - Async Chat Resource Tests
Tests for the AsyncChatResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
from unittest.mock import AsyncMock, patch

from ntlabs.resources.async_chat import AsyncChatResource
from ntlabs.resources.chat import ChatCompletion


@pytest.mark.asyncio
class TestAsyncChatResource:
    """Tests for AsyncChatResource."""

    async def test_initialization(self):
        """AsyncChatResource initializes with client."""
        mock_client = AsyncMock()
        chat = AsyncChatResource(mock_client)
        assert chat._client == mock_client

    async def test_complete_basic(self, chat_response):
        """Basic async chat completion."""
        mock_client = AsyncMock()
        mock_client.post.return_value = chat_response

        chat = AsyncChatResource(mock_client)
        result = await chat.complete(messages=[{"role": "user", "content": "Olá!"}])

        assert isinstance(result, ChatCompletion)
        assert result.content == "Olá! Como posso ajudar?"
        assert result.model == "maritaca-sabia-3"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/llm/completions"

    async def test_complete_with_model(self, chat_response):
        """Async chat completion with specific model."""
        mock_client = AsyncMock()
        mock_client.post.return_value = chat_response

        chat = AsyncChatResource(mock_client)
        result = await chat.complete(
            messages=[{"role": "user", "content": "Hello"}],
            model="claude-sonnet",
        )

        assert isinstance(result, ChatCompletion)
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["model"] == "claude-sonnet"

    async def test_complete_with_system_prompt(self, chat_response):
        """Async chat completion with system prompt."""
        mock_client = AsyncMock()
        mock_client.post.return_value = chat_response

        chat = AsyncChatResource(mock_client)
        result = await chat.complete(
            messages=[{"role": "user", "content": "What is Python?"}],
            system="You are a programming tutor.",
        )

        assert isinstance(result, ChatCompletion)
        call_kwargs = mock_client.post.call_args[1]
        messages = call_kwargs["json"]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a programming tutor."

    async def test_complete_with_parameters(self, chat_response):
        """Async chat completion with all parameters."""
        mock_client = AsyncMock()
        mock_client.post.return_value = chat_response

        chat = AsyncChatResource(mock_client)
        result = await chat.complete(
            messages=[{"role": "user", "content": "Tell me a story"}],
            model="maritaca-sabia-3",
            max_tokens=2048,
            temperature=0.9,
        )

        assert isinstance(result, ChatCompletion)
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["max_tokens"] == 2048
        assert call_kwargs["json"]["temperature"] == 0.9

    async def test_complete_multiple_messages(self, chat_response):
        """Async chat completion with conversation history."""
        mock_client = AsyncMock()
        mock_client.post.return_value = chat_response

        chat = AsyncChatResource(mock_client)
        messages = [
            {"role": "user", "content": "My name is João"},
            {"role": "assistant", "content": "Nice to meet you, João!"},
            {"role": "user", "content": "What is my name?"},
        ]

        result = await chat.complete(messages=messages)
        assert isinstance(result, ChatCompletion)
        call_kwargs = mock_client.post.call_args[1]
        assert len(call_kwargs["json"]["messages"]) == 3

    async def test_complete_empty_response(self):
        """Handle empty response gracefully."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {}

        chat = AsyncChatResource(mock_client)
        result = await chat.complete(messages=[{"role": "user", "content": "Hello"}])

        assert result.id == ""
        assert result.content == ""
        assert result.finish_reason == "stop"

    async def test_complete_with_kwargs(self, chat_response):
        """Async chat completion with extra kwargs."""
        mock_client = AsyncMock()
        mock_client.post.return_value = chat_response

        chat = AsyncChatResource(mock_client)
        result = await chat.complete(
            messages=[{"role": "user", "content": "Hello"}],
            top_p=0.95,
            presence_penalty=0.5,
        )

        assert isinstance(result, ChatCompletion)
        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["json"]["top_p"] == 0.95
        assert call_kwargs["json"]["presence_penalty"] == 0.5


@pytest.mark.asyncio
class TestAsyncChatResourceUsage:
    """Tests for usage tracking in async chat responses."""

    async def test_usage_tokens(self, chat_response):
        """Usage tokens are tracked."""
        mock_client = AsyncMock()
        mock_client.post.return_value = chat_response

        chat = AsyncChatResource(mock_client)
        result = await chat.complete(messages=[{"role": "user", "content": "Hello"}])

        assert result.usage["prompt_tokens"] == 10
        assert result.usage["completion_tokens"] == 20
        assert result.usage["total_tokens"] == 30

    async def test_missing_usage(self):
        """Handle missing usage gracefully."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "choices": [{"message": {"content": "Hi"}, "finish_reason": "stop"}]
        }

        chat = AsyncChatResource(mock_client)
        result = await chat.complete(messages=[{"role": "user", "content": "Hello"}])

        assert result.usage == {}


@pytest.mark.asyncio
class TestAsyncChatResourceStreaming:
    """Tests for async streaming chat completions."""

    async def test_complete_stream_placeholder(self, chat_response):
        """Streaming returns full response for now (placeholder)."""
        mock_client = AsyncMock()
        mock_client.post.return_value = chat_response

        chat = AsyncChatResource(mock_client)
        chunks = []
        async for chunk in chat.complete_stream(
            messages=[{"role": "user", "content": "Hello"}]
        ):
            chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0] == "Olá! Como posso ajudar?"

    async def test_complete_stream_with_model(self, chat_response):
        """Streaming with specific model."""
        mock_client = AsyncMock()
        mock_client.post.return_value = chat_response

        chat = AsyncChatResource(mock_client)
        chunks = []
        async for chunk in chat.complete_stream(
            messages=[{"role": "user", "content": "Hello"}],
            model="claude-opus",
        ):
            chunks.append(chunk)

        assert len(chunks) == 1
