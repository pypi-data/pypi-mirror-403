"""
NTLabs SDK - Async ONR Resource Tests
Tests for the AsyncONRResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
from unittest.mock import AsyncMock

from ntlabs.resources.registros.async_onr import AsyncONRResource
from ntlabs.resources.registros.onr import (
    MatriculaInfo,
    CertidaoResult,
    ProtocoloResult,
    BuscaPropriedadeResult,
    PenhoraResult,
    IndisponibilidadeResult,
    OficioResult,
    TipoCertidao,
    TipoProtocolo,
    TipoPenhora,
    StatusCertidao,
    StatusProtocolo,
)


@pytest.mark.asyncio
class TestAsyncONRResource:
    """Tests for AsyncONRResource."""

    async def test_initialization(self):
        """AsyncONRResource initializes with client."""
        mock_client = AsyncMock()
        onr = AsyncONRResource(mock_client)
        assert onr._client == mock_client
        assert onr.ENDPOINT_PREFIX == "/v1/onr"


@pytest.mark.asyncio
class TestAsyncONRMatriculas:
    """Tests for async matriculas."""

    async def test_consultar_matricula(self, onr_matricula_response):
        """Query matricula."""
        mock_client = AsyncMock()
        mock_client.get.return_value = onr_matricula_response

        onr = AsyncONRResource(mock_client)
        result = await onr.consultar_matricula(
            cartorio_id="cart_123",
            cns="12345",
            matricula="1234",
        )

        assert isinstance(result, MatriculaInfo)
        assert result.matricula == "1234"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/onr/cartorios/cart_123/serventias/12345/matriculas/1234"

    async def test_consultar_matricula_com_historico(self, onr_matricula_response):
        """Query matricula with history."""
        mock_client = AsyncMock()
        mock_client.get.return_value = onr_matricula_response

        onr = AsyncONRResource(mock_client)
        result = await onr.consultar_matricula(
            cartorio_id="cart_123",
            cns="12345",
            matricula="1234",
            incluir_historico=True,
        )

        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["incluir_historico"] is True

    async def test_visualizar_matricula(self):
        """View matricula summary."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"resumo": "Matricula 1234"}

        onr = AsyncONRResource(mock_client)
        result = await onr.visualizar_matricula("cart_123", "12345", "1234")

        assert "resumo" in result
        mock_client.get.assert_called_once()


