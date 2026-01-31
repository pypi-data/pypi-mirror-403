"""
Neural LAB - AI Solutions Platform
Transcribe Resource - Audio transcription via Deepgram/Groq.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

from ..base import DataclassMixin


@dataclass
class TranscriptionResult(DataclassMixin):
    """Audio transcription result."""

    text: str
    duration_seconds: float
    language: str
    confidence: float
    words: list[dict[str, Any]] | None
    latency_ms: int
    cost_brl: float


@dataclass
class TranscribeModel(DataclassMixin):
    """Transcription model info."""

    id: str
    name: str
    provider: str
    description: str
    languages: list[str]
    price_per_minute_brl: float
    available: bool


class TranscribeResource:
    """
    Transcription resource for audio-to-text via Deepgram/Groq.

    Usage:
        # From file path
        result = client.transcribe.audio("/path/to/audio.mp3")
        print(result.text)

        # From bytes
        with open("audio.mp3", "rb") as f:
            result = client.transcribe.audio(f)
    """

    def __init__(self, client):
        self._client = client

    def audio(
        self,
        file: str | Path | BinaryIO | bytes,
        language: str = "pt",
        model: str | None = None,
        punctuate: bool = True,
        diarize: bool = False,
        smart_format: bool = True,
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text.

        Args:
            file: Audio file (path, file object, or bytes)
            language: Language code (pt, en, es)
            model: Model to use (deepgram-nova-2, groq-whisper)
            punctuate: Add punctuation
            diarize: Speaker diarization
            smart_format: Smart formatting

        Returns:
            TranscriptionResult with transcribed text
        """
        # Prepare file
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            file_obj = open(file_path, "rb")
            filename = file_path.name
            close_file = True
        elif isinstance(file, bytes):
            import io

            file_obj = io.BytesIO(file)
            filename = "audio.mp3"
            close_file = True
        else:
            file_obj = file
            filename = getattr(file, "name", "audio.mp3")
            close_file = False

        try:
            # Prepare form data
            files = {"file": (filename, file_obj)}
            data = {
                "language": language,
                "punctuate": str(punctuate).lower(),
                "diarize": str(diarize).lower(),
                "smart_format": str(smart_format).lower(),
            }
            if model:
                data["model"] = model

            response = self._client.post(
                "/v1/transcribe/audio",
                files=files,
                data=data,
            )

            return TranscriptionResult(
                text=response.get("text", ""),
                duration_seconds=response.get("duration_seconds", 0),
                language=response.get("language", language),
                confidence=response.get("confidence", 0),
                words=response.get("words"),
                latency_ms=response.get("latency_ms", 0),
                cost_brl=response.get("cost_brl", 0),
            )

        finally:
            if close_file:
                file_obj.close()

    def get_models(self) -> list[TranscribeModel]:
        """
        Get available transcription models.

        Returns:
            List of available models
        """
        response = self._client.get("/v1/transcribe/models")

        return [
            TranscribeModel(
                id=m.get("id", ""),
                name=m.get("name", ""),
                provider=m.get("provider", ""),
                description=m.get("description", ""),
                languages=m.get("languages", []),
                price_per_minute_brl=m.get("price_per_minute_brl", 0),
                available=m.get("available", False),
            )
            for m in response.get("models", [])
        ]

    def health(self) -> dict[str, Any]:
        """
        Check transcription service health.

        Returns:
            Health status
        """
        return self._client.get("/v1/transcribe/health")
