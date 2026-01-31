"""
NTLabs SDK - Saude Resource Tests
Tests for the SaudeResource class (medical AI features).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import io

from ntlabs.resources.saude import (
    MedicalDocument,
    SaudeResource,
    SOAPNote,
    Transcription,
)


class TestTranscription:
    """Tests for Transcription dataclass."""

    def test_create_transcription(self):
        """Create transcription."""
        result = Transcription(
            text="Paciente relata dor de cabeça",
            duration_seconds=30,
            language="pt",
            confidence=0.95,
        )
        assert result.text == "Paciente relata dor de cabeça"
        assert result.duration_seconds == 30


class TestSOAPNote:
    """Tests for SOAPNote dataclass."""

    def test_create_soap(self):
        """Create SOAP note."""
        soap = SOAPNote(
            subjetivo="Paciente relata dor de cabeça há 3 dias",
            objetivo="PA: 120/80, FC: 72bpm",
            avaliacao="Cefaleia tensional",
            plano="Analgésico e repouso",
            cid_sugerido="R51",
            medicamentos=[
                {"nome": "Dipirona", "dosagem": "500mg", "posologia": "6/6h"}
            ],
        )
        assert soap.subjetivo.startswith("Paciente")
        assert soap.cid_sugerido == "R51"


class TestMedicalDocument:
    """Tests for MedicalDocument dataclass."""

    def test_create_document(self):
        """Create medical document."""
        doc = MedicalDocument(
            content="Receituário médico...",
            document_type="receita",
            metadata={"medico": "Dr. João", "crm": "12345-MG"},
        )
        assert doc.document_type == "receita"


class TestSaudeResource:
    """Tests for SaudeResource."""

    def test_initialization(self, mock_client):
        """SaudeResource initializes with client."""
        saude = SaudeResource(mock_client)
        assert saude._client == mock_client

    def test_transcribe(self, mock_client, mock_response):
        """Transcribe medical consultation."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "text": "Paciente relata dor no peito há 2 dias",
                "duration_seconds": 120,
                "language": "pt",
                "confidence": 0.92,
            }
        )

        audio = io.BytesIO(b"fake audio")
        result = mock_client.saude.transcribe(audio)

        assert isinstance(result, Transcription)
        assert "dor no peito" in result.text

    def test_transcribe_with_specialty(self, mock_client, mock_response):
        """Transcribe with medical specialty."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "text": "Exame de ECG normal",
                "duration_seconds": 60,
                "language": "pt",
                "confidence": 0.95,
            }
        )

        audio = io.BytesIO(b"fake audio")
        result = mock_client.saude.transcribe(
            audio,
            especialidade="cardiologia",
        )

        assert isinstance(result, Transcription)

    def test_generate_soap(self, mock_client, mock_response):
        """Generate SOAP note."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "subjetivo": "Paciente refere dor torácica",
                "objetivo": "PA: 130/85, FC: 88bpm",
                "avaliacao": "Suspeita de angina",
                "plano": "Solicitar ECG e enzimas cardíacas",
                "cid_sugerido": "I20.9",
                "medicamentos": [],
            }
        )

        result = mock_client.saude.generate_soap(
            transcription="Paciente relata dor no peito ao caminhar",
        )

        assert isinstance(result, SOAPNote)
        assert result.cid_sugerido == "I20.9"

    def test_generate_soap_with_patient(self, mock_client, mock_response):
        """Generate SOAP with patient info."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "subjetivo": "Idoso com dor torácica",
                "objetivo": "PA elevada",
                "avaliacao": "HAS + angina",
                "plano": "Cardiologista",
            }
        )

        result = mock_client.saude.generate_soap(
            transcription="Dor no peito",
            paciente={"idade": 65, "sexo": "M", "historico": ["HAS", "DM"]},
        )

        assert isinstance(result, SOAPNote)

    def test_generate_soap_with_history(self, mock_client, mock_response):
        """Generate SOAP with consultation history."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "subjetivo": "Retorno - melhora parcial",
                "objetivo": "PA normalizada",
                "avaliacao": "HAS controlada",
                "plano": "Manter medicação",
            }
        )

        result = mock_client.saude.generate_soap(
            transcription="Paciente retorna para reavaliação",
            historico=["Consulta anterior: HAS"],
        )

        assert isinstance(result, SOAPNote)

    def test_generate_receita(self, mock_client, mock_response):
        """Generate prescription."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "content": "RECEITUÁRIO\n\n1. Dipirona 500mg...",
                "metadata": {"validade": "30 dias"},
            }
        )

        result = mock_client.saude.generate_receita(
            medicamentos=[
                {"nome": "Dipirona", "dosagem": "500mg", "posologia": "6/6h", "dias": 5}
            ],
            paciente={"nome": "João Silva", "cpf": "123.456.789-00"},
            medico={"nome": "Dr. Pedro", "crm": "12345-MG", "especialidade": "Clínica"},
        )

        assert isinstance(result, MedicalDocument)
        assert result.document_type == "receita"

    def test_generate_atestado(self, mock_client, mock_response):
        """Generate medical certificate."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "content": "ATESTADO MÉDICO\n\nAtesto para os devidos fins...",
                "metadata": {"cid": "J06"},
            }
        )

        result = mock_client.saude.generate_atestado(
            dias=3,
            motivo="Síndrome gripal",
            paciente={"nome": "Maria Silva"},
            medico={"nome": "Dra. Ana", "crm": "54321-SP"},
            cid="J06",
        )

        assert isinstance(result, MedicalDocument)
        assert result.document_type == "atestado"

    def test_generate_atestado_without_cid(self, mock_client, mock_response):
        """Generate certificate without CID."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "content": "ATESTADO MÉDICO...",
                "metadata": {},
            }
        )

        result = mock_client.saude.generate_atestado(
            dias=1,
            motivo="Consulta médica",
            paciente={"nome": "João"},
            medico={"nome": "Dr. Pedro", "crm": "12345-MG"},
        )

        assert isinstance(result, MedicalDocument)

    def test_suggest_cid(self, mock_client, mock_response):
        """Suggest CID codes."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "sugestoes": [
                    {"codigo": "R51", "descricao": "Cefaleia", "confianca": 0.92},
                    {"codigo": "G43.9", "descricao": "Enxaqueca", "confianca": 0.75},
                ]
            }
        )

        result = mock_client.saude.suggest_cid(
            sintomas="Dor de cabeça intensa, náusea, fotofobia",
        )

        assert len(result) == 2
        assert result[0]["codigo"] == "R51"

    def test_suggest_cid_with_history(self, mock_client, mock_response):
        """Suggest CID with patient history."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "sugestoes": [
                    {"codigo": "I10", "descricao": "HAS", "confianca": 0.95},
                ]
            }
        )

        result = mock_client.saude.suggest_cid(
            sintomas="Pressão alta, tontura",
            historico="Paciente com histórico familiar de HAS",
        )

        assert len(result) == 1

    def test_check_interacao(self, mock_client, mock_response):
        """Check drug interactions."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "interacoes": [
                    {
                        "par": ["Varfarina", "AAS"],
                        "severidade": "alta",
                        "descricao": "Aumenta risco de sangramento",
                    }
                ],
                "total": 1,
            }
        )

        result = mock_client.saude.check_interacao(
            medicamentos=["Varfarina", "AAS", "Omeprazol"],
        )

        assert "interacoes" in result
        assert len(result["interacoes"]) == 1
        assert result["interacoes"][0]["severidade"] == "alta"

    def test_check_interacao_no_interactions(self, mock_client, mock_response):
        """Check medications with no interactions."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "interacoes": [],
                "total": 0,
            }
        )

        result = mock_client.saude.check_interacao(
            medicamentos=["Dipirona", "Vitamina C"],
        )

        assert result["total"] == 0

    def test_empty_response_handling(self, mock_client, mock_response):
        """Handle empty responses gracefully."""
        mock_client._mock_http.request.return_value = mock_response({})

        # Transcription
        audio = io.BytesIO(b"fake audio")
        result = mock_client.saude.transcribe(audio)
        assert result.text == ""
        assert result.duration_seconds == 0

        # SOAP
        result = mock_client.saude.generate_soap(transcription="test")
        assert result.subjetivo == ""

        # Suggest CID
        result = mock_client.saude.suggest_cid(sintomas="test")
        assert result == []