@pytest.mark.asyncio
class TestAsyncONRCertidoes:
    """Tests for async certidoes."""

    async def test_solicitar_certidao(self):
        """Request certidao."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "success": True,
            "pedido_id": "pedido_123",
            "status": "solicitada",
            "matricula": "1234",
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.solicitar_certidao(
            cartorio_id="cart_123",
            cns_destino="12345",
            matricula="1234",
            tipo=TipoCertidao.MATRICULA,
        )

        assert isinstance(result, CertidaoResult)
        assert result.status == StatusCertidao.SOLICITADA
        mock_client.post.assert_called_once()

    async def test_solicitar_certidao_urgente(self):
        """Request urgent certidao."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "success": True,
            "pedido_id": "pedido_123",
            "status": "solicitada",
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.solicitar_certidao(
            cartorio_id="cart_123",
            cns_destino="12345",
            matricula="1234",
            tipo=TipoCertidao.ONUS_ACOES,
            finalidade="Financiamento",
            urgente=True,
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["finalidade"] == "Financiamento"
        assert call_args[1]["json"]["urgente"] is True

    async def test_consultar_certidao(self):
        """Query certidao status."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "pedido_id": "pedido_123",
            "status": "disponivel",
            "tipo": "matricula",
            "matricula": "1234",
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.consultar_certidao("cart_123", "pedido_123")

        assert isinstance(result, CertidaoResult)
        mock_client.get.assert_called_once()

    async def test_download_certidao(self):
        """Download certidao PDF."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"arquivo_bytes": b"pdf_data"}

        onr = AsyncONRResource(mock_client)
        result = await onr.download_certidao("cart_123", "pedido_123")

        assert result == b"pdf_data"
        mock_client.get.assert_called_once()


@pytest.mark.asyncio
class TestAsyncONRPropriedades:
    """Tests for async property search."""

    async def test_buscar_propriedades(self):
        """Search properties."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "cpf_cnpj": "12345678909",
            "total": 2,
            "imoveis": [
                {"matricula": "1234", "endereco": "Rua A"},
                {"matricula": "5678", "endereco": "Rua B"},
            ],
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.buscar_propriedades(
            cartorio_id="cart_123",
            cpf="12345678909",
        )

        assert isinstance(result, BuscaPropriedadeResult)
        assert result.total == 2
        mock_client.get.assert_called_once()

    async def test_buscar_propriedades_cnpj(self):
        """Search properties by CNPJ."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"success": True, "total": 0, "imoveis": []}

        onr = AsyncONRResource(mock_client)
        result = await onr.buscar_propriedades(
            cartorio_id="cart_123",
            cnpj="12345678000190",
        )

        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["cnpj"] == "12345678000190"


@pytest.mark.asyncio
class TestAsyncONRProtocolo:
    """Tests for async protocolo."""

    async def test_criar_protocolo(self, onr_protocolo_response):
        """Create protocolo."""
        mock_client = AsyncMock()
        mock_client.post.return_value = onr_protocolo_response

        onr = AsyncONRResource(mock_client)
        result = await onr.criar_protocolo(
            cartorio_id="cart_123",
            cns_destino="12345",
            matricula="1234",
            tipo=TipoProtocolo.REGISTRO,
            documento_id="doc_123",
            titulo="Registro de Escritura",
        )

        assert isinstance(result, ProtocoloResult)
        assert result.protocolo == "PROTOC2026000001"
        mock_client.post.assert_called_once()

    async def test_consultar_protocolo(self):
        """Query protocolo."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "protocolo": "PROTOC2026000001",
            "status": "em_analise",
            "exigencias": [{"id": 1, "descricao": "Documento incompleto"}],
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.consultar_protocolo("cart_123", "PROTOC2026000001")

        assert isinstance(result, ProtocoloResult)
        assert len(result.exigencias) == 1

    async def test_responder_exigencia(self):
        """Respond to exigencia."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "success": True,
            "protocolo": "PROTOC2026000001",
            "status": "em_analise",
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.responder_exigencia(
            cartorio_id="cart_123",
            protocolo="PROTOC2026000001",
            documento_id="doc_novo_123",
            observacao="Documento corrigido",
        )

        assert isinstance(result, ProtocoloResult)
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
class TestAsyncONRPenhora:
    """Tests for async penhora."""

    async def test_consultar_penhora(self):
        """Query penhora."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "penhoras": [
                {
                    "codigo": "PEN123",
                    "tipo": "judicial",
                    "valor": 100000.00,
                    "processo": "0001234-12.2026.8.13.0000",
                }
            ]
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.consultar_penhora("cart_123", "12345", "1234")

        assert len(result) == 1
        assert isinstance(result[0], PenhoraResult)
        mock_client.get.assert_called_once()

    async def test_registrar_penhora(self):
        """Register penhora."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "success": True,
            "codigo": "PEN456",
            "tipo": "judicial",
            "matricula": "1234",
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.registrar_penhora(
            cartorio_id="cart_123",
            cns="12345",
            matricula="1234",
            tipo=TipoPenhora.JUDICIAL,
            processo="0001234-12.2026.8.13.0000",
            vara="1ª Vara Cível",
            credor="Banco XYZ",
            devedor="João Silva",
            valor=150000.00,
        )

        assert isinstance(result, PenhoraResult)
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
class TestAsyncONRCNIB:
    """Tests for async CNIB."""

    async def test_consultar_indisponibilidade(self):
        """Query indisponibilidade."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "cpf_cnpj": "12345678909",
            "nome": "João Silva",
            "possui_indisponibilidade": True,
            "indisponibilidades": [{"processo": "123", "valor": 50000}],
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.consultar_indisponibilidade(
            cartorio_id="cart_123",
            cpf="12345678909",
        )

        assert isinstance(result, IndisponibilidadeResult)
        assert result.possui_indisponibilidade is True
        mock_client.get.assert_called_once()

    async def test_consultar_indisponibilidade_cnpj(self):
        """Query indisponibilidade by CNPJ."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"success": True, "possui_indisponibilidade": False}

        onr = AsyncONRResource(mock_client)
        result = await onr.consultar_indisponibilidade(
            cartorio_id="cart_123",
            cnpj="12345678000190",
        )

        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["cnpj"] == "12345678000190"


@pytest.mark.asyncio
class TestAsyncONROficio:
    """Tests for async oficio."""

    async def test_enviar_oficio(self):
        """Send oficio."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "success": True,
            "oficio_id": "oficio_123",
            "tipo": "enviado",
            "assunto": "Consulta",
            "status": "enviado",
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.enviar_oficio(
            cartorio_id="cart_123",
            cns_destino="67890",
            assunto="Consulta de matrícula",
            conteudo="Solicito informações...",
        )

        assert isinstance(result, OficioResult)
        assert result.oficio_id == "oficio_123"
        mock_client.post.assert_called_once()

    async def test_consultar_oficio(self):
        """Query oficio."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "oficio_id": "oficio_123",
            "tipo": "recebido",
            "assunto": "Resposta",
            "status": "recebido",
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.consultar_oficio("cart_123", "oficio_123")

        assert isinstance(result, OficioResult)
        mock_client.get.assert_called_once()

    async def test_listar_oficios(self):
        """List oficios."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "oficios": [
                {"oficio_id": "oficio_1", "status": "enviado"},
                {"oficio_id": "oficio_2", "status": "respondido"},
            ]
        }

        onr = AsyncONRResource(mock_client)
        result = await onr.listar_oficios("cart_123", tipo="enviado")

        assert len(result["oficios"]) == 2
        mock_client.get.assert_called_once()
