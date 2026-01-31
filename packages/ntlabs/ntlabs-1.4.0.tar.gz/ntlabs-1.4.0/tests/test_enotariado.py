"""
Tests for e-Notariado Resource (Fluxo de Assinaturas).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ntlabs.resources.registros.async_enotariado import AsyncENotariadoResource
from ntlabs.resources.registros.enotariado import (
    DownloadResult,
    ENotariadoResource,
    FluxoAssinaturaResult,
    Participante,
    StatusFluxo,
    TipoAssinatura,
    TipoDocumento,
    TipoParticipante,
    UploadResult,
)

# =============================================================================
# Test Enums
# =============================================================================


class TestEnums:
    """Test enum values."""

    def test_tipo_documento_values(self):
        """Test document types."""
        assert TipoDocumento.ESCRITURA.value == "Deed"
        assert TipoDocumento.PROCURACAO.value == "PowerOfAttorney"
        assert TipoDocumento.ATA_NOTARIAL.value == "NotarialMinutes"
        assert TipoDocumento.TESTAMENTO.value == "Will"
        assert TipoDocumento.SUBSTABELECIMENTO.value == "SubPowerOfAttorney"
        assert TipoDocumento.REVOGACAO.value == "Revocation"
        assert TipoDocumento.APOSTILA.value == "Apostille"

    def test_tipo_assinatura_values(self):
        """Test signature types."""
        assert TipoAssinatura.ICP_BRASIL.value == "IcpBrasil"
        assert TipoAssinatura.NOTARIZADO.value == "Notarized"
        assert TipoAssinatura.VIDEOCONFERENCIA.value == "VideoConference"
        assert TipoAssinatura.PRESENCIAL.value == "InPerson"

    def test_status_fluxo_values(self):
        """Test flow status values."""
        assert StatusFluxo.CRIADO.value == "Created"
        assert StatusFluxo.AGUARDANDO.value == "Pending"
        assert StatusFluxo.EM_ANDAMENTO.value == "InProgress"
        assert StatusFluxo.CONCLUIDO.value == "Concluded"
        assert StatusFluxo.CANCELADO.value == "Canceled"
        assert StatusFluxo.EXPIRADO.value == "Expired"

    def test_tipo_participante_values(self):
        """Test participant types."""
        assert TipoParticipante.OUTORGANTE.value == "Grantor"
        assert TipoParticipante.OUTORGADO.value == "Grantee"
        assert TipoParticipante.TESTEMUNHA.value == "Witness"
        assert TipoParticipante.TABELIAO.value == "Notary"
        assert TipoParticipante.PREPOSTO.value == "Clerk"
        assert TipoParticipante.INTERVENIENTE.value == "Intervening"


# =============================================================================
# Test Dataclasses
# =============================================================================


class TestParticipante:
    """Test Participante dataclass."""

    def test_create_participante(self):
        """Test creating a participant."""
        p = Participante(
            nome="João Silva",
            cpf="123.456.789-00",
            email="joao@email.com",
            tipo=TipoParticipante.OUTORGANTE,
        )
        assert p.nome == "João Silva"
        assert p.cpf == "123.456.789-00"
        assert p.tipo == TipoParticipante.OUTORGANTE
        assert p.tipo_assinatura == TipoAssinatura.NOTARIZADO
        assert p.ordem == 1

    def test_participante_to_dict(self):
        """Test participant to_dict method."""
        p = Participante(
            nome="Maria Santos",
            cpf="987.654.321-00",
            email="maria@email.com",
            tipo=TipoParticipante.OUTORGADO,
            telefone="11999999999",
            ordem=2,
        )
        result = p.to_dict()
        assert result["nome"] == "Maria Santos"
        assert result["tipo"] == "Grantee"
        assert result["tipo_assinatura"] == "Notarized"
        assert result["telefone"] == "11999999999"
        assert result["ordem"] == 2


class TestUploadResult:
    """Test UploadResult dataclass."""

    def test_upload_result_to_dict(self):
        """Test upload result serialization."""
        result = UploadResult(
            success=True,
            upload_id="upload-123",
            filename="escritura.pdf",
            size_bytes=1024,
            content_type="application/pdf",
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["upload_id"] == "upload-123"
        assert d["filename"] == "escritura.pdf"


class TestFluxoAssinaturaResult:
    """Test FluxoAssinaturaResult dataclass."""

    def test_fluxo_result_to_dict(self):
        """Test flow result serialization."""
        result = FluxoAssinaturaResult(
            success=True,
            fluxo_id="fluxo-abc",
            mne="MNE-2026-001",
            status=StatusFluxo.CRIADO,
            tipo_documento=TipoDocumento.ESCRITURA,
            participantes=[{"nome": "João"}],
            criado_em="2026-01-25T10:00:00Z",
        )
        d = result.to_dict()
        assert d["status"] == "Created"
        assert d["tipo_documento"] == "Deed"
        assert d["mne"] == "MNE-2026-001"


class TestDownloadResult:
    """Test DownloadResult dataclass."""

    def test_download_result_to_dict_excludes_bytes(self):
        """Test download result excludes bytes in to_dict."""
        result = DownloadResult(
            success=True,
            fluxo_id="fluxo-abc",
            mne="MNE-2026-001",
            arquivo_bytes=b"PDF content here...",
            nome_arquivo="documento_assinado.pdf",
            content_type="application/pdf",
        )
        d = result.to_dict()
        assert "arquivo_bytes" not in d
        assert "tamanho_bytes" in d
        assert d["tamanho_bytes"] == 19


# =============================================================================
# Test Sync Resource
# =============================================================================


class TestENotariadoResource:
    """Test sync e-Notariado resource."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client."""
        client = MagicMock()
        client.post = MagicMock()
        client.get = MagicMock()
        return client

    @pytest.fixture
    def resource(self, mock_client):
        """Create resource with mock client."""
        return ENotariadoResource(mock_client)

    def test_upload_documento(self, resource, mock_client):
        """Test document upload."""
        mock_client.post.return_value = {
            "success": True,
            "upload_id": "upload-123",
            "filename": "escritura.pdf",
            "size_bytes": 2048,
            "content_type": "application/pdf",
        }

        result = resource.upload_documento(
            cartorio_id="123",
            arquivo=b"PDF content",
            nome_arquivo="escritura.pdf",
        )

        assert result.success is True
        assert result.upload_id == "upload-123"
        mock_client.post.assert_called_once()

    def test_criar_fluxo(self, resource, mock_client):
        """Test flow creation."""
        mock_client.post.return_value = {
            "success": True,
            "fluxo_id": "fluxo-abc",
            "mne": "MNE-2026-001",
            "status": "Created",
            "participantes": [],
            "criado_em": "2026-01-25T10:00:00Z",
        }

        participantes = [
            Participante(
                nome="João",
                cpf="123.456.789-00",
                email="joao@email.com",
                tipo=TipoParticipante.OUTORGANTE,
            )
        ]

        result = resource.criar_fluxo(
            cartorio_id="123",
            upload_id="upload-123",
            tipo=TipoDocumento.ESCRITURA,
            participantes=participantes,
            titulo="Escritura de Compra e Venda",
        )

        assert result.success is True
        assert result.fluxo_id == "fluxo-abc"
        assert result.status == StatusFluxo.CRIADO

    def test_consultar_fluxo(self, resource, mock_client):
        """Test flow query."""
        mock_client.get.return_value = {
            "success": True,
            "mne": "MNE-2026-001",
            "status": "InProgress",
            "tipo_documento": "Deed",
            "participantes": [],
            "assinaturas_pendentes": 2,
            "assinaturas_concluidas": 1,
            "criado_em": "2026-01-25T10:00:00Z",
            "atualizado_em": "2026-01-25T11:00:00Z",
        }

        result = resource.consultar_fluxo("123", "fluxo-abc")

        assert result.success is True
        assert result.status == StatusFluxo.EM_ANDAMENTO
        assert result.assinaturas_pendentes == 2
        assert result.assinaturas_concluidas == 1

    def test_listar_fluxos(self, resource, mock_client):
        """Test flow listing."""
        mock_client.get.return_value = {
            "success": True,
            "fluxos": [
                {
                    "fluxo_id": "fluxo-1",
                    "status": "Concluded",
                    "tipo_documento": "Deed",
                    "participantes": [],
                    "assinaturas_pendentes": 0,
                    "assinaturas_concluidas": 3,
                    "criado_em": "2026-01-20T10:00:00Z",
                    "atualizado_em": "2026-01-21T15:00:00Z",
                },
                {
                    "fluxo_id": "fluxo-2",
                    "status": "Pending",
                    "tipo_documento": "PowerOfAttorney",
                    "participantes": [],
                    "assinaturas_pendentes": 1,
                    "assinaturas_concluidas": 0,
                    "criado_em": "2026-01-25T10:00:00Z",
                    "atualizado_em": "2026-01-25T10:00:00Z",
                },
            ],
            "total": 2,
        }

        result = resource.listar_fluxos("123", concluidos=None)

        assert result.success is True
        assert len(result.fluxos) == 2
        assert result.total == 2
        assert result.fluxos[0].status == StatusFluxo.CONCLUIDO
        assert result.fluxos[1].status == StatusFluxo.AGUARDANDO

    def test_download_assinado(self, resource, mock_client):
        """Test signed document download."""
        mock_client.get.return_value = {
            "success": True,
            "mne": "MNE-2026-001",
            "arquivo_bytes": b"PDF assinado content",
            "nome_arquivo": "escritura_assinada.pdf",
            "content_type": "application/pdf",
            "hash_arquivo": "abc123hash",
        }

        result = resource.download_assinado("123", "fluxo-abc")

        assert result.success is True
        assert result.mne == "MNE-2026-001"
        assert len(result.arquivo_bytes) > 0
        assert result.hash_arquivo == "abc123hash"

    def test_cancelar_fluxo(self, resource, mock_client):
        """Test flow cancellation."""
        mock_client.post.return_value = {
            "success": True,
            "cancelado_em": "2026-01-25T12:00:00Z",
        }

        result = resource.cancelar_fluxo(
            cartorio_id="123",
            fluxo_id="fluxo-abc",
            motivo="Erro nos dados do outorgante",
        )

        assert result.success is True
        assert result.status == StatusFluxo.CANCELADO
        assert result.motivo == "Erro nos dados do outorgante"

    def test_reenviar_notificacao(self, resource, mock_client):
        """Test notification resend."""
        mock_client.post.return_value = {
            "success": True,
            "mensagem": "Notificação reenviada",
        }

        result = resource.reenviar_notificacao(
            cartorio_id="123",
            fluxo_id="fluxo-abc",
            participante_cpf="123.456.789-00",
        )

        assert result["success"] is True

    def test_criar_escritura(self, resource, mock_client):
        """Test deed creation helper."""
        mock_client.post.return_value = {
            "success": True,
            "fluxo_id": "fluxo-escritura",
            "status": "Created",
            "participantes": [],
            "criado_em": "2026-01-25T10:00:00Z",
        }

        outorgantes = [
            Participante(
                nome="Vendedor",
                cpf="111.111.111-11",
                email="vendedor@email.com",
                tipo=TipoParticipante.OUTORGANTE,
            )
        ]
        outorgados = [
            Participante(
                nome="Comprador",
                cpf="222.222.222-22",
                email="comprador@email.com",
                tipo=TipoParticipante.OUTORGADO,
            )
        ]

        result = resource.criar_escritura(
            cartorio_id="123",
            upload_id="upload-123",
            outorgantes=outorgantes,
            outorgados=outorgados,
            titulo="Escritura de Compra e Venda",
            livro="100",
            folha="50",
        )

        assert result.success is True
        assert result.fluxo_id == "fluxo-escritura"
        # Verify payload
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert payload["tipo_documento"] == "Deed"
        assert payload["assinatura_sequencial"] is True
        assert "livro" in payload.get("metadata", {})

    def test_criar_procuracao(self, resource, mock_client):
        """Test power of attorney creation helper."""
        mock_client.post.return_value = {
            "success": True,
            "fluxo_id": "fluxo-procuracao",
            "status": "Created",
            "participantes": [],
            "criado_em": "2026-01-25T10:00:00Z",
        }

        outorgante = Participante(
            nome="Mandante",
            cpf="111.111.111-11",
            email="mandante@email.com",
            tipo=TipoParticipante.OUTORGANTE,
        )
        outorgados = [
            Participante(
                nome="Mandatário",
                cpf="222.222.222-22",
                email="mandatario@email.com",
                tipo=TipoParticipante.OUTORGADO,
            )
        ]

        result = resource.criar_procuracao(
            cartorio_id="123",
            upload_id="upload-123",
            outorgante=outorgante,
            outorgados=outorgados,
            poderes="Poderes amplos para venda de imóvel",
            validade_dias=365,
        )

        assert result.success is True
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert payload["tipo_documento"] == "PowerOfAttorney"

    def test_criar_ata_notarial(self, resource, mock_client):
        """Test notarial minutes creation helper."""
        mock_client.post.return_value = {
            "success": True,
            "fluxo_id": "fluxo-ata",
            "status": "Created",
            "participantes": [],
            "criado_em": "2026-01-25T10:00:00Z",
        }

        solicitante = Participante(
            nome="Solicitante",
            cpf="111.111.111-11",
            email="solicitante@email.com",
            tipo=TipoParticipante.OUTORGANTE,
        )

        result = resource.criar_ata_notarial(
            cartorio_id="123",
            upload_id="upload-123",
            solicitante=solicitante,
            objeto="Constatação de conteúdo de site",
        )

        assert result.success is True
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert payload["tipo_documento"] == "NotarialMinutes"


