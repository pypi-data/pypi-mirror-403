"""
Tests for CENSEC Resource.
"""

from unittest.mock import Mock

import pytest

from ntlabs.resources.registros.censec import (
    CENSECResource,
    EscrituraResult,
    ProcuracaoResult,
    StatusAto,
    TestamentoResult,
    TipoAtoNotarial,
    TipoProcuracao,
    TipoTestamento,
)


class TestEnums:
    """Test enum values."""

    def test_tipo_testamento_values(self):
        assert TipoTestamento.PUBLICO.value == "publico"
        assert TipoTestamento.CERRADO.value == "cerrado"
        assert TipoTestamento.PARTICULAR.value == "particular"

    def test_tipo_ato_notarial_values(self):
        assert TipoAtoNotarial.ESCRITURA_PUBLICA.value == "escritura_publica"
        assert TipoAtoNotarial.PROCURACAO.value == "procuracao"
        assert TipoAtoNotarial.TESTAMENTO.value == "testamento"
        assert TipoAtoNotarial.DIVORCIO.value == "divorcio"
        assert TipoAtoNotarial.INVENTARIO.value == "inventario"

    def test_status_ato_values(self):
        assert StatusAto.VIGENTE.value == "vigente"
        assert StatusAto.REVOGADO.value == "revogado"
        assert StatusAto.CANCELADO.value == "cancelado"

    def test_tipo_procuracao_values(self):
        assert TipoProcuracao.AD_JUDICIA.value == "ad_judicia"
        assert TipoProcuracao.AD_NEGOTIA.value == "ad_negotia"
        assert TipoProcuracao.PLENOS_PODERES.value == "plenos_poderes"


class TestTestamentoResult:
    """Test TestamentoResult dataclass."""

    def test_create_testamento(self):
        testamento = TestamentoResult(
            id="test-123",
            tipo=TipoTestamento.PUBLICO,
            testador_nome="João da Silva",
            testador_cpf="123.456.789-00",
            data_lavratura="2025-01-20",
            livro="T-001",
            folha="001",
            cartorio_nome="1º Tabelionato",
            cartorio_cns="123456",
            municipio="Belo Horizonte",
            uf="MG",
            status=StatusAto.VIGENTE,
            tem_codicilo=False,
            latency_ms=150,
            cost_brl=0.50,
        )

        assert testamento.tipo == TipoTestamento.PUBLICO
        assert testamento.status == StatusAto.VIGENTE
        assert testamento.tem_codicilo is False

    def test_testamento_to_dict(self):
        testamento = TestamentoResult(
            id="test-123",
            tipo=TipoTestamento.CERRADO,
            testador_nome="Maria",
            testador_cpf=None,
            data_lavratura="2025-01-20",
            livro="T-001",
            folha="001",
            cartorio_nome="Cartório",
            cartorio_cns="123",
            municipio="SP",
            uf="SP",
            status=StatusAto.VIGENTE,
            tem_codicilo=True,
        )

        data = testamento.to_dict()
        assert data["id"] == "test-123"
        assert data["tem_codicilo"] is True


class TestProcuracaoResult:
    """Test ProcuracaoResult dataclass."""

    def test_create_procuracao(self):
        proc = ProcuracaoResult(
            id="proc-123",
            tipo=TipoProcuracao.AD_NEGOTIA,
            outorgante={"nome": "João", "cpf": "123.456.789-00"},
            outorgado={"nome": "Maria", "cpf": "987.654.321-00"},
            poderes=["vender", "comprar", "administrar"],
            data_lavratura="2025-01-20",
            data_validade="2026-01-20",
            livro="P-001",
            folha="001",
            cartorio_nome="1º Tabelionato",
            cartorio_cns="123456",
            municipio="BH",
            uf="MG",
            status=StatusAto.VIGENTE,
            substabelecimentos=[],
        )

        assert proc.tipo == TipoProcuracao.AD_NEGOTIA
        assert len(proc.poderes) == 3


