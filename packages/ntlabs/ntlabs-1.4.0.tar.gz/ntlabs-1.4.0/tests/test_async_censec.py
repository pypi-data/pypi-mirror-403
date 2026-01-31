"""
NTLabs SDK - Async CENSEC Resource Tests
Tests for the AsyncCENSECResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
import io
from unittest.mock import AsyncMock

from ntlabs.resources.registros.async_censec import AsyncCENSECResource
from ntlabs.resources.registros.censec import (
    TestamentoResult,
    ProcuracaoResult,
    EscrituraResult,
    RegistroAtoResult,
    SinalPublicoResult,
    BuscaTestamentoResult,
    BuscaProcuracaoResult,
    BuscaEscrituraResult,
    TipoTestamento,
    TipoProcuracao,
    TipoAtoNotarial,
    StatusAto,
)


@pytest.mark.asyncio
class TestAsyncCENSECResource:
    """Tests for AsyncCENSECResource."""

    async def test_initialization(self):
        """AsyncCENSECResource initializes with client."""
        mock_client = AsyncMock()
        censec = AsyncCENSECResource(mock_client)
        assert censec._client == mock_client


@pytest.mark.asyncio
class TestAsyncCENSECTestamentos:
    """Tests for async testamentos."""

    async def test_buscar_testamentos(self):
        """Search testamentos."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "total": 1,
            "testamentos": [{"id": "test_123", "tipo": "publico"}],
            "pagina": 1,
            "por_pagina": 20,
            "latency_ms": 100,
            "cost_brl": 0.01,
        }

        censec = AsyncCENSECResource(mock_client)
        result = await censec.buscar_testamentos(
            cartorio_id="cart_123",
            cpf_testador="12345678909",
        )

        assert isinstance(result, BuscaTestamentoResult)
        assert result.total == 1
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/censec/rcto/buscar"
        assert call_args[1]["params"]["cartorio_id"] == "cart_123"
        assert call_args[1]["params"]["cpf_testador"] == "12345678909"

    async def test_consultar_testamento(self, censec_testamento_response):
        """Consult testamento."""
        mock_client = AsyncMock()
        mock_client.get.return_value = censec_testamento_response

        censec = AsyncCENSECResource(mock_client)
        result = await censec.consultar_testamento("cart_123", "TEST123")

        assert isinstance(result, TestamentoResult)
        assert result.testador_nome == "João Silva"
        assert result.tipo == TipoTestamento.PUBLICO
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/censec/rcto/TEST123"

    async def test_existe_testamento(self):
        """Check if testamento exists."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"existe": True, "quantidade": 1}

        censec = AsyncCENSECResource(mock_client)
        result = await censec.existe_testamento("cart_123", "12345678909")

        assert result["existe"] is True
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/censec/rcto/existe/12345678909"

    async def test_registrar_testamento(self):
        """Register testamento."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "id": "test_123",
            "protocolo": "PROT123",
            "status": "registrado",
            "data_registro": "2026-01-27",
        }

        censec = AsyncCENSECResource(mock_client)
        result = await censec.registrar_testamento(
            cartorio_id="cart_123",
            tipo="publico",
            testador={"nome": "João Silva", "cpf": "12345678909"},
            data_lavratura="2026-01-15",
            livro="A-1",
            folha="10",
            dados_testamento={"clausulas": ["Cláusula 1"]},
        )

        assert isinstance(result, RegistroAtoResult)
        assert result.tipo == TipoAtoNotarial.TESTAMENTO
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/censec/rcto/registrar"

    async def test_revogar_testamento(self):
        """Revoke testamento."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": True}

        censec = AsyncCENSECResource(mock_client)
        result = await censec.revogar_testamento(
            cartorio_id="cart_123",
            codigo_testamento="TEST123",
            motivo="Novo testamento",
        )

        assert result["success"] is True
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/censec/rcto/revogar"


@pytest.mark.asyncio
class TestAsyncCENSECProcuracoes:
    """Tests for async procuracoes."""

    async def test_buscar_procuracoes(self):
        """Search procuracoes."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "total": 2,
            "procuracoes": [{"id": "proc_123"}, {"id": "proc_456"}],
            "pagina": 1,
            "por_pagina": 20,
        }

        censec = AsyncCENSECResource(mock_client)
        result = await censec.buscar_procuracoes(
            cartorio_id="cart_123",
            cpf_outorgante="12345678909",
            vigentes_apenas=True,
        )

        assert isinstance(result, BuscaProcuracaoResult)
        assert result.total == 2
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/censec/procuracoes/buscar"

    async def test_consultar_procuracao(self, censec_procuracao_response):
        """Consult procuracao."""
        mock_client = AsyncMock()
        mock_client.get.return_value = censec_procuracao_response

        censec = AsyncCENSECResource(mock_client)
        result = await censec.consultar_procuracao("cart_123", "PROC123")

        assert isinstance(result, ProcuracaoResult)
        assert result.outorgante["nome"] == "João Silva"
        assert result.tipo == TipoProcuracao.AD_NEGOTIA
        mock_client.get.assert_called_once()

    async def test_verificar_procuracao_vigente(self):
        """Check if procuracao is valid."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"vigente": True, "dias_restantes": 180}

        censec = AsyncCENSECResource(mock_client)
        result = await censec.verificar_procuracao_vigente("cart_123", "PROC123")

        assert result["vigente"] is True
        mock_client.get.assert_called_once()

    async def test_registrar_procuracao(self):
        """Register procuracao."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "id": "proc_123",
            "protocolo": "PROT456",
            "status": "registrado",
        }

        censec = AsyncCENSECResource(mock_client)
        result = await censec.registrar_procuracao(
            cartorio_id="cart_123",
            tipo="ad_negotia",
            outorgante={"nome": "João", "cpf": "12345678909"},
            outorgado={"nome": "Maria", "cpf": "98765432100"},
            poderes=["administrar", "vender"],
            data_lavratura="2026-01-20",
            livro="B-2",
            folha="15",
        )

        assert isinstance(result, RegistroAtoResult)
        assert result.tipo == TipoAtoNotarial.PROCURACAO

    async def test_registrar_substabelecimento(self):
        """Register substabelecimento."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "id": "subst_123",
            "protocolo": "PROT789",
            "status": "registrado",
        }

        censec = AsyncCENSECResource(mock_client)
        result = await censec.registrar_substabelecimento(
            cartorio_id="cart_123",
            codigo_procuracao="PROC123",
            novo_outorgado={"nome": "Carlos", "cpf": "11122233344"},
            poderes_substabelecidos=["administrar"],
        )

        assert isinstance(result, RegistroAtoResult)
        assert result.tipo == TipoAtoNotarial.SUBSTABELECIMENTO

    async def test_revogar_procuracao(self):
        """Revoke procuracao."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "id": "rev_123",
            "protocolo": "PROT999",
            "status": "registrado",
        }

        censec = AsyncCENSECResource(mock_client)
        result = await censec.revogar_procuracao(
            cartorio_id="cart_123",
            codigo_procuracao="PROC123",
            motivo="Revogação voluntária",
        )

        assert isinstance(result, RegistroAtoResult)
        assert result.tipo == TipoAtoNotarial.REVOGACAO


