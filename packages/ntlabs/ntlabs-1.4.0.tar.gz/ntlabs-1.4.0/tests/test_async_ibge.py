"""
NTLabs SDK - Async IBGE Resource Tests
Tests for the AsyncIBGEResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
from unittest.mock import AsyncMock

from ntlabs.resources.async_ibge import AsyncIBGEResource
from ntlabs.resources.ibge import Estado, Municipio, MunicipioDetails, Regiao, Mesorregiao, Microrregiao, Populacao, PIB, Indicadores


@pytest.mark.asyncio
class TestAsyncIBGEResource:
    """Tests for AsyncIBGEResource."""

    async def test_initialization(self):
        """AsyncIBGEResource initializes with client."""
        mock_client = AsyncMock()
        ibge = AsyncIBGEResource(mock_client)
        assert ibge._client == mock_client


@pytest.mark.asyncio
class TestAsyncIBGEEstados:
    """Tests for async estados."""

    async def test_estados(self, ibge_estados_response):
        """List all states."""
        mock_client = AsyncMock()
        mock_client.get.return_value = ibge_estados_response

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.estados()

        assert len(result) == 3
        assert all(isinstance(e, Estado) for e in result)
        assert result[0].sigla == "MG"
        assert result[1].sigla == "SP"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/estados"

    async def test_estado(self):
        """Get state by UF."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "id": 31,
            "sigla": "MG",
            "nome": "Minas Gerais",
            "regiao": {"id": 3, "sigla": "SE", "nome": "Sudeste"},
            "latency_ms": 50,
            "cost_brl": 0.0,
        }

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.estado("mg")

        assert isinstance(result, Estado)
        assert result.sigla == "MG"
        assert result.nome == "Minas Gerais"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/estados/MG"

    async def test_regioes(self):
        """List all regions."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "regioes": [
                {"id": 1, "sigla": "N", "nome": "Norte"},
                {"id": 2, "sigla": "NE", "nome": "Nordeste"},
                {"id": 3, "sigla": "SE", "nome": "Sudeste"},
            ],
            "latency_ms": 50,
            "cost_brl": 0.0,
        }

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.regioes()

        assert len(result) == 3
        assert all(isinstance(r, Regiao) for r in result)
        assert result[0].sigla == "N"
        assert result[2].nome == "Sudeste"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/regioes"


@pytest.mark.asyncio
class TestAsyncIBGEMunicipios:
    """Tests for async municipios."""

    async def test_municipios(self, ibge_municipios_response):
        """List municipalities in a state."""
        mock_client = AsyncMock()
        mock_client.get.return_value = ibge_municipios_response

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.municipios("MG")

        assert len(result) == 3
        assert all(isinstance(m, Municipio) for m in result)
        assert result[0].nome == "Belo Horizonte"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/municipios/MG"

    async def test_municipio(self):
        """Get municipality details."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "id": 3106200,
            "nome": "Belo Horizonte",
            "microrregiao": {"id": 31010, "nome": "Belo Horizonte"},
            "mesorregiao": {"id": 3101, "nome": "Metropolitana de BH"},
            "uf": {"id": 31, "sigla": "MG"},
            "regiao": {"id": 3, "sigla": "SE"},
            "regiao_imediata": {"id": 310001},
            "regiao_intermediaria": {"id": 3101},
            "latency_ms": 100,
            "cost_brl": 0.0,
        }

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.municipio(3106200)

        assert isinstance(result, MunicipioDetails)
        assert result.nome == "Belo Horizonte"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/municipio/3106200"


@pytest.mark.asyncio
class TestAsyncIBGERegioes:
    """Tests for async meso/micro regions."""

    async def test_mesorregioes(self):
        """List mesoregions."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "mesorregioes": [
                {"id": 3101, "nome": "Metropolitana de BH"},
                {"id": 3102, "nome": "Vale do Rio Doce"},
            ]
        }

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.mesorregioes("MG")

        assert len(result) == 2
        assert all(isinstance(m, Mesorregiao) for m in result)
        assert result[0].nome == "Metropolitana de BH"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/mesorregioes/MG"

    async def test_microrregioes(self):
        """List microregions."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "microrregioes": [
                {"id": 31010, "nome": "Belo Horizonte", "mesorregiao": {"id": 3101}},
                {"id": 31020, "nome": "Betim", "mesorregiao": {"id": 3101}},
            ]
        }

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.microrregioes("MG")

        assert len(result) == 2
        assert all(isinstance(m, Microrregiao) for m in result)
        assert result[0].nome == "Belo Horizonte"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/microrregioes/MG"


@pytest.mark.asyncio
class TestAsyncIBGEIndicadores:
    """Tests for async indicators."""

    async def test_populacao(self):
        """Get population."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "localidade_id": 3106200,
            "localidade_nome": "Belo Horizonte",
            "ano": 2024,
            "populacao": 2500000,
            "fonte": "IBGE",
            "latency_ms": 100,
            "cost_brl": 0.0,
        }

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.populacao(3106200)

        assert isinstance(result, Populacao)
        assert result.localidade_id == 3106200
        assert result.populacao == 2500000
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/populacao/3106200"

    async def test_populacao_with_ano(self):
        """Get population for specific year."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"localidade_id": 3106200, "ano": 2020, "populacao": 2400000}

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.populacao(3106200, ano=2020)

        assert result.ano == 2020
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["ano"] == 2020

    async def test_pib(self):
        """Get GDP."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "localidade_id": 3106200,
            "localidade_nome": "Belo Horizonte",
            "ano": 2021,
            "pib_per_capita": 45000.00,
            "unidade": "R$",
            "fonte": "IBGE",
            "latency_ms": 100,
            "cost_brl": 0.0,
        }

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.pib(3106200)

        assert isinstance(result, PIB)
        assert result.pib_per_capita == 45000.00
        assert result.unidade == "R$"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/pib/3106200"

    async def test_pib_with_ano(self):
        """Get GDP for specific year."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"localidade_id": 3106200, "ano": 2020, "pib_per_capita": 42000.00}

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.pib(3106200, ano=2020)

        assert result.ano == 2020
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["ano"] == 2020

    async def test_indicadores(self):
        """Get social indicators."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "localidade_id": 3106200,
            "indicadores": {
                "idh": 0.810,
                "gini": 0.55,
                "renda_per_capita": 2500.00,
            },
            "fonte": "IBGE",
            "latency_ms": 100,
            "cost_brl": 0.0,
        }

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.indicadores(3106200)

        assert isinstance(result, Indicadores)
        assert result.indicadores["idh"] == 0.810
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/indicadores/3106200"


@pytest.mark.asyncio
class TestAsyncIBGEHealth:
    """Tests for async IBGE health."""

    async def test_health(self):
        """Check IBGE API health."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"status": "healthy", "apis": {"ibge": "up"}}

        ibge = AsyncIBGEResource(mock_client)
        result = await ibge.health()

        assert result["status"] == "healthy"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/ibge/health"