# =============================================================================
# Test Async Resource
# =============================================================================


class TestAsyncENotariadoResource:
    """Test async e-Notariado resource."""

    @pytest.fixture
    def mock_async_client(self):
        """Create mock async client."""
        client = MagicMock()
        client.post = AsyncMock()
        client.get = AsyncMock()
        return client

    @pytest.fixture
    def async_resource(self, mock_async_client):
        """Create async resource with mock client."""
        return AsyncENotariadoResource(mock_async_client)

    @pytest.mark.asyncio
    async def test_async_upload_documento(self, async_resource, mock_async_client):
        """Test async document upload."""
        mock_async_client.post.return_value = {
            "success": True,
            "upload_id": "upload-async-123",
            "filename": "procuracao.pdf",
            "size_bytes": 4096,
            "content_type": "application/pdf",
        }

        result = await async_resource.upload_documento(
            cartorio_id="123",
            arquivo=b"PDF async content",
            nome_arquivo="procuracao.pdf",
        )

        assert result.success is True
        assert result.upload_id == "upload-async-123"

    @pytest.mark.asyncio
    async def test_async_criar_fluxo(self, async_resource, mock_async_client):
        """Test async flow creation."""
        mock_async_client.post.return_value = {
            "success": True,
            "fluxo_id": "async-fluxo-abc",
            "mne": "MNE-2026-ASYNC",
            "status": "Created",
            "participantes": [],
            "criado_em": "2026-01-25T10:00:00Z",
        }

        participantes = [
            Participante(
                nome="Async User",
                cpf="333.333.333-33",
                email="async@email.com",
                tipo=TipoParticipante.OUTORGANTE,
            )
        ]

        result = await async_resource.criar_fluxo(
            cartorio_id="123",
            upload_id="upload-123",
            tipo=TipoDocumento.PROCURACAO,
            participantes=participantes,
        )

        assert result.success is True
        assert result.fluxo_id == "async-fluxo-abc"

    @pytest.mark.asyncio
    async def test_async_consultar_fluxo(self, async_resource, mock_async_client):
        """Test async flow query."""
        mock_async_client.get.return_value = {
            "success": True,
            "status": "Concluded",
            "tipo_documento": "PowerOfAttorney",
            "participantes": [],
            "assinaturas_pendentes": 0,
            "assinaturas_concluidas": 2,
            "criado_em": "2026-01-25T10:00:00Z",
            "atualizado_em": "2026-01-25T12:00:00Z",
            "concluido_em": "2026-01-25T12:00:00Z",
        }

        result = await async_resource.consultar_fluxo("123", "fluxo-abc")

        assert result.success is True
        assert result.status == StatusFluxo.CONCLUIDO
        assert result.concluido_em is not None

    @pytest.mark.asyncio
    async def test_async_listar_fluxos(self, async_resource, mock_async_client):
        """Test async flow listing."""
        mock_async_client.get.return_value = {
            "success": True,
            "fluxos": [
                {
                    "fluxo_id": "async-fluxo-1",
                    "status": "Pending",
                    "tipo_documento": "Deed",
                    "participantes": [],
                    "assinaturas_pendentes": 3,
                    "assinaturas_concluidas": 0,
                    "criado_em": "2026-01-25T10:00:00Z",
                    "atualizado_em": "2026-01-25T10:00:00Z",
                }
            ],
            "total": 1,
        }

        result = await async_resource.listar_fluxos(
            cartorio_id="123",
            status=StatusFluxo.AGUARDANDO,
        )

        assert result.success is True
        assert len(result.fluxos) == 1

    @pytest.mark.asyncio
    async def test_async_download_assinado(self, async_resource, mock_async_client):
        """Test async signed document download."""
        mock_async_client.get.return_value = {
            "success": True,
            "mne": "MNE-ASYNC-001",
            "arquivo_bytes": b"Async PDF signed content",
            "nome_arquivo": "doc_assinado.pdf",
            "content_type": "application/pdf",
        }

        result = await async_resource.download_assinado("123", "fluxo-abc")

        assert result.success is True
        assert result.mne == "MNE-ASYNC-001"

    @pytest.mark.asyncio
    async def test_async_cancelar_fluxo(self, async_resource, mock_async_client):
        """Test async flow cancellation."""
        mock_async_client.post.return_value = {
            "success": True,
            "cancelado_em": "2026-01-25T14:00:00Z",
        }

        result = await async_resource.cancelar_fluxo(
            cartorio_id="123",
            fluxo_id="fluxo-abc",
            motivo="Desistência do negócio",
        )

        assert result.success is True
        assert result.status == StatusFluxo.CANCELADO

    @pytest.mark.asyncio
    async def test_async_criar_escritura(self, async_resource, mock_async_client):
        """Test async deed creation."""
        mock_async_client.post.return_value = {
            "success": True,
            "fluxo_id": "async-escritura",
            "status": "Created",
            "participantes": [],
            "criado_em": "2026-01-25T10:00:00Z",
        }

        outorgantes = [
            Participante(
                nome="Vendedor Async",
                cpf="444.444.444-44",
                email="vendedor.async@email.com",
                tipo=TipoParticipante.OUTORGANTE,
            )
        ]
        outorgados = [
            Participante(
                nome="Comprador Async",
                cpf="555.555.555-55",
                email="comprador.async@email.com",
                tipo=TipoParticipante.OUTORGADO,
            )
        ]

        result = await async_resource.criar_escritura(
            cartorio_id="123",
            upload_id="upload-async",
            outorgantes=outorgantes,
            outorgados=outorgados,
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_async_criar_procuracao(self, async_resource, mock_async_client):
        """Test async power of attorney creation."""
        mock_async_client.post.return_value = {
            "success": True,
            "fluxo_id": "async-procuracao",
            "status": "Created",
            "participantes": [],
            "criado_em": "2026-01-25T10:00:00Z",
        }

        outorgante = Participante(
            nome="Mandante Async",
            cpf="666.666.666-66",
            email="mandante.async@email.com",
            tipo=TipoParticipante.OUTORGANTE,
        )
        outorgados = [
            Participante(
                nome="Mandatário Async",
                cpf="777.777.777-77",
                email="mandatario.async@email.com",
                tipo=TipoParticipante.OUTORGADO,
            )
        ]

        result = await async_resource.criar_procuracao(
            cartorio_id="123",
            upload_id="upload-async",
            outorgante=outorgante,
            outorgados=outorgados,
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_async_criar_ata_notarial(self, async_resource, mock_async_client):
        """Test async notarial minutes creation."""
        mock_async_client.post.return_value = {
            "success": True,
            "fluxo_id": "async-ata",
            "status": "Created",
            "participantes": [],
            "criado_em": "2026-01-25T10:00:00Z",
        }

        solicitante = Participante(
            nome="Solicitante Async",
            cpf="888.888.888-88",
            email="solicitante.async@email.com",
            tipo=TipoParticipante.OUTORGANTE,
        )

        result = await async_resource.criar_ata_notarial(
            cartorio_id="123",
            upload_id="upload-async",
            solicitante=solicitante,
        )

        assert result.success is True
