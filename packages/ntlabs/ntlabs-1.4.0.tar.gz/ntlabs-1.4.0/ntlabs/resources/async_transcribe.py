"""
Neural LAB - AI Solutions Platform
Async Transcribe Resource.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from pathlib import Path
from typing import Any, BinaryIO

from .transcribe import TranscribeModel, TranscriptionResult


class AsyncTranscribeResource:
    """Async transcription resource for audio-to-text."""

    def __init__(self, client):
        self._client = client

    async def audio(
        self,
        file: str | Path | BinaryIO | bytes,
        language: str = "pt",
        model: str | None = None,
        punctuate: bool = True,
        diarize: bool = False,
        smart_format: bool = True,
    ) -> TranscriptionResult:
        """Transcribe audio file to text."""
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
            files = {"file": (filename, file_obj)}
            data = {
                "language": language,
                "punctuate": str(punctuate).lower(),
                "diarize": str(diarize).lower(),
                "smart_format": str(smart_format).lower(),
            }
            if model:
                data["model"] = model

            response = await self._client.post(
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

    async def get_models(self) -> list[TranscribeModel]:
        """Get available transcription models."""
        response = await self._client.get("/v1/transcribe/models")
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

    async def health(self) -> dict[str, Any]:
        """Check transcription service health."""
        return await self._client.get("/v1/transcribe/health")