@pytest.mark.asyncio
class TestAsyncCENSECEscrituras:
    """Tests for async escrituras."""

    async def test_buscar_escrituras(self):
        """Search escrituras."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "total": 1,
            "escrituras": [{"id": "esc_123"}],
            "pagina": 1,
            "por_pagina": 20,
        }

        censec = AsyncCENSECResource(mock_client)
        result = await censec.buscar_escrituras(
            cartorio_id="cart_123",
            cpf_parte="12345678909",
        )

        assert isinstance(result, BuscaEscrituraResult)
        assert result.total == 1
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/censec/escrituras/buscar"

    async def test_consultar_escritura(self):
        """Consult escritura."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "id": "esc_123",
            "tipo": "escritura_publica",
            "partes": [{"nome": "João", "cpf": "12345678909"}],
            "status": "vigente",
        }

        censec = AsyncCENSECResource(mock_client)
        result = await censec.consultar_escritura("cart_123", "ESC123")

        assert isinstance(result, EscrituraResult)
        mock_client.get.assert_called_once()

    async def test_registrar_escritura(self):
        """Register escritura."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "id": "esc_123",
            "protocolo": "PROTEsc",
            "status": "registrado",
        }

        censec = AsyncCENSECResource(mock_client)
        result = await censec.registrar_escritura(
            cartorio_id="cart_123",
            tipo="escritura_publica",
            partes=[{"nome": "João", "cpf": "12345678909"}],
            objeto="Compra e venda de imóvel",
            data_lavratura="2026-01-25",
            livro="C-3",
            folha="20",
            valor=250000.00,
        )

        assert isinstance(result, RegistroAtoResult)


@pytest.mark.asyncio
class TestAsyncCENSECSinalPublico:
    """Tests for async sinal publico."""

    async def test_consultar_sinal_publico(self):
        """Consult sinal publico."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "id": "sinal_123",
            "notario_nome": "Dr. João",
            "notario_cpf": "12345678909",
            "cartorio_nome": "Cartório",
            "cartorio_cns": "12345",
            "uf": "MG",
            "sinal_base64": "iVBORw0...",
            "status": "ativo",
        }

        censec = AsyncCENSECResource(mock_client)
        result = await censec.consultar_sinal_publico("cart_123", "12345")

        assert isinstance(result, SinalPublicoResult)
        assert result.notario_nome == "Dr. João"
        mock_client.get.assert_called_once()

    async def test_registrar_sinal_publico(self):
        """Register sinal publico."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {"success": True, "id": "sinal_123"}

        censec = AsyncCENSECResource(mock_client)
        image = io.BytesIO(b"fake_image")
        result = await censec.registrar_sinal_publico(
            cartorio_id="cart_123",
            sinal_imagem=image,
            notario_cpf="12345678909",
        )

        assert result["success"] is True
        mock_client.post.assert_called_once()


@pytest.mark.asyncio
class TestAsyncCENSECUtilities:
    """Tests for async utilities."""

    async def test_health(self):
        """Check CENSEC health."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"status": "healthy"}

        censec = AsyncCENSECResource(mock_client)
        result = await censec.health()

        assert result["status"] == "healthy"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/censec/health"

    async def test_get_estatisticas(self):
        """Get estatisticas."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"total_atos": 100, "mes": "2026-01"}

        censec = AsyncCENSECResource(mock_client)
        result = await censec.get_estatisticas("cart_123", periodo="mes")

        assert result["total_atos"] == 100
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/censec/estatisticas"
