"""
NTLabs SDK - Transcribe Resource Tests
Tests for the TranscribeResource class (audio transcription).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import io
from pathlib import Path
from unittest.mock import mock_open, patch

from ntlabs.resources.transcribe import (
    TranscribeModel,
    TranscribeResource,
    TranscriptionResult,
)


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""

    def test_create_result(self, transcription_response):
        """Create transcription result."""
        result = TranscriptionResult(
            text=transcription_response["text"],
            duration_seconds=transcription_response["duration_seconds"],
            language=transcription_response["language"],
            confidence=transcription_response["confidence"],
            words=transcription_response["words"],
            latency_ms=transcription_response["latency_ms"],
            cost_brl=transcription_response["cost_brl"],
        )
        assert result.text == "Olá, bom dia. Como você está?"
        assert result.duration_seconds == 3.5
        assert result.confidence == 0.95


class TestTranscribeModel:
    """Tests for TranscribeModel dataclass."""

    def test_create_model(self):
        """Create transcribe model."""
        model = TranscribeModel(
            id="deepgram-nova-2",
            name="Deepgram Nova 2",
            provider="deepgram",
            description="High accuracy transcription",
            languages=["pt", "en", "es"],
            price_per_minute_brl=0.05,
            available=True,
        )
        assert model.id == "deepgram-nova-2"
        assert "pt" in model.languages
        assert model.available is True


class TestTranscribeResource:
    """Tests for TranscribeResource."""

    def test_initialization(self, mock_client):
        """TranscribeResource initializes with client."""
        transcribe = TranscribeResource(mock_client)
        assert transcribe._client == mock_client

    def test_audio_from_bytes(self, mock_client, mock_response, transcription_response):
        """Transcribe audio from bytes."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        audio_bytes = b"fake audio content"
        result = mock_client.transcribe.audio(audio_bytes)

        assert isinstance(result, TranscriptionResult)
        assert result.text == "Olá, bom dia. Como você está?"

    def test_audio_from_file_object(
        self, mock_client, mock_response, transcription_response
    ):
        """Transcribe audio from file object."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        file_obj = io.BytesIO(b"fake audio content")
        result = mock_client.transcribe.audio(file_obj)

        assert isinstance(result, TranscriptionResult)
        assert result.language == "pt"

    def test_audio_from_path_string(
        self, mock_client, mock_response, transcription_response
    ):
        """Transcribe audio from path string."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        with patch("builtins.open", mock_open(read_data=b"fake audio")):
            with patch.object(Path, "exists", return_value=True):
                result = mock_client.transcribe.audio("/path/to/audio.mp3")

        assert isinstance(result, TranscriptionResult)

    def test_audio_from_path_object(
        self, mock_client, mock_response, transcription_response
    ):
        """Transcribe audio from Path object."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        with patch("builtins.open", mock_open(read_data=b"fake audio")):
            with patch.object(Path, "exists", return_value=True):
                result = mock_client.transcribe.audio(Path("/path/to/audio.mp3"))

        assert isinstance(result, TranscriptionResult)

    def test_audio_with_language(
        self, mock_client, mock_response, transcription_response
    ):
        """Transcribe audio with specific language."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        result = mock_client.transcribe.audio(
            b"fake audio",
            language="en",
        )

        assert isinstance(result, TranscriptionResult)

    def test_audio_with_model(self, mock_client, mock_response, transcription_response):
        """Transcribe audio with specific model."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        result = mock_client.transcribe.audio(
            b"fake audio",
            model="groq-whisper",
        )

        assert isinstance(result, TranscriptionResult)

    def test_audio_with_options(
        self, mock_client, mock_response, transcription_response
    ):
        """Transcribe audio with all options."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        result = mock_client.transcribe.audio(
            b"fake audio",
            language="pt",
            model="deepgram-nova-2",
            punctuate=True,
            diarize=True,
            smart_format=True,
        )

        assert isinstance(result, TranscriptionResult)

    def test_audio_word_timestamps(
        self, mock_client, mock_response, transcription_response
    ):
        """Transcription includes word timestamps."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        result = mock_client.transcribe.audio(b"fake audio")

        assert result.words is not None
        assert len(result.words) == 3
        assert result.words[0]["word"] == "Olá"
        assert result.words[0]["start"] == 0.0

    def test_get_models(self, mock_client, mock_response):
        """Get available transcription models."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "models": [
                    {
                        "id": "deepgram-nova-2",
                        "name": "Deepgram Nova 2",
                        "provider": "deepgram",
                        "description": "High accuracy",
                        "languages": ["pt", "en"],
                        "price_per_minute_brl": 0.05,
                        "available": True,
                    },
                    {
                        "id": "groq-whisper",
                        "name": "Groq Whisper",
                        "provider": "groq",
                        "description": "Fast transcription",
                        "languages": ["pt", "en", "es"],
                        "price_per_minute_brl": 0.03,
                        "available": True,
                    },
                ]
            }
        )

        models = mock_client.transcribe.get_models()

        assert len(models) == 2
        assert all(isinstance(m, TranscribeModel) for m in models)
        assert models[0].id == "deepgram-nova-2"

    def test_get_models_empty(self, mock_client, mock_response):
        """Handle empty models list."""
        mock_client._mock_http.request.return_value = mock_response({})

        models = mock_client.transcribe.get_models()
        assert models == []

    def test_health(self, mock_client, mock_response):
        """Check transcription service health."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "status": "healthy",
                "providers": {
                    "deepgram": "up",
                    "groq": "up",
                },
            }
        )

        health = mock_client.transcribe.health()

        assert health["status"] == "healthy"

    def test_audio_empty_response(self, mock_client, mock_response):
        """Handle empty response gracefully."""
        mock_client._mock_http.request.return_value = mock_response({})

        result = mock_client.transcribe.audio(b"fake audio")

        assert result.text == ""
        assert result.duration_seconds == 0
        assert result.confidence == 0
        assert result.words is None

    def test_audio_file_object_name(
        self, mock_client, mock_response, transcription_response
    ):
        """Uses file object name if available."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        file_obj = io.BytesIO(b"fake audio")
        file_obj.name = "recording.webm"
        result = mock_client.transcribe.audio(file_obj)

        assert isinstance(result, TranscriptionResult)

    def test_audio_punctuate_false(
        self, mock_client, mock_response, transcription_response
    ):
        """Transcribe without punctuation."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        result = mock_client.transcribe.audio(
            b"fake audio",
            punctuate=False,
        )

        assert isinstance(result, TranscriptionResult)

    def test_audio_diarize(self, mock_client, mock_response, transcription_response):
        """Transcribe with speaker diarization."""
        mock_client._mock_http.request.return_value = mock_response(
            transcription_response
        )

        result = mock_client.transcribe.audio(
            b"fake audio",
            diarize=True,
        )

        assert isinstance(result, TranscriptionResult)
