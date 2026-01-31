"""
NTLabs SDK - Async CRC Resource Tests
Tests for the AsyncCRCResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
import io
from datetime import datetime
from unittest.mock import AsyncMock

from ntlabs.resources.registros.async_crc import AsyncCRCResource
from ntlabs.resources.registros.crc import (
    CertidaoResult,
    CertificadoInfo,
    CertificadoUploadResult,
    SegundaViaResult,
    AverbacaoResult,
    ProclamaResult,
    LivroDResult,
    TipoCertidao,
    TipoCertificado,
    StatusCertidao,
)


@pytest.mark.asyncio
class TestAsyncCRCResource:
    """Tests for AsyncCRCResource."""

    async def test_initialization(self):
        """AsyncCRCResource initializes with client."""
        mock_client = AsyncMock()
        crc = AsyncCRCResource(mock_client)
        assert crc._client == mock_client


@pytest.mark.asyncio
class TestAsyncCRCCertificados:
    """Tests for async certificates."""

    async def test_upload_certificate(self):
        """Upload certificate."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "success": True,
            "certificate": {
                "id": "cert_123",
                "tipo": "e-cnpj-a3",
                "titular_nome": "Cartório Teste",
                "titular_cpf_cnpj": "12345678000190",
                "emissor": "ICP-Brasil",
                "valido_de": "2026-01-01T00:00:00Z",
                "valido_ate": "2027-01-01T00:00:00Z",
                "status": "active",
                "crc_validado": True,
            },
        }

        crc = AsyncCRCResource(mock_client)
        cert_data = io.BytesIO(b"fake_certificate")
        result = await crc.upload_certificate("cart_123", cert_data, "password123")

        assert isinstance(result, CertificadoUploadResult)
        assert result.success is True
        assert result.certificado_id == "cert_123"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/crc/certificates/upload"

    async def test_upload_certificate_failure(self):
        """Upload certificate failure."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": False, "error": "Invalid password"}

        crc = AsyncCRCResource(mock_client)
        cert_data = io.BytesIO(b"fake_certificate")
        result = await crc.upload_certificate("cart_123", cert_data, "wrong_pass")

        assert isinstance(result, CertificadoUploadResult)
        assert result.success is False
        assert result.error == "Invalid password"

    async def test_get_certificates(self):
        """Get certificates."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "certificates": [
                {
                    "id": "cert_123",
                    "tipo": "e-cnpj-a3",
                    "titular_nome": "Cartório",
                    "valido_de": "2026-01-01T00:00:00Z",
                    "valido_ate": "2027-01-01T00:00:00Z",
                    "status": "active",
                }
            ]
        }

        crc = AsyncCRCResource(mock_client)
        result = await crc.get_certificates("cart_123")

        assert len(result) == 1
        assert isinstance(result[0], CertificadoInfo)
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/crc/certificates"

    async def test_has_valid_certificate(self):
        """Check valid certificate."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"valid": True}

        crc = AsyncCRCResource(mock_client)
        result = await crc.has_valid_certificate("cart_123")

        assert result is True
        mock_client.get.assert_called_once()

    async def test_revoke_certificate(self):
        """Revoke certificate."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": True}

        crc = AsyncCRCResource(mock_client)
        result = await crc.revoke_certificate("cert_123", "Compromised")

        assert result is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/crc/certificates/revoke"


@pytest.mark.asyncio
class TestAsyncCRCCertidoes:
    """Tests for async certidoes."""

    async def test_consultar_certidao(self, crc_certidao_response):
        """Consult certidao."""
        mock_client = AsyncMock()
        mock_client.get.return_value = crc_certidao_response

        crc = AsyncCRCResource(mock_client)
        result = await crc.consultar_certidao(
            cartorio_id="cart_123",
            tipo="nascimento",
            matricula="123456 01 55 2025 1 00001 123 1234567",
        )

        assert isinstance(result, CertidaoResult)
        assert result.matricula == "123456 01 55 2025 1 00001 123 1234567"
        assert result.tipo == TipoCertidao.NASCIMENTO
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/crc/certidao"

    async def test_buscar_certidoes(self):
        """Search certidoes."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "total": 2,
            "certidoes": [{"matricula": "123"}, {"matricula": "456"}],
            "pagina": 1,
            "por_pagina": 20,
        }

        crc = AsyncCRCResource(mock_client)
        result = await crc.buscar_certidoes(
            cartorio_id="cart_123",
            tipo="nascimento",
            nome="João Silva",
            cpf="12345678909",
        )

        assert result.total == 2
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["cpf"] == "12345678909"

    async def test_verificar_autenticidade(self):
        """Verify certidao authenticity."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "autentica": True,
            "matricula": "123456...",
            "tipo": "nascimento",
            "data_emissao": "2026-01-27",
        }

        crc = AsyncCRCResource(mock_client)
        result = await crc.verificar_autenticidade("code123")

        assert result.autentica is True
        mock_client.get.assert_called_once()


