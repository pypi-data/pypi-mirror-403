"""
Tests for CRC Nacional Resource.
"""

from datetime import datetime
from unittest.mock import Mock

import pytest

from ntlabs.resources.registros.crc import (
    CertidaoResult,
    CertificadoInfo,
    CRCResource,
    ProclamaResult,
    StatusCertidao,
    TipoCertidao,
    TipoCertificado,
)


class TestEnums:
    """Test enum values."""

    def test_tipo_certidao_values(self):
        assert TipoCertidao.NASCIMENTO.value == "nascimento"
        assert TipoCertidao.CASAMENTO.value == "casamento"
        assert TipoCertidao.OBITO.value == "obito"
        assert TipoCertidao.INTEIRO_TEOR.value == "inteiro_teor"

    def test_status_certidao_values(self):
        assert StatusCertidao.VALIDA.value == "valida"
        assert StatusCertidao.CANCELADA.value == "cancelada"
        assert StatusCertidao.AVERBADA.value == "averbada"
        assert StatusCertidao.NAO_ENCONTRADA.value == "nao_encontrada"

    def test_tipo_certificado_values(self):
        assert TipoCertificado.E_CPF_A3.value == "e-cpf-a3"
        assert TipoCertificado.E_CNPJ_A3.value == "e-cnpj-a3"


class TestCertidaoResult:
    """Test CertidaoResult dataclass."""

    def test_create_certidao(self):
        certidao = CertidaoResult(
            matricula="123456 01 55 2020 1 00001 001 0000001-00",
            tipo=TipoCertidao.NASCIMENTO,
            livro="A-001",
            folha="001",
            termo="00001",
            data_registro="2020-01-15",
            cartorio_nome="1º Ofício de Registro Civil",
            cartorio_cns="123456",
            municipio="Belo Horizonte",
            uf="MG",
            status=StatusCertidao.VALIDA,
            dados={"nome": "João da Silva"},
            hash_validacao="abc123",
            latency_ms=150,
            cost_brl=0.10,
        )

        assert "123456" in certidao.matricula
        assert certidao.tipo == TipoCertidao.NASCIMENTO
        assert certidao.status == StatusCertidao.VALIDA
        assert certidao.municipio == "Belo Horizonte"

    def test_certidao_to_dict(self):
        certidao = CertidaoResult(
            matricula="123456",
            tipo=TipoCertidao.CASAMENTO,
            livro="B-001",
            folha="001",
            termo="00001",
            data_registro="2020-06-20",
            cartorio_nome="Cartório",
            cartorio_cns="123",
            municipio="SP",
            uf="SP",
            status=StatusCertidao.VALIDA,
            dados={},
            latency_ms=100,
            cost_brl=0.05,
        )

        data = certidao.to_dict()
        assert data["matricula"] == "123456"
        assert data["tipo"] == TipoCertidao.CASAMENTO


class TestProclamaResult:
    """Test ProclamaResult dataclass."""

    def test_create_proclama(self):
        proclama = ProclamaResult(
            id="uuid-123",
            protocolo="2025/001234",
            status="publicado",
            data_publicacao="2025-01-25",
            prazo_final="2025-02-10",
            nubente1={"nome": "Maria", "cpf": "123.456.789-00"},
            nubente2={"nome": "João", "cpf": "987.654.321-00"},
            cartorio_cns="123456",
            mensagem="Proclama publicado com sucesso",
            latency_ms=200,
            cost_brl=0.50,
        )

        assert proclama.protocolo == "2025/001234"
        assert proclama.status == "publicado"
        assert "Maria" in proclama.nubente1["nome"]


class TestCertificadoInfo:
    """Test CertificadoInfo dataclass."""

    def test_create_certificado(self):
        cert = CertificadoInfo(
            id="cert-123",
            tipo=TipoCertificado.E_CNPJ_A3,
            titular_nome="Cartório 1º Ofício",
            titular_cpf_cnpj="12.345.678/0001-90",
            emissor="AC Certisign",
            valido_de=datetime(2024, 1, 1),
            valido_ate=datetime(2027, 1, 1),
            status="active",
            crc_validado=True,
            cartorio_cns="123456",
        )

        assert cert.tipo == TipoCertificado.E_CNPJ_A3
        assert cert.crc_validado is True
        assert cert.status == "active"


