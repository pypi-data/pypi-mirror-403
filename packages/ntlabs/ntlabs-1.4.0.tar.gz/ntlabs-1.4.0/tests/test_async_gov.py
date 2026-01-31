"""
NTLabs SDK - Async Gov Resource Tests
Tests for the AsyncGovResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
from unittest.mock import AsyncMock

from ntlabs.resources.async_gov import AsyncGovResource
from ntlabs.resources.gov import CNPJResult, CPFValidation, CEPResult, Municipio, MunicipioDetails


@pytest.mark.asyncio
class TestAsyncGovResource:
    """Tests for AsyncGovResource."""

    async def test_initialization(self):
        """AsyncGovResource initializes with client."""
        mock_client = AsyncMock()
        gov = AsyncGovResource(mock_client)
        assert gov._client == mock_client


@pytest.mark.asyncio
class TestAsyncGovCNPJ:
    """Tests for async CNPJ lookup."""

    async def test_cnpj_lookup(self, cnpj_response):
        """Lookup CNPJ."""
        mock_client = AsyncMock()
        mock_client.get.return_value = cnpj_response

        gov = AsyncGovResource(mock_client)
        result = await gov.cnpj("12.345.678/0001-90")

        assert isinstance(result, CNPJResult)
        assert result.razao_social == "EMPRESA TESTE LTDA"
        assert result.situacao == "ATIVA"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/gov/cnpj/12345678000190"

    async def test_cnpj_lookup_clean_number(self, cnpj_response):
        """CNPJ lookup cleans formatting."""
        mock_client = AsyncMock()
        mock_client.get.return_value = cnpj_response

        gov = AsyncGovResource(mock_client)
        result = await gov.cnpj("12345678000190")

        assert isinstance(result, CNPJResult)

    async def test_cnpj_endereco(self, cnpj_response):
        """CNPJ lookup includes address."""
        mock_client = AsyncMock()
        mock_client.get.return_value = cnpj_response

        gov = AsyncGovResource(mock_client)
        result = await gov.cnpj("12345678000190")

        assert result.endereco["logradouro"] == "Rua Teste"
        assert result.endereco["municipio"] == "Belo Horizonte"

    async def test_cnpj_atividades(self, cnpj_response):
        """CNPJ lookup includes activities."""
        mock_client = AsyncMock()
        mock_client.get.return_value = cnpj_response

        gov = AsyncGovResource(mock_client)
        result = await gov.cnpj("12345678000190")

        assert len(result.atividade_principal) == 1
        assert result.atividade_principal[0]["codigo"] == "6201-5/01"


@pytest.mark.asyncio
class TestAsyncGovCPF:
    """Tests for async CPF validation."""

    async def test_validate_cpf_valid(self, cpf_response):
        """Validate valid CPF."""
        mock_client = AsyncMock()
        mock_client.get.return_value = cpf_response

        gov = AsyncGovResource(mock_client)
        result = await gov.validate_cpf("123.456.789-09")

        assert isinstance(result, CPFValidation)
        assert result.valid is True
        assert result.reason is None
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/gov/cpf/12345678909/validate"

    async def test_validate_cpf_invalid(self):
        """Validate invalid CPF."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "cpf": "11111111111",
            "valid": False,
            "reason": "Invalid check digit",
            "latency_ms": 5,
            "cost_brl": 0.0,
        }

        gov = AsyncGovResource(mock_client)
        result = await gov.validate_cpf("111.111.111-11")

        assert result.valid is False
        assert result.reason == "Invalid check digit"

    async def test_validate_cpf_clean_number(self, cpf_response):
        """CPF validation cleans formatting."""
        mock_client = AsyncMock()
        mock_client.get.return_value = cpf_response

        gov = AsyncGovResource(mock_client)
        result = await gov.validate_cpf("12345678909")

        assert isinstance(result, CPFValidation)


