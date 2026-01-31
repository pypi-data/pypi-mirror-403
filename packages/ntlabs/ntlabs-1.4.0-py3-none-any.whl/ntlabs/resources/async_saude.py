"""
Neural LAB - AI Solutions Platform
Async Saúde Resource - Medical AI features.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from typing import Any, BinaryIO

from .saude import MedicalDocument, SOAPNote, Transcription


class AsyncSaudeResource:
    """Async medical AI resource for Hipocrates integration."""

    def __init__(self, client):
        self._client = client

    async def transcribe(
        self,
        audio: BinaryIO,
        language: str = "pt",
        especialidade: str | None = None,
        **kwargs,
    ) -> Transcription:
        """Transcribe medical consultation audio."""
        files = {"file": audio}
        data = {"language": language}
        if especialidade:
            data["especialidade"] = especialidade

        response = await self._client.post(
            "/v1/saude/transcribe/consulta",
            files=files,
            data=data,
        )

        return Transcription(
            text=response.get("text", ""),
            duration_seconds=response.get("duration_seconds", 0),
            language=response.get("language", language),
            confidence=response.get("confidence", 0.0),
        )

    async def generate_soap(
        self,
        transcription: str,
        paciente: dict | None = None,
        historico: list[str] | None = None,
        **kwargs,
    ) -> SOAPNote:
        """Generate SOAP note from transcription."""
        response = await self._client.post(
            "/v1/saude/soap/generate",
            json={
                "transcription": transcription,
                "paciente": paciente or {},
                "historico": historico or [],
                **kwargs,
            },
        )

        return SOAPNote(
            subjetivo=response.get("subjetivo", ""),
            objetivo=response.get("objetivo", ""),
            avaliacao=response.get("avaliacao", ""),
            plano=response.get("plano", ""),
            cid_sugerido=response.get("cid_sugerido"),
            medicamentos=response.get("medicamentos"),
        )

    async def generate_receita(
        self,
        medicamentos: list[dict],
        paciente: dict,
        medico: dict,
        **kwargs,
    ) -> MedicalDocument:
        """Generate prescription document."""
        response = await self._client.post(
            "/v1/saude/generate/receita",
            json={
                "medicamentos": medicamentos,
                "paciente": paciente,
                "medico": medico,
                **kwargs,
            },
        )

        return MedicalDocument(
            content=response.get("content", ""),
            document_type="receita",
            metadata=response.get("metadata", {}),
        )

    async def generate_atestado(
        self,
        dias: int,
        motivo: str,
        paciente: dict,
        medico: dict,
        cid: str | None = None,
        **kwargs,
    ) -> MedicalDocument:
        """Generate medical certificate."""
        response = await self._client.post(
            "/v1/saude/generate/atestado",
            json={
                "dias": dias,
                "motivo": motivo,
                "paciente": paciente,
                "medico": medico,
                "cid": cid,
                **kwargs,
            },
        )

        return MedicalDocument(
            content=response.get("content", ""),
            document_type="atestado",
            metadata=response.get("metadata", {}),
        )

    async def suggest_cid(
        self,
        sintomas: str,
        historico: str | None = None,
        **kwargs,
    ) -> list[dict[str, str]]:
        """Suggest CID codes based on symptoms."""
        response = await self._client.post(
            "/v1/saude/cid/suggest",
            json={
                "sintomas": sintomas,
                "historico": historico,
                **kwargs,
            },
        )
        return response.get("sugestoes", [])

    async def check_interacao(
        self,
        medicamentos: list[str],
        **kwargs,
    ) -> dict[str, Any]:
        """Check drug interactions."""
        response = await self._client.post(
            "/v1/saude/interacao/check",
            json={"medicamentos": medicamentos, **kwargs},
        )
        return response