@pytest.mark.asyncio
class TestAsyncCRCSegundaVia:
    """Tests for async segunda via."""

    async def test_solicitar_segunda_via(self):
        """Request segunda via."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "id": "seg_123",
            "protocolo": "PROT123",
            "status": "pendente",
            "matricula": "123456...",
            "valor_emolumentos": 50.00,
        }

        crc = AsyncCRCResource(mock_client)
        result = await crc.solicitar_segunda_via(
            cartorio_id="cart_123",
            tipo="nascimento",
            matricula="123456...",
            solicitante={"nome": "João", "cpf": "12345678909"},
            motivo="Perda",
        )

        assert isinstance(result, SegundaViaResult)
        assert result.protocolo == "PROT123"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/crc/segunda-via"

    async def test_consultar_segunda_via(self):
        """Query segunda via status."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "id": "seg_123",
            "protocolo": "PROT123",
            "status": "pronto",
        }

        crc = AsyncCRCResource(mock_client)
        result = await crc.consultar_segunda_via("PROT123")

        assert result.status == "pronto"
        mock_client.get.assert_called_once()


@pytest.mark.asyncio
class TestAsyncCRCAverbacoes:
    """Tests for async averbacoes."""

    async def test_registrar_averbacao(self):
        """Register averbacao."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "id": "avb_123",
            "matricula": "123456...",
            "tipo_averbacao": "casamento",
            "data_averbacao": "2026-01-27",
            "status": "registrada",
        }

        crc = AsyncCRCResource(mock_client)
        result = await crc.registrar_averbacao(
            cartorio_id="cart_123",
            matricula="123456...",
            tipo_averbacao="casamento",
            conteudo="Averbacao de casamento...",
        )

        assert isinstance(result, AverbacaoResult)
        assert result.status == "registrada"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/crc/averbacao"


@pytest.mark.asyncio
class TestAsyncCRCProclamas:
    """Tests for async proclamas."""

    async def test_enviar_proclama(self):
        """Send proclama."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "id": "proc_123",
            "protocolo": "PROC123",
            "status": "publicado",
            "nubente1": {"nome": "João"},
            "nubente2": {"nome": "Maria"},
        }

        crc = AsyncCRCResource(mock_client)
        result = await crc.enviar_proclama(
            cartorio_id="cart_123",
            nubente1={"nome": "João", "cpf": "12345678909"},
            nubente2={"nome": "Maria", "cpf": "98765432100"},
        )

        assert isinstance(result, ProclamaResult)
        assert result.status == "publicado"
        mock_client.post.assert_called_once()

    async def test_consultar_proclama(self):
        """Query proclama."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "id": "proc_123",
            "protocolo": "PROC123",
            "status": "em_andamento",
        }

        crc = AsyncCRCResource(mock_client)
        result = await crc.consultar_proclama("PROC123")

        assert result.status == "em_andamento"
        mock_client.get.assert_called_once()

    async def test_cancelar_proclama(self):
        """Cancel proclama."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": True}

        crc = AsyncCRCResource(mock_client)
        result = await crc.cancelar_proclama("cart_123", "PROC123", "Desistência")

        assert result["success"] is True
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
class TestAsyncCRCLivroD:
    """Tests for async Livro D."""

    async def test_registrar_livro_d(self):
        """Register in Livro D."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "id": "livrod_123",
            "numero_registro": "1234",
            "data_registro": "2026-01-27",
            "status": "registrado",
        }

        crc = AsyncCRCResource(mock_client)
        result = await crc.registrar_livro_d(
            cartorio_id="cart_123",
            proclama_protocolo="PROC123",
            data_casamento="2026-01-25",
            dados_casamento={"testemunhas": []},
        )

        assert isinstance(result, LivroDResult)
        assert result.numero_registro == "1234"
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
class TestAsyncCRCUtilities:
    """Tests for async utilities."""

    async def test_health(self):
        """Check CRC health."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"status": "healthy"}

        crc = AsyncCRCResource(mock_client)
        result = await crc.health()

        assert result["status"] == "healthy"
        mock_client.get.assert_called_once()

    async def test_get_cartorios(self):
        """Get cartorios list."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "cartorios": [{"id": "cart_123", "nome": "Cartório Teste"}]
        }

        crc = AsyncCRCResource(mock_client)
        result = await crc.get_cartorios(uf="MG", municipio="Belo Horizonte")

        assert len(result) == 1
        mock_client.get.assert_called_once()
