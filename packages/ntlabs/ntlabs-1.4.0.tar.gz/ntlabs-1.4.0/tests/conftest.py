"""
NTLabs SDK - Test Configuration
Shared fixtures and mocks for all tests.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# =============================================================================
# API Response Fixtures
# =============================================================================


@pytest.fixture
def chat_response() -> dict[str, Any]:
    """Mock chat completion response."""
    return {
        "id": "chat-123",
        "choices": [
            {
                "message": {"content": "Olá! Como posso ajudar?"},
                "finish_reason": "stop",
            }
        ],
        "model": "maritaca-sabia-3",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
    }


@pytest.fixture
def email_response() -> dict[str, Any]:
    """Mock email send response."""
    return {
        "id": "email-456",
        "status": "sent",
        "latency_ms": 150,
        "cost_brl": 0.001,
    }


@pytest.fixture
def cnpj_response() -> dict[str, Any]:
    """Mock CNPJ lookup response."""
    return {
        "cnpj": "12345678000190",
        "razao_social": "EMPRESA TESTE LTDA",
        "nome_fantasia": "Empresa Teste",
        "situacao": "ATIVA",
        "data_situacao": "2020-01-01",
        "tipo": "MATRIZ",
        "porte": "PEQUENO",
        "natureza_juridica": "206-2 - Sociedade Empresária Limitada",
        "atividade_principal": [
            {"codigo": "6201-5/01", "descricao": "Desenvolvimento de software"}
        ],
        "atividades_secundarias": [],
        "endereco": {
            "logradouro": "Rua Teste",
            "numero": "123",
            "bairro": "Centro",
            "municipio": "Belo Horizonte",
            "uf": "MG",
            "cep": "30130-000",
        },
        "telefone": "(31) 3333-4444",
        "email": "contato@empresateste.com.br",
        "capital_social": "100000.00",
        "data_abertura": "2015-06-15",
        "latency_ms": 250,
        "cost_brl": 0.01,
    }


@pytest.fixture
def cep_response() -> dict[str, Any]:
    """Mock CEP lookup response."""
    return {
        "cep": "01310-100",
        "logradouro": "Avenida Paulista",
        "complemento": "",
        "bairro": "Bela Vista",
        "municipio": "São Paulo",
        "uf": "SP",
        "ibge": "3550308",
        "ddd": "11",
        "latency_ms": 50,
        "cost_brl": 0.001,
    }


@pytest.fixture
def cpf_response() -> dict[str, Any]:
    """Mock CPF validation response."""
    return {
        "cpf": "12345678909",
        "valid": True,
        "reason": None,
        "latency_ms": 10,
        "cost_brl": 0.0,
    }


@pytest.fixture
def transcription_response() -> dict[str, Any]:
    """Mock transcription response."""
    return {
        "text": "Olá, bom dia. Como você está?",
        "duration_seconds": 3.5,
        "language": "pt",
        "confidence": 0.95,
        "words": [
            {"word": "Olá", "start": 0.0, "end": 0.5},
            {"word": "bom", "start": 0.6, "end": 0.9},
            {"word": "dia", "start": 1.0, "end": 1.3},
        ],
        "latency_ms": 500,
        "cost_brl": 0.05,
    }


@pytest.fixture
def usage_response() -> dict[str, Any]:
    """Mock billing usage response."""
    return {
        "total_requests": 1000,
        "total_tokens": 500000,
        "total_cost": 25.50,
        "included_requests": 10000,
        "included_tokens": 1000000,
        "requests_percentage": 10.0,
        "tokens_percentage": 50.0,
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
        "days_remaining": 15,
    }


@pytest.fixture
def subscription_response() -> dict[str, Any]:
    """Mock subscription response."""
    return {
        "id": "sub-123",
        "plan": {"name": "pro", "id": "plan-pro"},
        "status": "active",
        "billing_cycle": "monthly",
        "current_period_start": "2026-01-01",
        "current_period_end": "2026-01-31",
    }


@pytest.fixture
def credits_response() -> dict[str, Any]:
    """Mock credits response."""
    return {
        "current_balance": 100.00,
        "credit_limit": 500.00,
        "available": 100.00,
    }


@pytest.fixture
def ibge_estados_response() -> dict[str, Any]:
    """Mock IBGE estados response."""
    return {
        "estados": [
            {"id": 31, "sigla": "MG", "nome": "Minas Gerais"},
            {"id": 35, "sigla": "SP", "nome": "São Paulo"},
            {"id": 33, "sigla": "RJ", "nome": "Rio de Janeiro"},
        ],
        "latency_ms": 50,
        "cost_brl": 0.0,
    }


@pytest.fixture
def ibge_municipios_response() -> dict[str, Any]:
    """Mock IBGE municipios response."""
    return {
        "municipios": [
            {"id": 3106200, "nome": "Belo Horizonte"},
            {"id": 3106705, "nome": "Betim"},
            {"id": 3118601, "nome": "Contagem"},
        ],
        "uf": {"id": 31, "sigla": "MG", "nome": "Minas Gerais"},
        "latency_ms": 100,
        "cost_brl": 0.0,
    }


# =============================================================================
# Mock Client Fixture
# =============================================================================


@pytest.fixture
def mock_client():
    """Create a mock NTLClient for testing."""
    with patch("ntlabs.client.httpx.Client") as mock_httpx:
        mock_http_client = MagicMock()
        mock_httpx.return_value = mock_http_client

        # Import after patching
        from ntlabs import NTLClient

        client = NTLClient(api_key="ntl_test_123")
        client._mock_http = mock_http_client

        yield client


@pytest.fixture
def mock_response():
    """Factory for creating mock HTTP responses."""

    def _create_response(json_data: dict, status_code: int = 200):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = json_data
        response.content = b'{"data": "test"}'
        response.headers = {}
        return response

    return _create_response


# =============================================================================
# Async Fixtures
# =============================================================================


@pytest.fixture
def mock_async_client():
    """Create a mock AsyncNTLClient for testing."""
    with patch("ntlabs.async_client.httpx.AsyncClient") as mock_httpx:
        mock_http_client = MagicMock()
        mock_httpx.return_value = mock_http_client

        # Import after patching
        from ntlabs import AsyncNTLClient

        client = AsyncNTLClient(api_key="ntl_test_123")
        client._mock_http = mock_http_client

        yield client


@pytest.fixture
def mock_async_response():
    """Factory for creating mock async HTTP responses."""

    def _create_async_response(json_data: dict, status_code: int = 200):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = json_data
        response.content = b'{"data": "test"}'
        response.headers = {}
        return response

    return _create_async_response


# =============================================================================
# Async Response Fixtures
# =============================================================================


@pytest.fixture
def auth_response() -> dict[str, Any]:
    """Mock auth response."""
    return {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "refresh_token": "refresh_abc123",
        "expires_in": 3600,
        "token_type": "Bearer",
    }


@pytest.fixture
def oauth_v2_response() -> dict[str, Any]:
    """Mock OAuth v2 response."""
    return {
        "session_id": "sess_abc123",
        "authorization_url": "https://auth.example.com/authorize?state=xyz",
        "state": "xyz",
        "expires_at": "2026-01-27T22:00:00Z",
    }


@pytest.fixture
def bb_oauth_response() -> dict[str, Any]:
    """Mock BB OAuth response."""
    return {
        "authorize_url": "https://oauth.bb.com.br/authorize?state=abc",
        "state": "abc123",
    }


@pytest.fixture
def bb_token_response() -> dict[str, Any]:
    """Mock BB token response."""
    return {
        "access_token": "bb_token_123",
        "refresh_token": "bb_refresh_456",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "openid-otp cpf",
    }


@pytest.fixture
def pix_charge_response() -> dict[str, Any]:
    """Mock PIX charge response."""
    return {
        "txid": "txid_abc123",
        "status": "ATIVA",
        "qr_code": "00020126580014BR.GOV.BCB.PIX0136...",
        "qr_code_base64": "iVBORw0KGgoAAAANS...",
        "amount": "100.00",
        "expires_at": "2026-01-27T22:00:00Z",
        "latency_ms": 150,
        "cost_brl": 0.01,
    }


@pytest.fixture
def product_plans_response() -> list[dict[str, Any]]:
    """Mock product plans response."""
    return [
        {
            "id": "plan-basic",
            "product": "hipocrates",
            "plan": "basic",
            "name": "Básico",
            "price_monthly": 99.0,
            "price_annual": 990.0,
            "limits": {"consultations": 100, "doctors": 5},
            "features": ["AI SOAP", "Prescriptions"],
        },
        {
            "id": "plan-pro",
            "product": "hipocrates",
            "plan": "professional",
            "name": "Profissional",
            "price_monthly": 299.0,
            "price_annual": 2990.0,
            "limits": {"consultations": 500, "doctors": 20},
            "features": ["AI SOAP", "Prescriptions", "RNDS Integration"],
        },
    ]


@pytest.fixture
def ocr_response() -> dict[str, Any]:
    """Mock OCR response."""
    return {
        "text": "CERTIDÃO DE NASCIMENTO...",
        "dados": {
            "nome": "João Silva",
            "data_nascimento": "1990-01-15",
            "nome_mae": "Maria Silva",
        },
        "confidence": 0.95,
    }


@pytest.fixture
def document_generation_response() -> dict[str, Any]:
    """Mock document generation response."""
    return {
        "content": "ESCRITURA PÚBLICA DE COMPRA E VENDA...",
        "document_type": "escritura_compra_venda",
        "metadata": {"model": "claude-sonnet", "tokens": 2048},
    }


@pytest.fixture
def rnds_prescription_response() -> dict[str, Any]:
    """Mock RNDS prescription response."""
    return {
        "success": True,
        "mock": False,
        "message": "Prescription sent successfully",
        "rnds_id": "rnds_abc123",
        "cost_brl": 0.05,
    }


@pytest.fixture
def rnds_certificate_response() -> dict[str, Any]:
    """Mock RNDS certificate response."""
    return {
        "success": True,
        "certificate": {
            "id": "cert_123",
            "type": "e-cpf",
            "subject_cn": "João Silva",
            "subject_cpf_cnpj": "12345678909",
            "issuer_cn": "ICP-Brasil",
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": "2027-01-01T00:00:00Z",
            "status": "active",
            "rnds_validated": True,
            "sncr_validated": True,
        },
    }


@pytest.fixture
def saude_transcription_response() -> dict[str, Any]:
    """Mock saude transcription response."""
    return {
        "text": "Paciente relata dor de cabeça há 3 dias...",
        "duration_seconds": 125.5,
        "language": "pt",
        "confidence": 0.92,
    }


@pytest.fixture
def soap_note_response() -> dict[str, Any]:
    """Mock SOAP note response."""
    return {
        "subjetivo": "Paciente relata dor de cabeça...",
        "objetivo": "PA: 120/80, FC: 72, Temp: 36.5°C...",
        "avaliacao": "Cefaleia tensional provável...",
        "plano": "1. Paracetamol 750mg...",
        "cid_sugerido": "G44.2",
        "medicamentos": [{"nome": "Paracetamol", "dosagem": "750mg"}],
    }


@pytest.fixture
def transcribe_models_response() -> dict[str, Any]:
    """Mock transcribe models response."""
    return {
        "models": [
            {
                "id": "whisper-1",
                "name": "Whisper",
                "provider": "openai",
                "description": "General purpose transcription",
                "languages": ["pt", "en", "es"],
                "price_per_minute_brl": 0.10,
                "available": True,
            },
            {
                "id": "azure-speech",
                "name": "Azure Speech",
                "provider": "azure",
                "description": "Azure speech recognition",
                "languages": ["pt-BR", "en-US"],
                "price_per_minute_brl": 0.08,
                "available": True,
            },
        ]
    }


@pytest.fixture
def censec_testamento_response() -> dict[str, Any]:
    """Mock CENSEC testamento response."""
    return {
        "id": "test_abc123",
        "tipo": "publico",
        "testador_nome": "João Silva",
        "testador_cpf": "12345678909",
        "data_lavratura": "2025-06-15",
        "livro": "A-123",
        "folha": "45",
        "cartorio_nome": "Cartório de Notas",
        "cartorio_cns": "12345",
        "municipio": "Belo Horizonte",
        "uf": "MG",
        "status": "vigente",
        "tem_codicilo": False,
    }


@pytest.fixture
def censec_procuracao_response() -> dict[str, Any]:
    """Mock CENSEC procuracao response."""
    return {
        "id": "proc_def456",
        "tipo": "ad_negotia",
        "outorgante": {"nome": "João Silva", "cpf": "12345678909"},
        "outorgado": {"nome": "Maria Souza", "cpf": "98765432100"},
        "poderes": ["administrar", "vender"],
        "data_lavratura": "2025-07-20",
        "data_validade": "2026-07-20",
        "livro": "B-456",
        "folha": "78",
        "cartorio_nome": "Cartório de Notas",
        "cartorio_cns": "12345",
        "municipio": "Belo Horizonte",
        "uf": "MG",
        "status": "vigente",
        "substabelecimentos": [],
    }


@pytest.fixture
def crc_certidao_response() -> dict[str, Any]:
    """Mock CRC certidao response."""
    return {
        "matricula": "123456 01 55 2025 1 00001 123 1234567",
        "tipo": "nascimento",
        "livro": "A-1",
        "folha": "55",
        "termo": "1234",
        "data_registro": "2025-01-15",
        "cartorio_nome": "Cartório de Registro Civil",
        "cartorio_cns": "12345",
        "municipio": "Belo Horizonte",
        "uf": "MG",
        "status": "valida",
        "dados": {
            "nome": "João Silva",
            "data_nascimento": "2025-01-10",
            "nome_mae": "Maria Silva",
            "nome_pai": "José Silva",
        },
        "hash_validacao": "abc123hash",
        "url_verificacao": "https://crc.example.com/verify/abc123",
    }


@pytest.fixture
def enotariado_fluxo_response() -> dict[str, Any]:
    """Mock e-Notariado fluxo response."""
    return {
        "success": True,
        "fluxo_id": "fluxo_abc123",
        "mne": "ABC123XYZ",
        "status": "Created",
        "tipo_documento": "Deed",
        "participantes": [
            {"cpf": "12345678909", "nome": "João Silva", "tipo": "outorgante", "assinou": False}
        ],
        "criado_em": "2026-01-27T20:00:00Z",
        "expira_em": "2026-02-27T20:00:00Z",
        "url_assinatura": "https://enotariado.example.com/sign/ABC123XYZ",
    }


@pytest.fixture
def onr_matricula_response() -> dict[str, Any]:
    """Mock ONR matricula response."""
    return {
        "matricula": "1234",
        "serventia": "Cartório de Registro de Imóveis",
        "cns": "12345",
        "uf": "MG",
        "municipio": "Belo Horizonte",
        "area": 150.5,
        "endereco": {
            "logradouro": "Rua das Flores",
            "numero": "123",
            "bairro": "Centro",
        },
        "proprietarios": [{"nome": "João Silva", "cpf": "12345678909"}],
        "onus": [],
        "averbacoes": [],
        "atualizado_em": "2026-01-20T10:00:00Z",
    }


@pytest.fixture
def onr_protocolo_response() -> dict[str, Any]:
    """Mock ONR protocolo response."""
    return {
        "success": True,
        "protocolo": "PROTOC2026000001",
        "numero_prenotacao": "123456",
        "tipo": "registro",
        "matricula": "1234",
        "serventia": "Cartório de Registro de Imóveis",
        "status": "prenotado",
        "prenotado_em": "2026-01-27T20:00:00Z",
        "prazo_exigencia": "2026-02-27T20:00:00Z",
        "exigencias": [],
    }


# =============================================================================
# Environment Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Clean environment variables for each test."""
    monkeypatch.delenv("NTL_API_KEY", raising=False)
    monkeypatch.delenv("NTL_API_URL", raising=False)
    monkeypatch.delenv("NTL_INTERNAL_URL", raising=False)
