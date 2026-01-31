"""
NTLabs SDK - Async Transcribe Resource Tests
Tests for the AsyncTranscribeResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
import io
from pathlib import Path
from unittest.mock import AsyncMock, mock_open, patch

from ntlabs.resources.async_transcribe import AsyncTranscribeResource
from ntlabs.resources.transcribe import TranscriptionResult, TranscribeModel


@pytest.mark.asyncio
class TestAsyncTranscribeResource:
    """Tests for AsyncTranscribeResource."""

    async def test_initialization(self):
        """AsyncTranscribeResource initializes with client."""
        mock_client = AsyncMock()
        transcribe = AsyncTranscribeResource(mock_client)
        assert transcribe._client == mock_client


@pytest.mark.asyncio
class TestAsyncTranscribeAudio:
    """Tests for async audio transcription."""

    async def test_transcribe_with_bytes(self, transcription_response):
        """Transcribe audio from bytes."""
        mock_client = AsyncMock()
        mock_client.post.return_value = transcription_response

        transcribe = AsyncTranscribeResource(mock_client)
        audio_bytes = b"fake_audio_data"
        result = await transcribe.audio(audio_bytes)

        assert isinstance(result, TranscriptionResult)
        assert result.text == transcription_response["text"]
        assert result.language == "pt"
        assert result.confidence == 0.95
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/transcribe/audio"

    async def test_transcribe_with_path(self, transcription_response, tmp_path):
        """Transcribe audio from file path."""
        mock_client = AsyncMock()
        mock_client.post.return_value = transcription_response

        # Create a temporary file
        audio_file = tmp_path / "audio.mp3"
        audio_file.write_bytes(b"fake_audio_data")

        transcribe = AsyncTranscribeResource(mock_client)
        result = await transcribe.audio(str(audio_file))

        assert isinstance(result, TranscriptionResult)
        mock_client.post.assert_called_once()

    async def test_transcribe_with_file_object(self, transcription_response):
        """Transcribe audio from file object."""
        mock_client = AsyncMock()
        mock_client.post.return_value = transcription_response

        transcribe = AsyncTranscribeResource(mock_client)
        file_obj = io.BytesIO(b"fake_audio_data")
        file_obj.name = "audio.mp3"
        result = await transcribe.audio(file_obj)

        assert isinstance(result, TranscriptionResult)
        mock_client.post.assert_called_once()

    async def test_transcribe_with_options(self, transcription_response):
        """Transcribe with options."""
        mock_client = AsyncMock()
        mock_client.post.return_value = transcription_response

        transcribe = AsyncTranscribeResource(mock_client)
        audio_bytes = b"fake_audio_data"
        result = await transcribe.audio(
            audio_bytes,
            language="en",
            model="whisper-1",
            punctuate=False,
            diarize=True,
            smart_format=False,
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["language"] == "en"
        assert call_args[1]["data"]["model"] == "whisper-1"
        assert call_args[1]["data"]["punctuate"] == "false"
        assert call_args[1]["data"]["diarize"] == "true"
        assert call_args[1]["data"]["smart_format"] == "false"

    async def test_transcribe_default_options(self, transcription_response):
        """Transcribe with default options."""
        mock_client = AsyncMock()
        mock_client.post.return_value = transcription_response

        transcribe = AsyncTranscribeResource(mock_client)
        audio_bytes = b"fake_audio_data"
        result = await transcribe.audio(audio_bytes)

        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["language"] == "pt"
        assert call_args[1]["data"]["punctuate"] == "true"
        assert call_args[1]["data"]["diarize"] == "false"
        assert call_args[1]["data"]["smart_format"] == "true"


@pytest.mark.asyncio
class TestAsyncTranscribeModels:
    """Tests for async transcription models."""

    async def test_get_models(self, transcribe_models_response):
        """Get available models."""
        mock_client = AsyncMock()
        mock_client.get.return_value = transcribe_models_response

        transcribe = AsyncTranscribeResource(mock_client)
        result = await transcribe.get_models()

        assert len(result) == 2
        assert all(isinstance(m, TranscribeModel) for m in result)
        assert result[0].id == "whisper-1"
        assert result[0].price_per_minute_brl == 0.10
        assert result[1].id == "azure-speech"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/transcribe/models"

    async def test_get_models_empty(self):
        """Get models with empty response."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"models": []}

        transcribe = AsyncTranscribeResource(mock_client)
        result = await transcribe.get_models()

        assert len(result) == 0


@pytest.mark.asyncio
class TestAsyncTranscribeHealth:
    """Tests for async transcription health."""

    async def test_health(self):
        """Check transcription health."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"status": "healthy", "queue_size": 0}

        transcribe = AsyncTranscribeResource(mock_client)
        result = await transcribe.health()

        assert result["status"] == "healthy"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/transcribe/health"
