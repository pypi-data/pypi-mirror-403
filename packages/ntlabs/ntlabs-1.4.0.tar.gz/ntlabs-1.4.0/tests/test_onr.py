"""
Tests for ONR/SREI Resource (Registro de Imóveis).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ntlabs.resources.registros.async_onr import AsyncONRResource
from ntlabs.resources.registros.onr import (
    CertidaoResult,
    MatriculaInfo,
    ONRResource,
    ProtocoloResult,
    StatusCertidao,
    StatusProtocolo,
    TipoCertidao,
    TipoPenhora,
    TipoProtocolo,
)

# =============================================================================
# Test Enums
# =============================================================================


class TestEnums:
    """Test enum values."""

    def test_tipo_certidao_values(self):
        """Test certificate types."""
        assert TipoCertidao.MATRICULA.value == "matricula"
        assert TipoCertidao.MATRICULA_ATUALIZADA.value == "matricula_atualizada"
        assert TipoCertidao.ONUS_ACOES.value == "onus_acoes"
        assert TipoCertidao.NEGATIVA.value == "negativa"
        assert TipoCertidao.PROPRIEDADE.value == "propriedade"
        assert TipoCertidao.LIVRO_3.value == "livro_3"
        assert TipoCertidao.INTEIRO_TEOR.value == "inteiro_teor"

    def test_status_certidao_values(self):
        """Test certificate status values."""
        assert StatusCertidao.SOLICITADA.value == "solicitada"
        assert StatusCertidao.EM_PROCESSAMENTO.value == "em_processamento"
        assert StatusCertidao.DISPONIVEL.value == "disponivel"
        assert StatusCertidao.EXPIRADA.value == "expirada"
        assert StatusCertidao.CANCELADA.value == "cancelada"

    def test_tipo_protocolo_values(self):
        """Test protocol types."""
        assert TipoProtocolo.REGISTRO.value == "registro"
        assert TipoProtocolo.AVERBACAO.value == "averbacao"
        assert TipoProtocolo.CANCELAMENTO.value == "cancelamento"
        assert TipoProtocolo.RETIFICACAO.value == "retificacao"

    def test_status_protocolo_values(self):
        """Test protocol status values."""
        assert StatusProtocolo.PRENOTADO.value == "prenotado"
        assert StatusProtocolo.EM_ANALISE.value == "em_analise"
        assert StatusProtocolo.EXIGENCIA.value == "exigencia"
        assert StatusProtocolo.REGISTRADO.value == "registrado"
        assert StatusProtocolo.DEVOLVIDO.value == "devolvido"

    def test_tipo_penhora_values(self):
        """Test pledge types."""
        assert TipoPenhora.JUDICIAL.value == "judicial"
        assert TipoPenhora.ADMINISTRATIVA.value == "administrativa"
        assert TipoPenhora.ARRESTO.value == "arresto"
        assert TipoPenhora.SEQUESTRO.value == "sequestro"


# =============================================================================
# Test Dataclasses
# =============================================================================


class TestMatriculaInfo:
    """Test MatriculaInfo dataclass."""

    def test_create_matricula_info(self):
        """Test creating matricula info."""
        info = MatriculaInfo(
            matricula="1234",
            serventia="1º Registro de Imóveis",
            cns="12345",
            uf="MG",
            municipio="Belo Horizonte",
            area=100.5,
            endereco="Rua Teste, 123",
            proprietarios=[{"nome": "João Silva", "cpf": "123.456.789-00"}],
        )
        assert info.matricula == "1234"
        assert info.cns == "12345"
        assert info.area == 100.5

    def test_matricula_info_to_dict(self):
        """Test matricula info serialization."""
        info = MatriculaInfo(
            matricula="1234",
            serventia="1º RI",
            cns="12345",
            uf="SP",
            municipio="São Paulo",
        )
        d = info.to_dict()
        assert d["matricula"] == "1234"
        assert d["uf"] == "SP"


class TestCertidaoResult:
    """Test CertidaoResult dataclass."""

    def test_certidao_result_to_dict(self):
        """Test certificate result serialization."""
        result = CertidaoResult(
            success=True,
            pedido_id="pedido-123",
            tipo=TipoCertidao.ONUS_ACOES,
            matricula="1234",
            serventia="1º RI",
            status=StatusCertidao.DISPONIVEL,
            solicitado_em="2026-01-25T10:00:00Z",
            valor=50.0,
        )
        d = result.to_dict()
        assert d["tipo"] == "onus_acoes"
        assert d["status"] == "disponivel"
        assert d["valor"] == 50.0


class TestProtocoloResult:
    """Test ProtocoloResult dataclass."""

    def test_protocolo_result_to_dict(self):
        """Test protocol result serialization."""
        result = ProtocoloResult(
            success=True,
            protocolo="PROT-2026-001",
            numero_prenotacao="12345",
            tipo=TipoProtocolo.REGISTRO,
            matricula="1234",
            serventia="1º RI",
            status=StatusProtocolo.PRENOTADO,
            prenotado_em="2026-01-25T10:00:00Z",
            exigencias=["Documentos pessoais", "Comprovante de pagamento"],
        )
        d = result.to_dict()
        assert d["tipo"] == "registro"
        assert d["status"] == "prenotado"
        assert len(d["exigencias"]) == 2


# =============================================================================
# Test Sync Resource
# =============================================================================


class TestONRResource:
    """Test sync ONR resource."""

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
        return ONRResource(mock_client)

    def test_consultar_matricula(self, resource, mock_client):
        """Test querying matricula info."""
        mock_client.get.return_value = {
            "matricula": "1234",
            "serventia": "1º RI de BH",
            "cns": "12345",
            "uf": "MG",
            "municipio": "Belo Horizonte",
            "area": 200.0,
            "proprietarios": [{"nome": "Maria", "cpf": "987.654.321-00"}],
            "onus": [],
        }

        result = resource.consultar_matricula("123", "12345", "1234")

        assert result.matricula == "1234"
        assert result.uf == "MG"
        assert len(result.proprietarios) == 1
        mock_client.get.assert_called_once()

    def test_visualizar_matricula(self, resource, mock_client):
        """Test viewing matricula (free preview)."""
        mock_client.get.return_value = {
            "matricula": "1234",
            "serventia": "1º RI",
            "uf": "SP",
        }

        result = resource.visualizar_matricula("123", "12345", "1234")

        assert result["matricula"] == "1234"

    def test_solicitar_certidao(self, resource, mock_client):
        """Test requesting certificate."""
        mock_client.post.return_value = {
            "success": True,
            "pedido_id": "pedido-abc",
            "serventia": "1º RI",
            "status": "solicitada",
            "solicitado_em": "2026-01-25T10:00:00Z",
            "valor": 75.50,
        }

        result = resource.solicitar_certidao(
            cartorio_id="123",
            cns_destino="12345",
            matricula="1234",
            tipo=TipoCertidao.MATRICULA_ATUALIZADA,
        )

        assert result.success is True
        assert result.pedido_id == "pedido-abc"
        assert result.tipo == TipoCertidao.MATRICULA_ATUALIZADA
        assert result.valor == 75.50

    def test_consultar_certidao(self, resource, mock_client):
        """Test querying certificate status."""
        mock_client.get.return_value = {
            "success": True,
            "tipo": "matricula",
            "matricula": "1234",
            "serventia": "1º RI",
            "status": "disponivel",
            "solicitado_em": "2026-01-25T10:00:00Z",
            "url_download": "https://example.com/cert.pdf",
            "codigo_verificacao": "ABC123",
        }

        result = resource.consultar_certidao("123", "pedido-abc")

        assert result.status == StatusCertidao.DISPONIVEL
        assert result.url_download is not None
        assert result.codigo_verificacao == "ABC123"

    def test_buscar_propriedades(self, resource, mock_client):
        """Test searching properties by CPF."""
        mock_client.get.return_value = {
            "success": True,
            "total": 2,
            "imoveis": [
                {"matricula": "1234", "cns": "12345", "municipio": "BH"},
                {"matricula": "5678", "cns": "12345", "municipio": "BH"},
            ],
        }

        result = resource.buscar_propriedades("123", cpf="123.456.789-00")

        assert result.success is True
        assert result.total == 2
        assert len(result.imoveis) == 2

    def test_criar_protocolo(self, resource, mock_client):
        """Test creating e-protocolo."""
        mock_client.post.return_value = {
            "success": True,
            "protocolo": "PROT-2026-001",
            "numero_prenotacao": "12345",
            "serventia": "1º RI",
            "status": "prenotado",
            "prenotado_em": "2026-01-25T10:00:00Z",
        }

        result = resource.criar_protocolo(
            cartorio_id="123",
            cns_destino="12345",
            matricula="1234",
            tipo=TipoProtocolo.REGISTRO,
            documento_id="doc-abc",
            titulo="Escritura de Compra e Venda",
        )

        assert result.success is True
        assert result.protocolo == "PROT-2026-001"
        assert result.status == StatusProtocolo.PRENOTADO

    def test_consultar_protocolo(self, resource, mock_client):
        """Test querying protocol status."""
        mock_client.get.return_value = {
            "success": True,
            "numero_prenotacao": "12345",
            "tipo": "registro",
            "matricula": "1234",
            "serventia": "1º RI",
            "status": "exigencia",
            "prenotado_em": "2026-01-25T10:00:00Z",
            "prazo_exigencia": "2026-02-01",
            "exigencias": ["Comprovante de ITBI"],
        }

        result = resource.consultar_protocolo("123", "PROT-2026-001")

        assert result.status == StatusProtocolo.EXIGENCIA
        assert len(result.exigencias) == 1

    def test_responder_exigencia(self, resource, mock_client):
        """Test responding to protocol requirement."""
        mock_client.post.return_value = {
            "success": True,
            "numero_prenotacao": "12345",
            "tipo": "registro",
            "matricula": "1234",
            "serventia": "1º RI",
            "status": "em_analise",
            "prenotado_em": "2026-01-25T10:00:00Z",
        }

        result = resource.responder_exigencia(
            cartorio_id="123",
            protocolo="PROT-2026-001",
            documento_id="doc-resposta",
            observacao="ITBI quitado",
        )

        assert result.status == StatusProtocolo.EM_ANALISE

    def test_consultar_penhora(self, resource, mock_client):
        """Test querying pledges."""
        mock_client.get.return_value = {
            "penhoras": [
                {
                    "codigo": "PEN-001",
                    "tipo": "judicial",
                    "serventia": "1º RI",
                    "valor": 100000.0,
                    "processo": "0001234-56.2026.8.13.0000",
                    "credor": "Banco X",
                    "devedor": "João Silva",
                    "registrado_em": "2026-01-20T10:00:00Z",
                }
            ]
        }

        result = resource.consultar_penhora("123", "12345", "1234")

        assert len(result) == 1
        assert result[0].tipo == TipoPenhora.JUDICIAL
        assert result[0].valor == 100000.0

    def test_registrar_penhora(self, resource, mock_client):
        """Test registering pledge."""
        mock_client.post.return_value = {
            "success": True,
            "codigo": "PEN-002",
            "serventia": "1º RI",
            "registrado_em": "2026-01-25T11:00:00Z",
        }

        result = resource.registrar_penhora(
            cartorio_id="123",
            cns="12345",
            matricula="1234",
            tipo=TipoPenhora.JUDICIAL,
            processo="0001234-56.2026.8.13.0001",
            vara="1ª Vara Cível",
            credor="Empresa Y",
            devedor="Maria Santos",
            valor=50000.0,
        )

        assert result.success is True
        assert result.codigo == "PEN-002"

    def test_consultar_indisponibilidade(self, resource, mock_client):
        """Test querying CNIB unavailability."""
        mock_client.get.return_value = {
            "success": True,
            "nome": "José Oliveira",
            "possui_indisponibilidade": True,
            "indisponibilidades": [{"origem": "Receita Federal", "data": "2025-12-01"}],
            "consultado_em": "2026-01-25T10:00:00Z",
        }

        result = resource.consultar_indisponibilidade(
            cartorio_id="123",
            cpf="111.222.333-44",
        )

        assert result.possui_indisponibilidade is True
        assert len(result.indisponibilidades) == 1

    def test_enviar_oficio(self, resource, mock_client):
        """Test sending electronic letter."""
        mock_client.post.return_value = {
            "success": True,
            "oficio_id": "OF-2026-001",
            "tipo": "enviado",
            "origem": "1º RI BH",
            "destino": "2º RI BH",
            "status": "enviado",
            "enviado_em": "2026-01-25T10:00:00Z",
        }

        result = resource.enviar_oficio(
            cartorio_id="123",
            cns_destino="12346",
            assunto="Solicitação de Informação",
            conteudo="Prezados, solicito...",
        )

        assert result.success is True
        assert result.oficio_id == "OF-2026-001"

    def test_consultar_oficio(self, resource, mock_client):
        """Test querying electronic letter."""
        mock_client.get.return_value = {
            "success": True,
            "tipo": "recebido",
            "origem": "2º RI",
            "destino": "1º RI",
            "assunto": "Resposta",
            "status": "respondido",
            "enviado_em": "2026-01-24T10:00:00Z",
            "respondido_em": "2026-01-25T09:00:00Z",
            "resposta": "Segue em anexo...",
        }

        result = resource.consultar_oficio("123", "OF-2026-001")

        assert result.status == "respondido"
        assert result.resposta is not None


# =============================================================================
# Test Async Resource
# =============================================================================


class TestAsyncONRResource:
    """Test async ONR resource."""

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
        return AsyncONRResource(mock_async_client)

    @pytest.mark.asyncio
    async def test_async_consultar_matricula(self, async_resource, mock_async_client):
        """Test async querying matricula."""
        mock_async_client.get.return_value = {
            "matricula": "5678",
            "serventia": "2º RI",
            "cns": "54321",
            "uf": "SP",
            "municipio": "São Paulo",
            "proprietarios": [],
        }

        result = await async_resource.consultar_matricula("123", "54321", "5678")

        assert result.matricula == "5678"
        assert result.uf == "SP"

    @pytest.mark.asyncio
    async def test_async_solicitar_certidao(self, async_resource, mock_async_client):
        """Test async certificate request."""
        mock_async_client.post.return_value = {
            "success": True,
            "pedido_id": "async-pedido",
            "serventia": "2º RI",
            "status": "solicitada",
            "solicitado_em": "2026-01-25T10:00:00Z",
        }

        result = await async_resource.solicitar_certidao(
            cartorio_id="123",
            cns_destino="54321",
            matricula="5678",
            tipo=TipoCertidao.NEGATIVA,
        )

        assert result.pedido_id == "async-pedido"
        assert result.tipo == TipoCertidao.NEGATIVA

    @pytest.mark.asyncio
    async def test_async_buscar_propriedades(self, async_resource, mock_async_client):
        """Test async property search."""
        mock_async_client.get.return_value = {
            "success": True,
            "total": 1,
            "imoveis": [{"matricula": "9999", "cns": "11111"}],
        }

        result = await async_resource.buscar_propriedades(
            cartorio_id="123",
            cnpj="12.345.678/0001-90",
        )

        assert result.total == 1

    @pytest.mark.asyncio
    async def test_async_criar_protocolo(self, async_resource, mock_async_client):
        """Test async e-protocolo creation."""
        mock_async_client.post.return_value = {
            "success": True,
            "protocolo": "ASYNC-PROT-001",
            "numero_prenotacao": "99999",
            "serventia": "2º RI",
            "status": "prenotado",
            "prenotado_em": "2026-01-25T10:00:00Z",
        }

        result = await async_resource.criar_protocolo(
            cartorio_id="123",
            cns_destino="54321",
            matricula="5678",
            tipo=TipoProtocolo.AVERBACAO,
            documento_id="doc-xyz",
            titulo="Averbação de Construção",
        )

        assert result.protocolo == "ASYNC-PROT-001"
        assert result.tipo == TipoProtocolo.AVERBACAO

    @pytest.mark.asyncio
    async def test_async_consultar_indisponibilidade(
        self, async_resource, mock_async_client
    ):
        """Test async CNIB query."""
        mock_async_client.get.return_value = {
            "success": True,
            "nome": "Empresa ABC",
            "possui_indisponibilidade": False,
            "indisponibilidades": [],
            "consultado_em": "2026-01-25T10:00:00Z",
        }

        result = await async_resource.consultar_indisponibilidade(
            cartorio_id="123",
            cnpj="12.345.678/0001-90",
        )

        assert result.possui_indisponibilidade is False
        assert len(result.indisponibilidades) == 0

    @pytest.mark.asyncio
    async def test_async_registrar_penhora(self, async_resource, mock_async_client):
        """Test async pledge registration."""
        mock_async_client.post.return_value = {
            "success": True,
            "codigo": "ASYNC-PEN-001",
            "serventia": "2º RI",
            "registrado_em": "2026-01-25T12:00:00Z",
        }

        result = await async_resource.registrar_penhora(
            cartorio_id="123",
            cns="54321",
            matricula="5678",
            tipo=TipoPenhora.ARRESTO,
            processo="0009999-88.2026.8.26.0000",
            vara="Vara de Execuções",
            credor="Credor XYZ",
            devedor="Devedor ABC",
        )

        assert result.codigo == "ASYNC-PEN-001"
        assert result.tipo == TipoPenhora.ARRESTO

    @pytest.mark.asyncio
    async def test_async_enviar_oficio(self, async_resource, mock_async_client):
        """Test async sending electronic letter."""
        mock_async_client.post.return_value = {
            "success": True,
            "oficio_id": "ASYNC-OF-001",
            "tipo": "enviado",
            "origem": "2º RI",
            "destino": "3º RI",
            "status": "enviado",
            "enviado_em": "2026-01-25T10:00:00Z",
        }

        result = await async_resource.enviar_oficio(
            cartorio_id="123",
            cns_destino="99999",
            assunto="Consulta Urgente",
            conteudo="Prezados...",
            urgente=True,
        )

        assert result.oficio_id == "ASYNC-OF-001"

    @pytest.mark.asyncio
    async def test_async_consultar_penhora(self, async_resource, mock_async_client):
        """Test async pledge query."""
        mock_async_client.get.return_value = {
            "penhoras": [
                {
                    "codigo": "PEN-ASYNC",
                    "tipo": "administrativa",
                    "serventia": "2º RI",
                    "valor": 25000.0,
                    "processo": "PAD-001",
                }
            ]
        }

        result = await async_resource.consultar_penhora("123", "54321", "5678")

        assert len(result) == 1
        assert result[0].tipo == TipoPenhora.ADMINISTRATIVA
