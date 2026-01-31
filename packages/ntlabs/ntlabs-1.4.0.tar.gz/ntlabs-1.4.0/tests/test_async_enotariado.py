"""
NTLabs SDK - Async E-Notariado Resource Tests
Tests for the AsyncENotariadoResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
from unittest.mock import AsyncMock

from ntlabs.resources.registros.async_enotariado import AsyncENotariadoResource
from ntlabs.resources.registros.enotariado import (
    UploadResult,
    FluxoAssinaturaResult,
    ConsultaFluxoResult,
    ListaFluxosResult,
    CancelamentoResult,
    DownloadResult,
    TipoDocumento,
    TipoParticipante,
    StatusFluxo,
    Participante,
)


@pytest.mark.asyncio
class TestAsyncENotariadoResource:
    """Tests for AsyncENotariadoResource."""

    async def test_initialization(self):
        """AsyncENotariadoResource initializes with client."""
        mock_client = AsyncMock()
        enot = AsyncENotariadoResource(mock_client)
        assert enot._client == mock_client
        assert enot.ENDPOINT_PREFIX == "/v1/enotariado"


@pytest.mark.asyncio
class TestAsyncENotariadoUpload:
    """Tests for async upload."""

    async def test_upload_documento(self):
        """Upload document."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "success": True,
            "upload_id": "upload_123",
            "filename": "escritura.pdf",
            "size_bytes": 1024,
            "content_type": "application/pdf",
        }

        enot = AsyncENotariadoResource(mock_client)
        pdf_bytes = b"fake_pdf_data"
        result = await enot.upload_documento(
            cartorio_id="cart_123",
            arquivo=pdf_bytes,
            nome_arquivo="escritura.pdf",
        )

        assert isinstance(result, UploadResult)
        assert result.upload_id == "upload_123"
        assert result.filename == "escritura.pdf"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/enotariado/cartorios/cart_123/uploads"


@pytest.mark.asyncio
class TestAsyncENotariadoFluxos:
    """Tests for async fluxos."""

    async def test_criar_fluxo(self, enotariado_fluxo_response):
        """Create signing flow."""
        mock_client = AsyncMock()
        mock_client.post.return_value = enotariado_fluxo_response

        enot = AsyncENotariadoResource(mock_client)
        participantes = [
            Participante(
                cpf="12345678909",
                nome="João Silva",
                email="joao@example.com",
                tipo=TipoParticipante.OUTORGANTE,
            )
        ]
        result = await enot.criar_fluxo(
            cartorio_id="cart_123",
            upload_id="upload_123",
            tipo=TipoDocumento.ESCRITURA,
            participantes=participantes,
            titulo="Escritura de Compra e Venda",
        )

        assert isinstance(result, FluxoAssinaturaResult)
        assert result.fluxo_id == "fluxo_abc123"
        assert result.mne == "ABC123XYZ"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/enotariado/cartorios/cart_123/fluxos"

    async def test_consultar_fluxo(self):
        """Query signing flow."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "fluxo_id": "fluxo_123",
            "mne": "ABC123",
            "status": "Pending",
            "tipo_documento": "Deed",
            "participantes": [],
            "assinaturas_pendentes": 2,
            "assinaturas_concluidas": 0,
        }

        enot = AsyncENotariadoResource(mock_client)
        result = await enot.consultar_fluxo("cart_123", "fluxo_123")

        assert isinstance(result, ConsultaFluxoResult)
        assert result.fluxo_id == "fluxo_123"
        mock_client.get.assert_called_once()

    async def test_listar_fluxos(self):
        """List signing flows."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "fluxos": [
                {"fluxo_id": "fluxo_1", "status": "Pending"},
                {"fluxo_id": "fluxo_2", "status": "Concluded"},
            ],
            "total": 2,
            "pagina": 1,
        }

        enot = AsyncENotariadoResource(mock_client)
        result = await enot.listar_fluxos("cart_123")

        assert isinstance(result, ListaFluxosResult)
        assert result.total == 2
        mock_client.get.assert_called_once()

    async def test_listar_fluxos_with_filters(self):
        """List flows with filters."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"success": True, "fluxos": [], "total": 0}

        enot = AsyncENotariadoResource(mock_client)
        result = await enot.listar_fluxos(
            "cart_123",
            status=StatusFluxo.AGUARDANDO,
            tipo=TipoDocumento.ESCRITURA,
            concluidos=False,
        )

        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["status"] == "Pending"
        assert call_args[1]["params"]["tipo_documento"] == "Deed"


@pytest.mark.asyncio
class TestAsyncENotariadoDownload:
    """Tests for async download."""

    async def test_download_assinado(self):
        """Download signed document."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "success": True,
            "mne": "ABC123",
            "arquivo_bytes": b"signed_pdf_data",
            "nome_arquivo": "escritura_assinada.pdf",
        }

        enot = AsyncENotariadoResource(mock_client)
        result = await enot.download_assinado("cart_123", "fluxo_123")

        assert isinstance(result, DownloadResult)
        assert result.arquivo_bytes == b"signed_pdf_data"
        mock_client.get.assert_called_once()