class TestCRCResource:
    """Test CRCResource methods."""

    @pytest.fixture
    def mock_client(self):
        client = Mock()
        return client

    @pytest.fixture
    def crc(self, mock_client):
        return CRCResource(mock_client)

    def test_initialization(self, crc, mock_client):
        assert crc._client == mock_client

    # =========================================================================
    # Certificate Management
    # =========================================================================

    def test_upload_certificate_success(self, crc, mock_client):
        mock_client.post.return_value = {
            "success": True,
            "certificate": {
                "id": "cert-123",
                "tipo": "e-cnpj-a3",
                "titular_nome": "Cartório",
                "titular_cpf_cnpj": "12.345.678/0001-90",
                "emissor": "AC Certisign",
                "valido_de": "2024-01-01T00:00:00",
                "valido_ate": "2027-01-01T00:00:00",
                "status": "active",
                "crc_validado": True,
                "cartorio_cns": "123456",
            },
        }

        result = crc.upload_certificate(
            cartorio_id="uuid-123",
            certificate=Mock(),
            password="senha123",
        )

        assert result.success is True
        assert result.certificado_id == "cert-123"
        assert result.certificado_info.crc_validado is True

    def test_upload_certificate_failure(self, crc, mock_client):
        mock_client.post.return_value = {
            "success": False,
            "error": "Certificado inválido",
        }

        result = crc.upload_certificate(
            cartorio_id="uuid-123",
            certificate=Mock(),
            password="senha_errada",
        )

        assert result.success is False
        assert result.error == "Certificado inválido"

    def test_get_certificates(self, crc, mock_client):
        mock_client.get.return_value = {
            "certificates": [
                {
                    "id": "cert-1",
                    "tipo": "e-cnpj-a3",
                    "titular_nome": "Cartório 1",
                    "emissor": "AC Certisign",
                    "valido_de": "2024-01-01T00:00:00",
                    "valido_ate": "2027-01-01T00:00:00",
                    "status": "active",
                    "crc_validado": True,
                },
            ]
        }

        certs = crc.get_certificates("uuid-123")

        assert len(certs) == 1
        assert certs[0].id == "cert-1"

    def test_has_valid_certificate(self, crc, mock_client):
        mock_client.get.return_value = {"valid": True}

        assert crc.has_valid_certificate("uuid-123") is True

    def test_revoke_certificate(self, crc, mock_client):
        mock_client.post.return_value = {"success": True}

        assert crc.revoke_certificate("cert-123", "Expirado") is True

    # =========================================================================
    # Certidões
    # =========================================================================

    def test_consultar_certidao(self, crc, mock_client):
        mock_client.get.return_value = {
            "matricula": "123456 01 55 2020 1 00001 001 0000001-00",
            "tipo": "nascimento",
            "livro": "A-001",
            "folha": "001",
            "termo": "00001",
            "data_registro": "2020-01-15",
            "cartorio_nome": "1º Ofício",
            "cartorio_cns": "123456",
            "municipio": "Belo Horizonte",
            "uf": "MG",
            "status": "valida",
            "dados": {"nome": "João da Silva", "data_nascimento": "2020-01-10"},
            "hash_validacao": "abc123xyz",
            "latency_ms": 150,
            "cost_brl": 0.10,
        }

        result = crc.consultar_certidao(
            cartorio_id="uuid-123",
            tipo="nascimento",
            matricula="123456 01 55 2020 1 00001 001 0000001-00",
        )

        assert result.tipo == TipoCertidao.NASCIMENTO
        assert result.status == StatusCertidao.VALIDA
        assert result.municipio == "Belo Horizonte"
        assert "João" in result.dados["nome"]

    def test_buscar_certidoes(self, crc, mock_client):
        mock_client.get.return_value = {
            "total": 2,
            "certidoes": [
                {"matricula": "123", "nome": "João"},
                {"matricula": "456", "nome": "Maria"},
            ],
            "pagina": 1,
            "por_pagina": 20,
            "latency_ms": 200,
            "cost_brl": 0.20,
        }

        result = crc.buscar_certidoes(
            cartorio_id="uuid-123",
            tipo="nascimento",
            nome="Silva",
            uf="mg",
        )

        assert result.total == 2
        assert len(result.certidoes) == 2

        # Verify UF was uppercased
        mock_client.get.assert_called_once()
        call_params = mock_client.get.call_args[1]["params"]
        assert call_params["uf"] == "MG"

    def test_verificar_autenticidade(self, crc, mock_client):
        mock_client.get.return_value = {
            "autentica": True,
            "matricula": "123456",
            "tipo": "nascimento",
            "data_emissao": "2025-01-20",
            "cartorio_nome": "1º Ofício",
            "mensagem": "Certidão autêntica",
            "latency_ms": 100,
            "cost_brl": 0.05,
        }

        result = crc.verificar_autenticidade("ABC123XYZ")

        assert result.autentica is True
        assert result.tipo == TipoCertidao.NASCIMENTO

    # =========================================================================
    # Segunda Via
    # =========================================================================

    def test_solicitar_segunda_via(self, crc, mock_client):
        mock_client.post.return_value = {
            "id": "sv-123",
            "protocolo": "2025/SV/001234",
            "status": "pendente",
            "valor_emolumentos": 73.50,
            "prazo_entrega": "2025-02-01",
            "url_pagamento": "https://pag.crc.org.br/...",
            "latency_ms": 300,
            "cost_brl": 0.30,
        }

        result = crc.solicitar_segunda_via(
            cartorio_id="uuid-123",
            tipo="nascimento",
            matricula="123456",
            solicitante={"nome": "Maria", "cpf": "123.456.789-00"},
            motivo="Extravio",
        )

        assert result.protocolo == "2025/SV/001234"
        assert result.valor_emolumentos == 73.50

    def test_consultar_segunda_via(self, crc, mock_client):
        mock_client.get.return_value = {
            "id": "sv-123",
            "status": "pronta",
            "matricula": "123456",
            "tipo": "nascimento",
            "solicitante": {"nome": "Maria"},
            "valor_emolumentos": 73.50,
            "latency_ms": 100,
        }

        result = crc.consultar_segunda_via("2025/SV/001234")

        assert result.status == "pronta"

    # =========================================================================
    # Averbações
    # =========================================================================

    def test_registrar_averbacao(self, crc, mock_client):
        mock_client.post.return_value = {
            "id": "av-123",
            "data_averbacao": "2025-01-25",
            "status": "registrada",
            "latency_ms": 250,
            "cost_brl": 0.50,
        }

        result = crc.registrar_averbacao(
            cartorio_id="uuid-123",
            matricula="123456",
            tipo_averbacao="divorcio",
            conteudo="Averbação de divórcio conforme...",
        )

        assert result.status == "registrada"
        assert result.tipo_averbacao == "divorcio"

    # =========================================================================
    # e-Proclamas
    # =========================================================================

    def test_enviar_proclama(self, crc, mock_client):
        mock_client.post.return_value = {
            "id": "proc-123",
            "protocolo": "2025/PROC/001234",
            "status": "publicado",
            "data_publicacao": "2025-01-25",
            "prazo_final": "2025-02-10",
            "cartorio_cns": "123456",
            "mensagem": "Proclama publicado",
            "latency_ms": 350,
            "cost_brl": 1.00,
        }

        result = crc.enviar_proclama(
            cartorio_id="uuid-123",
            nubente1={"nome": "Maria Silva", "cpf": "123.456.789-00"},
            nubente2={"nome": "João Santos", "cpf": "987.654.321-00"},
            regime_bens="comunhao_parcial",
        )

        assert result.protocolo == "2025/PROC/001234"
        assert result.status == "publicado"

    def test_consultar_proclama(self, crc, mock_client):
        mock_client.get.return_value = {
            "id": "proc-123",
            "status": "aguardando_prazo",
            "data_publicacao": "2025-01-25",
            "prazo_final": "2025-02-10",
            "nubente1": {"nome": "Maria"},
            "nubente2": {"nome": "João"},
            "cartorio_cns": "123456",
            "mensagem": "",
            "latency_ms": 100,
        }

        result = crc.consultar_proclama("2025/PROC/001234")

        assert result.status == "aguardando_prazo"

    def test_cancelar_proclama(self, crc, mock_client):
        mock_client.post.return_value = {"success": True, "message": "Cancelado"}

        result = crc.cancelar_proclama(
            cartorio_id="uuid-123",
            protocolo="2025/PROC/001234",
            motivo="Desistência",
        )

        assert result["success"] is True

    # =========================================================================
    # Livro D
    # =========================================================================

    def test_registrar_livro_d(self, crc, mock_client):
        mock_client.post.return_value = {
            "id": "ld-123",
            "numero_registro": "D-001-2025",
            "data_registro": "2025-01-25",
            "cartorio_origem_cns": "111111",
            "cartorio_destino_cns": "222222",
            "status": "registrado",
            "latency_ms": 400,
            "cost_brl": 1.50,
        }

        result = crc.registrar_livro_d(
            cartorio_id="uuid-222",
            proclama_protocolo="2025/PROC/001234",
            data_casamento="2025-01-25",
            dados_casamento={"regime": "comunhao_parcial"},
        )

        assert result.numero_registro == "D-001-2025"
        assert result.status == "registrado"

    # =========================================================================
    # Utilidades
    # =========================================================================

    def test_health(self, crc, mock_client):
        mock_client.get.return_value = {
            "status": "healthy",
            "crc_connection": "ok",
            "certificate_valid": True,
        }

        result = crc.health()

        assert result["status"] == "healthy"

    def test_get_cartorios(self, crc, mock_client):
        mock_client.get.return_value = {
            "cartorios": [
                {"cns": "123456", "nome": "1º Ofício", "municipio": "BH"},
                {"cns": "789012", "nome": "2º Ofício", "municipio": "BH"},
            ]
        }

        result = crc.get_cartorios(uf="mg", municipio="Belo Horizonte")

        assert len(result) == 2

        # Verify UF was uppercased
        call_params = mock_client.get.call_args[1]["params"]
        assert call_params["uf"] == "MG"

    def test_empty_response_handling(self, crc, mock_client):
        mock_client.get.return_value = {}

        result = crc.consultar_certidao(
            cartorio_id="uuid-123",
            tipo="nascimento",
            matricula="123456",
        )

        assert result.matricula == "123456"
        assert result.dados == {}
