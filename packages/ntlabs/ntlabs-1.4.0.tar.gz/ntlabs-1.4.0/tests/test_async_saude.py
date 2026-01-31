"""
NTLabs SDK - Async Saúde Resource Tests
Tests for the AsyncSaudeResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
import io
from unittest.mock import AsyncMock

from ntlabs.resources.async_saude import AsyncSaudeResource
from ntlabs.resources.saude import Transcription, SOAPNote, MedicalDocument


@pytest.mark.asyncio
class TestAsyncSaudeResource:
    """Tests for AsyncSaudeResource."""

    async def test_initialization(self):
        """AsyncSaudeResource initializes with client."""
        mock_client = AsyncMock()
        saude = AsyncSaudeResource(mock_client)
        assert saude._client == mock_client


@pytest.mark.asyncio
class TestAsyncSaudeTranscription:
    """Tests for async transcription."""

    async def test_transcribe(self, saude_transcription_response):
        """Transcribe medical audio."""
        mock_client = AsyncMock()
        mock_client.post.return_value = saude_transcription_response

        saude = AsyncSaudeResource(mock_client)
        audio = io.BytesIO(b"fake_audio_data")
        result = await saude.transcribe(audio)

        assert isinstance(result, Transcription)
        assert result.text == saude_transcription_response["text"]
        assert result.language == "pt"
        assert result.confidence == 0.92
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/saude/transcribe/consulta"

    async def test_transcribe_with_especialidade(self, saude_transcription_response):
        """Transcribe with specialty."""
        mock_client = AsyncMock()
        mock_client.post.return_value = saude_transcription_response

        saude = AsyncSaudeResource(mock_client)
        audio = io.BytesIO(b"fake_audio_data")
        result = await saude.transcribe(audio, especialidade="cardiologia")

        call_args = mock_client.post.call_args
        assert call_args[1]["data"]["especialidade"] == "cardiologia"


@pytest.mark.asyncio
class TestAsyncSaudeSOAP:
    """Tests for async SOAP note generation."""

    async def test_generate_soap(self, soap_note_response):
        """Generate SOAP note."""
        mock_client = AsyncMock()
        mock_client.post.return_value = soap_note_response

        saude = AsyncSaudeResource(mock_client)
        result = await saude.generate_soap(
            transcription="Paciente relata dor de cabeça...",
        )

        assert isinstance(result, SOAPNote)
        assert result.subjetivo == soap_note_response["subjetivo"]
        assert result.objetivo == soap_note_response["objetivo"]
        assert result.avaliacao == soap_note_response["avaliacao"]
        assert result.plano == soap_note_response["plano"]
        assert result.cid_sugerido == "G44.2"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/saude/soap/generate"

    async def test_generate_soap_with_paciente(self, soap_note_response):
        """Generate SOAP with patient info."""
        mock_client = AsyncMock()
        mock_client.post.return_value = soap_note_response

        saude = AsyncSaudeResource(mock_client)
        paciente = {"nome": "João Silva", "idade": 35, "sexo": "M"}
        result = await saude.generate_soap(
            transcription="Paciente relata...",
            paciente=paciente,
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["paciente"] == paciente

    async def test_generate_soap_with_historico(self, soap_note_response):
        """Generate SOAP with history."""
        mock_client = AsyncMock()
        mock_client.post.return_value = soap_note_response

        saude = AsyncSaudeResource(mock_client)
        historico = ["Hipertensão", "Diabetes tipo 2"]
        result = await saude.generate_soap(
            transcription="Paciente relata...",
            historico=historico,
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["historico"] == historico


@pytest.mark.asyncio
class TestAsyncSaudeDocuments:
    """Tests for async document generation."""

    async def test_generate_receita(self):
        """Generate prescription."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "content": "RECEITUÁRIO...",
            "metadata": {"doctor": "Dr. João", "date": "2026-01-27"},
        }

        saude = AsyncSaudeResource(mock_client)
        result = await saude.generate_receita(
            medicamentos=[{"nome": "Paracetamol", "dosagem": "500mg"}],
            paciente={"nome": "Maria", "cpf": "12345678909"},
            medico={"nome": "Dr. João", "crm": "12345"},
        )

        assert isinstance(result, MedicalDocument)
        assert result.content == "RECEITUÁRIO..."
        assert result.document_type == "receita"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/saude/generate/receita"

    async def test_generate_atestado(self):
        """Generate medical certificate."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "content": "ATESTADO MÉDICO...",
            "metadata": {"dias": 3},
        }

        saude = AsyncSaudeResource(mock_client)
        result = await saude.generate_atestado(
            dias=3,
            motivo="Gripe",
            paciente={"nome": "Maria", "cpf": "12345678909"},
            medico={"nome": "Dr. João", "crm": "12345"},
            cid="J11",
        )

        assert isinstance(result, MedicalDocument)
        assert result.content == "ATESTADO MÉDICO..."
        assert result.document_type == "atestado"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/saude/generate/atestado"
        assert call_args[1]["json"]["dias"] == 3
        assert call_args[1]["json"]["motivo"] == "Gripe"
        assert call_args[1]["json"]["cid"] == "J11"


@pytest.mark.asyncio
class TestAsyncSaudeClinical:
    """Tests for async clinical tools."""

    async def test_suggest_cid(self):
        """Suggest CID codes."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "sugestoes": [
                {"codigo": "G44.2", "nome": "Cefaleia tensional", "probabilidade": 0.85},
                {"codigo": "G43.9", "nome": "Enxaqueca", "probabilidade": 0.60},
            ]
        }

        saude = AsyncSaudeResource(mock_client)
        result = await saude.suggest_cid(
            sintomas="Dor de cabeça, sensibilidade à luz",
        )

        assert len(result) == 2
        assert result[0]["codigo"] == "G44.2"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/saude/cid/suggest"

    async def test_suggest_cid_with_historico(self):
        """Suggest CID with history."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"sugestoes": []}

        saude = AsyncSaudeResource(mock_client)
        await saude.suggest_cid(
            sintomas="Dor de cabeça",
            historico="Histórico de enxaqueca",
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["historico"] == "Histórico de enxaqueca"

    async def test_check_interacao(self):
        """Check drug interactions."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "interacoes": [
                {"medicamento1": "Warfarina", "medicamento2": "AAS", "severidade": "alta"},
            ],
            "total": 1,
        }

        saude = AsyncSaudeResource(mock_client)
        result = await saude.check_interacao(["Warfarina", "AAS", "Paracetamol"])

        assert "interacoes" in result
        assert len(result["interacoes"]) == 1
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/saude/interacao/check"
        assert call_args[1]["json"]["medicamentos"] == ["Warfarina", "AAS", "Paracetamol"]