@pytest.mark.asyncio
class TestAsyncGovCEP:
    """Tests for async CEP lookup."""

    async def test_cep_lookup(self, cep_response):
        """Lookup CEP."""
        mock_client = AsyncMock()
        mock_client.get.return_value = cep_response

        gov = AsyncGovResource(mock_client)
        result = await gov.cep("01310-100")

        assert isinstance(result, CEPResult)
        assert result.logradouro == "Avenida Paulista"
        assert result.municipio == "São Paulo"
        assert result.uf == "SP"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/gov/cep/01310100"

    async def test_cep_lookup_clean_number(self, cep_response):
        """CEP lookup cleans formatting."""
        mock_client = AsyncMock()
        mock_client.get.return_value = cep_response

        gov = AsyncGovResource(mock_client)
        result = await gov.cep("01310100")

        assert isinstance(result, CEPResult)

    async def test_cep_ibge_code(self, cep_response):
        """CEP lookup includes IBGE code."""
        mock_client = AsyncMock()
        mock_client.get.return_value = cep_response

        gov = AsyncGovResource(mock_client)
        result = await gov.cep("01310100")

        assert result.ibge == "3550308"


@pytest.mark.asyncio
class TestAsyncGovMunicipios:
    """Tests for async municipalities."""

    async def test_municipios_list(self):
        """List municipalities."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "municipios": [
                {"codigo_ibge": 3106200, "nome": "Belo Horizonte"},
                {"codigo_ibge": 3106705, "nome": "Betim"},
            ]
        }

        gov = AsyncGovResource(mock_client)
        result = await gov.municipios("MG")

        assert len(result) == 2
        assert all(isinstance(m, Municipio) for m in result)
        assert result[0].nome == "Belo Horizonte"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/gov/ibge/municipios/MG"

    async def test_municipios_uppercase(self):
        """Municipios converts UF to uppercase."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"municipios": []}

        gov = AsyncGovResource(mock_client)
        await gov.municipios("mg")

        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/gov/ibge/municipios/MG"

    async def test_municipio_details(self):
        """Get municipality details."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "codigo_ibge": 3106200,
            "nome": "Belo Horizonte",
            "microrregiao": "Belo Horizonte",
            "mesorregiao": "Metropolitana de BH",
            "uf": {"id": 31, "sigla": "MG", "nome": "Minas Gerais"},
            "regiao": "Sudeste",
            "latency_ms": 100,
            "cost_brl": 0.0,
        }

        gov = AsyncGovResource(mock_client)
        result = await gov.municipio("3106200")

        assert isinstance(result, MunicipioDetails)
        assert result.nome == "Belo Horizonte"
        assert result.uf["sigla"] == "MG"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/gov/ibge/municipio/3106200"


@pytest.mark.asyncio
class TestAsyncGovContratos:
    """Tests for async government contracts."""

    async def test_contratos_search(self):
        """Search contracts."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "contratos": [
                {"id": "1", "valor": 100000, "orgao": "26000"},
            ],
            "total": 1,
        }

        gov = AsyncGovResource(mock_client)
        result = await gov.contratos(orgao="26000", ano=2024)

        assert "contratos" in result
        assert len(result["contratos"]) == 1
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/gov/transparencia/contratos"
        assert call_args[1]["params"]["orgao"] == "26000"
        assert call_args[1]["params"]["ano"] == 2024

    async def test_contratos_with_cnpj(self):
        """Search contracts by CNPJ."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"contratos": []}

        gov = AsyncGovResource(mock_client)
        await gov.contratos(cnpj="12.345.678/0001-90")

        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["cnpj"] == "12345678000190"

    async def test_contratos_pagination(self):
        """Contracts pagination."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"contratos": []}

        gov = AsyncGovResource(mock_client)
        await gov.contratos(pagina=2, quantidade=50)

        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["pagina"] == 2
        assert call_args[1]["params"]["quantidade"] == 50


@pytest.mark.asyncio
class TestAsyncGovHealth:
    """Tests for async gov health."""

    async def test_health(self):
        """Check government APIs health."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "status": "healthy",
            "apis": {
                "receita_ws": "up",
                "via_cep": "up",
                "ibge": "up",
            },
        }

        gov = AsyncGovResource(mock_client)
        result = await gov.health()

        assert result["status"] == "healthy"
        assert result["apis"]["via_cep"] == "up"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/v1/gov/health"
