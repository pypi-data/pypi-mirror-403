"""
NTLabs SDK - Chat Resource Tests
Tests for the ChatResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

from ntlabs.resources.chat import ChatCompletion, ChatMessage, ChatResource


class TestChatMessage:
    """Tests for ChatMessage dataclass."""

    def test_create_user_message(self):
        """Create user message."""
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_create_assistant_message(self):
        """Create assistant message."""
        msg = ChatMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"

    def test_create_system_message(self):
        """Create system message."""
        msg = ChatMessage(role="system", content="You are a helpful assistant.")
        assert msg.role == "system"


class TestChatCompletion:
    """Tests for ChatCompletion dataclass."""

    def test_create_completion(self):
        """Create chat completion."""
        completion = ChatCompletion(
            id="chat-123",
            content="Hello! How can I help?",
            model="maritaca-sabia-3",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            finish_reason="stop",
        )
        assert completion.id == "chat-123"
        assert completion.content == "Hello! How can I help?"
        assert completion.model == "maritaca-sabia-3"
        assert completion.usage["total_tokens"] == 30
        assert completion.finish_reason == "stop"


class TestChatResource:
    """Tests for ChatResource."""

    def test_initialization(self, mock_client):
        """ChatResource initializes with client."""
        chat = ChatResource(mock_client)
        assert chat._client == mock_client

    def test_complete_basic(self, mock_client, mock_response, chat_response):
        """Basic chat completion."""
        mock_client._mock_http.request.return_value = mock_response(chat_response)

        result = mock_client.chat.complete(
            messages=[{"role": "user", "content": "Olá!"}]
        )

        assert isinstance(result, ChatCompletion)
        assert result.content == "Olá! Como posso ajudar?"
        assert result.model == "maritaca-sabia-3"

    def test_complete_with_model(self, mock_client, mock_response, chat_response):
        """Chat completion with specific model."""
        mock_client._mock_http.request.return_value = mock_response(chat_response)

        result = mock_client.chat.complete(
            messages=[{"role": "user", "content": "Hello"}],
            model="claude-sonnet",
        )

        assert isinstance(result, ChatCompletion)
        # Verify the request was made with correct model
        call_kwargs = mock_client._mock_http.request.call_args
        assert "claude-sonnet" in str(call_kwargs)

    def test_complete_with_system_prompt(
        self, mock_client, mock_response, chat_response
    ):
        """Chat completion with system prompt."""
        mock_client._mock_http.request.return_value = mock_response(chat_response)

        result = mock_client.chat.complete(
            messages=[{"role": "user", "content": "What is Python?"}],
            system="You are a programming tutor.",
        )

        assert isinstance(result, ChatCompletion)

    def test_complete_with_parameters(self, mock_client, mock_response, chat_response):
        """Chat completion with all parameters."""
        mock_client._mock_http.request.return_value = mock_response(chat_response)

        result = mock_client.chat.complete(
            messages=[{"role": "user", "content": "Tell me a story"}],
            model="maritaca-sabia-3",
            max_tokens=2048,
            temperature=0.9,
        )

        assert isinstance(result, ChatCompletion)

    def test_complete_multiple_messages(
        self, mock_client, mock_response, chat_response
    ):
        """Chat completion with conversation history."""
        mock_client._mock_http.request.return_value = mock_response(chat_response)

        messages = [
            {"role": "user", "content": "My name is João"},
            {"role": "assistant", "content": "Nice to meet you, João!"},
            {"role": "user", "content": "What is my name?"},
        ]

        result = mock_client.chat.complete(messages=messages)
        assert isinstance(result, ChatCompletion)

    def test_complete_empty_response(self, mock_client, mock_response):
        """Handle empty response gracefully."""
        mock_client._mock_http.request.return_value = mock_response({})

        result = mock_client.chat.complete(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert result.id == ""
        assert result.content == ""
        assert result.finish_reason == "stop"

    def test_complete_stream_placeholder(
        self, mock_client, mock_response, chat_response
    ):
        """Streaming returns full response for now."""
        mock_client._mock_http.request.return_value = mock_response(chat_response)

        chunks = list(
            mock_client.chat.complete_stream(
                messages=[{"role": "user", "content": "Hello"}]
            )
        )

        assert len(chunks) == 1
        assert chunks[0] == "Olá! Como posso ajudar?"

    def test_complete_with_kwargs(self, mock_client, mock_response, chat_response):
        """Chat completion with extra kwargs."""
        mock_client._mock_http.request.return_value = mock_response(chat_response)

        result = mock_client.chat.complete(
            messages=[{"role": "user", "content": "Hello"}],
            top_p=0.95,
            presence_penalty=0.5,
        )

        assert isinstance(result, ChatCompletion)


class TestChatResourceUsage:
    """Tests for usage tracking in chat responses."""

    def test_usage_tokens(self, mock_client, mock_response, chat_response):
        """Usage tokens are tracked."""
        mock_client._mock_http.request.return_value = mock_response(chat_response)

        result = mock_client.chat.complete(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert result.usage["prompt_tokens"] == 10
        assert result.usage["completion_tokens"] == 20
        assert result.usage["total_tokens"] == 30

    def test_missing_usage(self, mock_client, mock_response):
        """Handle missing usage gracefully."""
        mock_client._mock_http.request.return_value = mock_response(
            {"choices": [{"message": {"content": "Hi"}, "finish_reason": "stop"}]}
        )

        result = mock_client.chat.complete(
            messages=[{"role": "user", "content": "Hello"}]
        )

        assert result.usage == {}
