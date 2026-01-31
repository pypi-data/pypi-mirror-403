"""
Neural LAB - AI Solutions Platform
Saúde Resource - Medical AI features (Hipocrates integration).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from dataclasses import dataclass
from typing import Any, BinaryIO

from ..base import DataclassMixin


@dataclass
class Transcription(DataclassMixin):
    """Audio transcription result."""

    text: str
    duration_seconds: int
    language: str
    confidence: float


@dataclass
class SOAPNote(DataclassMixin):
    """SOAP note structure."""

    subjetivo: str
    objetivo: str
    avaliacao: str
    plano: str
    cid_sugerido: str | None = None
    medicamentos: list[dict] | None = None


@dataclass
class MedicalDocument(DataclassMixin):
    """Generated medical document."""

    content: str
    document_type: str
    metadata: dict[str, Any]


class SaudeResource:
    """
    Medical AI resource for Hipocrates integration.

    Usage:
        # Transcribe consultation
        result = client.saude.transcribe(audio_file)

        # Generate SOAP note
        soap = client.saude.generate_soap(result.text, paciente={...})

        # Generate prescription
        receita = client.saude.generate_receita(medicamentos=[...])
    """

    def __init__(self, client):
        self._client = client

    def transcribe(
        self,
        audio: BinaryIO,
        language: str = "pt",
        especialidade: str | None = None,
        **kwargs,
    ) -> Transcription:
        """
        Transcribe audio to text.

        Args:
            audio: Audio file (mp3, wav, m4a, webm)
            language: Language code (pt, en)
            especialidade: Medical specialty for better accuracy
            **kwargs: Additional parameters

        Returns:
            Transcription result
        """
        files = {"file": audio}
        data = {"language": language}
        if especialidade:
            data["especialidade"] = especialidade

        response = self._client.post(
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

    def generate_soap(
        self,
        transcription: str,
        paciente: dict | None = None,
        historico: list[str] | None = None,
        **kwargs,
    ) -> SOAPNote:
        """
        Generate SOAP note from transcription.

        Args:
            transcription: Consultation transcription text
            paciente: Patient info (idade, sexo, historico)
            historico: Previous consultations context
            **kwargs: Additional parameters

        Returns:
            SOAP note structure
        """
        response = self._client.post(
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

    def generate_receita(
        self,
        medicamentos: list[dict],
        paciente: dict,
        medico: dict,
        **kwargs,
    ) -> MedicalDocument:
        """
        Generate prescription document.

        Args:
            medicamentos: List of medications with dosage
            paciente: Patient info
            medico: Doctor info (nome, crm, especialidade)
            **kwargs: Additional parameters

        Returns:
            Generated prescription
        """
        response = self._client.post(
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

    def generate_atestado(
        self,
        dias: int,
        motivo: str,
        paciente: dict,
        medico: dict,
        cid: str | None = None,
        **kwargs,
    ) -> MedicalDocument:
        """
        Generate medical certificate.

        Args:
            dias: Number of days
            motivo: Reason for certificate
            paciente: Patient info
            medico: Doctor info
            cid: CID code (optional)
            **kwargs: Additional parameters

        Returns:
            Generated certificate
        """
        response = self._client.post(
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

    def suggest_cid(
        self,
        sintomas: str,
        historico: str | None = None,
        **kwargs,
    ) -> list[dict[str, str]]:
        """
        Suggest CID codes based on symptoms.

        Args:
            sintomas: Description of symptoms
            historico: Patient history
            **kwargs: Additional parameters

        Returns:
            List of CID suggestions with confidence
        """
        response = self._client.post(
            "/v1/saude/cid/suggest",
            json={
                "sintomas": sintomas,
                "historico": historico,
                **kwargs,
            },
        )

        return response.get("sugestoes", [])

    def check_interacao(
        self,
        medicamentos: list[str],
        **kwargs,
    ) -> dict[str, Any]:
        """
        Check drug interactions.

        Args:
            medicamentos: List of medication names
            **kwargs: Additional parameters

        Returns:
            Interaction analysis
        """
        response = self._client.post(
            "/v1/saude/interacao/check",
            json={"medicamentos": medicamentos, **kwargs},
        )

        return response