class TestEscrituraResult:
    """Test EscrituraResult dataclass."""

    def test_create_escritura(self):
        escritura = EscrituraResult(
            id="esc-123",
            tipo=TipoAtoNotarial.DIVORCIO,
            partes=[{"nome": "João"}, {"nome": "Maria"}],
            objeto="Divórcio consensual",
            valor=None,
            data_lavratura="2025-01-20",
            livro="E-001",
            folha="001",
            cartorio_nome="Cartório",
            cartorio_cns="123456",
            municipio="BH",
            uf="MG",
            status=StatusAto.VIGENTE,
        )

        assert escritura.tipo == TipoAtoNotarial.DIVORCIO
        assert len(escritura.partes) == 2


class TestCENSECResource:
    """Test CENSECResource methods."""

    @pytest.fixture
    def mock_client(self):
        return Mock()

    @pytest.fixture
    def censec(self, mock_client):
        return CENSECResource(mock_client)

    def test_initialization(self, censec, mock_client):
        assert censec._client == mock_client

    # =========================================================================
    # RCTO - Testamentos
    # =========================================================================

    def test_buscar_testamentos(self, censec, mock_client):
        mock_client.get.return_value = {
            "total": 2,
            "testamentos": [
                {"id": "t1", "testador_nome": "João"},
                {"id": "t2", "testador_nome": "Maria"},
            ],
            "pagina": 1,
            "por_pagina": 20,
            "latency_ms": 200,
        }

        result = censec.buscar_testamentos(
            cartorio_id="uuid-123",
            cpf_testador="123.456.789-00",
        )

        assert result.total == 2
        assert len(result.testamentos) == 2

        # Verify CPF was cleaned
        call_params = mock_client.get.call_args[1]["params"]
        assert call_params["cpf_testador"] == "12345678900"

    def test_consultar_testamento(self, censec, mock_client):
        mock_client.get.return_value = {
            "id": "test-123",
            "tipo": "publico",
            "testador_nome": "João da Silva",
            "testador_cpf": "12345678900",
            "data_lavratura": "2025-01-20",
            "livro": "T-001",
            "folha": "001",
            "cartorio_nome": "1º Tabelionato",
            "cartorio_cns": "123456",
            "municipio": "BH",
            "uf": "MG",
            "status": "vigente",
            "tem_codicilo": False,
            "latency_ms": 150,
        }

        result = censec.consultar_testamento(
            cartorio_id="uuid-123",
            codigo="ABC123",
        )

        assert result.tipo == TipoTestamento.PUBLICO
        assert result.status == StatusAto.VIGENTE

    def test_existe_testamento(self, censec, mock_client):
        mock_client.get.return_value = {"existe": True, "quantidade": 2}

        result = censec.existe_testamento(
            cartorio_id="uuid-123",
            cpf="123.456.789-00",
        )

        assert result["existe"] is True
        assert result["quantidade"] == 2

    def test_registrar_testamento(self, censec, mock_client):
        mock_client.post.return_value = {
            "id": "test-new",
            "protocolo": "2025/RCTO/001234",
            "status": "registrado",
            "data_registro": "2025-01-25",
            "mensagem": "Testamento registrado",
            "latency_ms": 300,
        }

        result = censec.registrar_testamento(
            cartorio_id="uuid-123",
            tipo="publico",
            testador={"nome": "João", "cpf": "12345678900"},
            data_lavratura="2025-01-20",
            livro="T-001",
            folha="001",
            dados_testamento={"disposicoes": "..."},
        )

        assert result.protocolo == "2025/RCTO/001234"
        assert result.tipo == TipoAtoNotarial.TESTAMENTO

    def test_revogar_testamento(self, censec, mock_client):
        mock_client.post.return_value = {"success": True}

        result = censec.revogar_testamento(
            cartorio_id="uuid-123",
            codigo_testamento="ABC123",
            motivo="Novo testamento lavrado",
        )

        assert result["success"] is True

    # =========================================================================
    # Procurações
    # =========================================================================

    def test_buscar_procuracoes(self, censec, mock_client):
        mock_client.get.return_value = {
            "total": 1,
            "procuracoes": [{"id": "p1", "outorgante": {"nome": "João"}}],
            "pagina": 1,
            "por_pagina": 20,
        }

        result = censec.buscar_procuracoes(
            cartorio_id="uuid-123",
            cpf_outorgante="123.456.789-00",
            vigentes_apenas=True,
        )

        assert result.total == 1
        call_params = mock_client.get.call_args[1]["params"]
        assert call_params["vigentes_apenas"] == "true"

    def test_consultar_procuracao(self, censec, mock_client):
        mock_client.get.return_value = {
            "id": "proc-123",
            "tipo": "ad_negotia",
            "outorgante": {"nome": "João"},
            "outorgado": {"nome": "Maria"},
            "poderes": ["vender", "comprar"],
            "data_lavratura": "2025-01-20",
            "livro": "P-001",
            "folha": "001",
            "cartorio_nome": "Cartório",
            "cartorio_cns": "123456",
            "municipio": "BH",
            "uf": "MG",
            "status": "vigente",
            "substabelecimentos": [],
        }

        result = censec.consultar_procuracao(
            cartorio_id="uuid-123",
            codigo="XYZ789",
        )

        assert result.tipo == TipoProcuracao.AD_NEGOTIA
        assert len(result.poderes) == 2

    def test_verificar_procuracao_vigente(self, censec, mock_client):
        mock_client.get.return_value = {
            "vigente": True,
            "status": "vigente",
            "data_verificacao": "2025-01-25",
        }

        result = censec.verificar_procuracao_vigente(
            cartorio_id="uuid-123",
            codigo="XYZ789",
        )

        assert result["vigente"] is True

    def test_registrar_procuracao(self, censec, mock_client):
        mock_client.post.return_value = {
            "id": "proc-new",
            "protocolo": "2025/PROC/001234",
            "status": "registrado",
            "data_registro": "2025-01-25",
            "mensagem": "Procuração registrada",
        }

        result = censec.registrar_procuracao(
            cartorio_id="uuid-123",
            tipo="ad_negotia",
            outorgante={"nome": "João", "cpf": "123"},
            outorgado={"nome": "Maria", "cpf": "456"},
            poderes=["vender", "comprar"],
            data_lavratura="2025-01-20",
            livro="P-001",
            folha="001",
        )

        assert result.protocolo == "2025/PROC/001234"
        assert result.tipo == TipoAtoNotarial.PROCURACAO

    def test_registrar_substabelecimento(self, censec, mock_client):
        mock_client.post.return_value = {
            "id": "sub-123",
            "protocolo": "2025/SUB/001234",
            "status": "registrado",
            "data_registro": "2025-01-25",
            "mensagem": "Substabelecimento registrado",
        }

        result = censec.registrar_substabelecimento(
            cartorio_id="uuid-123",
            codigo_procuracao="XYZ789",
            novo_outorgado={"nome": "Pedro", "cpf": "789"},
            poderes_substabelecidos=["vender"],
            com_reserva=True,
        )

        assert result.tipo == TipoAtoNotarial.SUBSTABELECIMENTO

    def test_revogar_procuracao(self, censec, mock_client):
        mock_client.post.return_value = {
            "id": "rev-123",
            "protocolo": "2025/REV/001234",
            "status": "registrado",
            "data_registro": "2025-01-25",
            "mensagem": "Procuração revogada",
        }

        result = censec.revogar_procuracao(
            cartorio_id="uuid-123",
            codigo_procuracao="XYZ789",
            motivo="Revogação a pedido do outorgante",
        )

        assert result.tipo == TipoAtoNotarial.REVOGACAO

    # =========================================================================
    # Escrituras
    # =========================================================================

    def test_buscar_escrituras(self, censec, mock_client):
        mock_client.get.return_value = {
            "total": 1,
            "escrituras": [{"id": "e1", "tipo": "divorcio"}],
            "pagina": 1,
            "por_pagina": 20,
        }

        result = censec.buscar_escrituras(
            cartorio_id="uuid-123",
            tipo="divorcio",
            uf="mg",
        )

        assert result.total == 1
        call_params = mock_client.get.call_args[1]["params"]
        assert call_params["uf"] == "MG"

    def test_consultar_escritura(self, censec, mock_client):
        mock_client.get.return_value = {
            "id": "esc-123",
            "tipo": "divorcio",
            "partes": [{"nome": "João"}, {"nome": "Maria"}],
            "objeto": "Divórcio consensual",
            "data_lavratura": "2025-01-20",
            "livro": "E-001",
            "folha": "001",
            "cartorio_nome": "Cartório",
            "cartorio_cns": "123456",
            "municipio": "BH",
            "uf": "MG",
            "status": "vigente",
        }

        result = censec.consultar_escritura(
            cartorio_id="uuid-123",
            codigo="ESC123",
        )

        assert result.tipo == TipoAtoNotarial.DIVORCIO
        assert len(result.partes) == 2

    def test_registrar_escritura(self, censec, mock_client):
        mock_client.post.return_value = {
            "id": "esc-new",
            "protocolo": "2025/ESC/001234",
            "status": "registrado",
            "data_registro": "2025-01-25",
            "mensagem": "Escritura registrada",
        }

        result = censec.registrar_escritura(
            cartorio_id="uuid-123",
            tipo="inventario",
            partes=[{"nome": "Herdeiro 1"}, {"nome": "Herdeiro 2"}],
            objeto="Inventário extrajudicial",
            data_lavratura="2025-01-20",
            livro="E-001",
            folha="001",
            valor=500000.00,
        )

        assert result.protocolo == "2025/ESC/001234"
        assert result.tipo == TipoAtoNotarial.INVENTARIO

    # =========================================================================
    # CNSIP - Sinal Público
    # =========================================================================

    def test_consultar_sinal_publico(self, censec, mock_client):
        mock_client.get.return_value = {
            "id": "sinal-123",
            "notario_nome": "Dr. João da Silva",
            "notario_cpf": "12345678900",
            "cartorio_nome": "1º Tabelionato",
            "uf": "MG",
            "sinal_base64": "iVBORw0KGgo...",
            "data_cadastro": "2024-01-01",
            "status": "ativo",
        }

        result = censec.consultar_sinal_publico(
            cartorio_id="uuid-123",
            cns_cartorio="654321",
        )

        assert result.notario_nome == "Dr. João da Silva"
        assert result.status == "ativo"

    def test_registrar_sinal_publico(self, censec, mock_client):
        mock_client.post.return_value = {"success": True, "id": "sinal-new"}

        result = censec.registrar_sinal_publico(
            cartorio_id="uuid-123",
            sinal_imagem=Mock(),
            notario_cpf="123.456.789-00",
        )

        assert result["success"] is True

    # =========================================================================
    # Utilidades
    # =========================================================================

    def test_health(self, censec, mock_client):
        mock_client.get.return_value = {
            "status": "healthy",
            "censec_connection": "ok",
        }

        result = censec.health()
        assert result["status"] == "healthy"

    def test_get_estatisticas(self, censec, mock_client):
        mock_client.get.return_value = {
            "consultas": 150,
            "registros": 25,
            "periodo": "mes",
        }

        result = censec.get_estatisticas(
            cartorio_id="uuid-123",
            periodo="mes",
        )

        assert result["consultas"] == 150

    def test_empty_response_handling(self, censec, mock_client):
        mock_client.get.return_value = {}

        result = censec.consultar_testamento(
            cartorio_id="uuid-123",
            codigo="ABC123",
        )

        assert result.id == ""
        assert result.testador_nome == ""