@pytest.mark.asyncio
class TestAsyncENotariadoGerenciamento:
    """Tests for async management."""

    async def test_cancelar_fluxo(self):
        """Cancel flow."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "success": True,
            "cancelado_em": "2026-01-27T20:00:00Z",
        }

        enot = AsyncENotariadoResource(mock_client)
        result = await enot.cancelar_fluxo("cart_123", "fluxo_123", "Erro no documento")

        assert isinstance(result, CancelamentoResult)
        assert result.motivo == "Erro no documento"
        mock_client.post.assert_called_once()

    async def test_reenviar_notificacao(self):
        """Resend notification."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": True}

        enot = AsyncENotariadoResource(mock_client)
        result = await enot.reenviar_notificacao(
            "cart_123", "fluxo_123", "12345678909"
        )

        assert result["success"] is True
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["participante_cpf"] == "12345678909"


@pytest.mark.asyncio
class TestAsyncENotariadoAtos:
    """Tests for async specific acts."""

    async def test_criar_escritura(self, enotariado_fluxo_response):
        """Create escritura flow."""
        mock_client = AsyncMock()
        mock_client.post.return_value = enotariado_fluxo_response

        enot = AsyncENotariadoResource(mock_client)
        outorgantes = [Participante(cpf="12345678909", nome="João", email="joao@test.com", tipo=TipoParticipante.OUTORGANTE)]
        outorgados = [Participante(cpf="98765432100", nome="Maria", email="maria@test.com", tipo=TipoParticipante.OUTORGADO)]
        
        result = await enot.criar_escritura(
            cartorio_id="cart_123",
            upload_id="upload_123",
            outorgantes=outorgantes,
            outorgados=outorgados,
            titulo="Escritura de Venda",
        )

        assert isinstance(result, FluxoAssinaturaResult)
        assert result.tipo_documento == TipoDocumento.ESCRITURA

    async def test_criar_procuracao(self, enotariado_fluxo_response):
        """Create procuracao flow."""
        mock_client = AsyncMock()
        mock_client.post.return_value = enotariado_fluxo_response

        enot = AsyncENotariadoResource(mock_client)
        outorgante = Participante(cpf="12345678909", nome="João", email="joao@test.com", tipo=TipoParticipante.OUTORGANTE)
        outorgados = [Participante(cpf="98765432100", nome="Maria", email="maria@test.com", tipo=TipoParticipante.OUTORGADO)]
        
        result = await enot.criar_procuracao(
            cartorio_id="cart_123",
            upload_id="upload_123",
            outorgante=outorgante,
            outorgados=outorgados,
            poderes="Poderes para administrar",
        )

        assert isinstance(result, FluxoAssinaturaResult)
        assert result.tipo_documento == TipoDocumento.PROCURACAO

    async def test_criar_ata_notarial(self, enotariado_fluxo_response):
        """Create ata notarial flow."""
        mock_client = AsyncMock()
        mock_client.post.return_value = enotariado_fluxo_response

        enot = AsyncENotariadoResource(mock_client)
        solicitante = Participante(cpf="12345678909", nome="João", email="joao@test.com", tipo=TipoParticipante.OUTORGANTE)
        
        result = await enot.criar_ata_notarial(
            cartorio_id="cart_123",
            upload_id="upload_123",
            solicitante=solicitante,
            objeto="Constatação de abandono",
        )

        assert isinstance(result, FluxoAssinaturaResult)
        assert result.tipo_documento == TipoDocumento.ATA_NOTARIAL
