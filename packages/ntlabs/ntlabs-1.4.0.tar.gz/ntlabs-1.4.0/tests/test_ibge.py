"""
NTLabs SDK - IBGE Resource Tests
Tests for the IBGEResource class (Brazilian geographic and demographic data).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

from ntlabs.resources.ibge import (
    PIB,
    Estado,
    IBGEResource,
    Indicadores,
    Mesorregiao,
    Microrregiao,
    Municipio,
    MunicipioDetails,
    Populacao,
    Regiao,
)


class TestEstado:
    """Tests for Estado dataclass."""

    def test_create_estado(self):
        """Create estado."""
        estado = Estado(
            id=31,
            sigla="MG",
            nome="Minas Gerais",
            regiao={"id": 3, "sigla": "SE", "nome": "Sudeste"},
            latency_ms=50,
            cost_brl=0.0,
        )
        assert estado.id == 31
        assert estado.sigla == "MG"
        assert estado.regiao["nome"] == "Sudeste"


class TestRegiao:
    """Tests for Regiao dataclass."""

    def test_create_regiao(self):
        """Create regiao."""
        regiao = Regiao(
            id=3,
            sigla="SE",
            nome="Sudeste",
            latency_ms=50,
            cost_brl=0.0,
        )
        assert regiao.nome == "Sudeste"


class TestMunicipio:
    """Tests for Municipio dataclass."""

    def test_create_municipio(self):
        """Create municipio."""
        municipio = Municipio(id=3106200, nome="Belo Horizonte")
        assert municipio.id == 3106200
        assert municipio.nome == "Belo Horizonte"


class TestPopulacao:
    """Tests for Populacao dataclass."""

    def test_create_populacao(self):
        """Create populacao."""
        pop = Populacao(
            localidade_id=3106200,
            localidade_nome="Belo Horizonte",
            ano=2024,
            populacao=2530701,
            fonte="IBGE",
            latency_ms=100,
            cost_brl=0.0,
        )
        assert pop.populacao == 2530701
        assert pop.ano == 2024


class TestPIB:
    """Tests for PIB dataclass."""

    def test_create_pib(self):
        """Create PIB."""
        pib = PIB(
            localidade_id=3106200,
            localidade_nome="Belo Horizonte",
            ano=2021,
            pib_per_capita=42500.50,
            unidade="R$",
            fonte="IBGE",
            latency_ms=150,
            cost_brl=0.0,
        )
        assert pib.pib_per_capita == 42500.50


class TestIBGEResource:
    """Tests for IBGEResource."""

    def test_initialization(self, mock_client):
        """IBGEResource initializes with client."""
        ibge = IBGEResource(mock_client)
        assert ibge._client == mock_client

    def test_estados_list(self, mock_client, mock_response, ibge_estados_response):
        """List all Brazilian states."""
        mock_client._mock_http.request.return_value = mock_response(
            ibge_estados_response
        )

        result = mock_client.ibge.estados()

        assert len(result) == 3
        assert all(isinstance(e, Estado) for e in result)
        assert result[0].sigla == "MG"
        assert result[0].nome == "Minas Gerais"

    def test_estado_detail(self, mock_client, mock_response):
        """Get state details by UF."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "id": 31,
                "sigla": "MG",
                "nome": "Minas Gerais",
                "regiao": {"id": 3, "sigla": "SE", "nome": "Sudeste"},
                "latency_ms": 50,
                "cost_brl": 0.0,
            }
        )

        result = mock_client.ibge.estado("MG")

        assert isinstance(result, Estado)
        assert result.nome == "Minas Gerais"
        assert result.regiao["sigla"] == "SE"

    def test_estado_uppercase(self, mock_client, mock_response):
        """Estado converts UF to uppercase."""
        mock_client._mock_http.request.return_value = mock_response(
            {"id": 31, "sigla": "MG", "nome": "Minas Gerais", "regiao": {}}
        )

        mock_client.ibge.estado("mg")
        call_args = mock_client._mock_http.request.call_args
        assert "MG" in str(call_args)

    def test_regioes_list(self, mock_client, mock_response):
        """List all regions."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "regioes": [
                    {"id": 1, "sigla": "N", "nome": "Norte"},
                    {"id": 2, "sigla": "NE", "nome": "Nordeste"},
                    {"id": 3, "sigla": "SE", "nome": "Sudeste"},
                    {"id": 4, "sigla": "S", "nome": "Sul"},
                    {"id": 5, "sigla": "CO", "nome": "Centro-Oeste"},
                ],
                "latency_ms": 30,
                "cost_brl": 0.0,
            }
        )

        result = mock_client.ibge.regioes()

        assert len(result) == 5
        assert all(isinstance(r, Regiao) for r in result)
        assert result[2].nome == "Sudeste"

    def test_municipios_list(
        self, mock_client, mock_response, ibge_municipios_response
    ):
        """List municipalities by state."""
        mock_client._mock_http.request.return_value = mock_response(
            ibge_municipios_response
        )

        result = mock_client.ibge.municipios("MG")

        assert len(result) == 3
        assert all(isinstance(m, Municipio) for m in result)
        assert result[0].nome == "Belo Horizonte"

    def test_municipio_detail(self, mock_client, mock_response):
        """Get municipality details."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "id": 3106200,
                "nome": "Belo Horizonte",
                "microrregiao": {"id": 31030, "nome": "Belo Horizonte"},
                "mesorregiao": {"id": 3107, "nome": "Metropolitana de BH"},
                "uf": {"id": 31, "sigla": "MG", "nome": "Minas Gerais"},
                "regiao": {"id": 3, "sigla": "SE", "nome": "Sudeste"},
                "regiao_imediata": None,
                "regiao_intermediaria": None,
                "latency_ms": 80,
                "cost_brl": 0.0,
            }
        )

        result = mock_client.ibge.municipio(3106200)

        assert isinstance(result, MunicipioDetails)
        assert result.nome == "Belo Horizonte"
        assert result.uf["sigla"] == "MG"

    def test_mesorregioes_list(self, mock_client, mock_response):
        """List mesoregions by state."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "mesorregioes": [
                    {"id": 3101, "nome": "Noroeste de Minas"},
                    {"id": 3107, "nome": "Metropolitana de Belo Horizonte"},
                ]
            }
        )

        result = mock_client.ibge.mesorregioes("MG")

        assert len(result) == 2
        assert all(isinstance(m, Mesorregiao) for m in result)

    def test_microrregioes_list(self, mock_client, mock_response):
        """List microregions by state."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "microrregioes": [
                    {
                        "id": 31001,
                        "nome": "Unaí",
                        "mesorregiao": {"id": 3101, "nome": "Noroeste"},
                    },
                    {
                        "id": 31030,
                        "nome": "Belo Horizonte",
                        "mesorregiao": {"id": 3107, "nome": "Metropolitana"},
                    },
                ]
            }
        )

        result = mock_client.ibge.microrregioes("MG")

        assert len(result) == 2
        assert all(isinstance(m, Microrregiao) for m in result)
        assert result[0].mesorregiao["nome"] == "Noroeste"

    def test_populacao(self, mock_client, mock_response):
        """Get population estimate."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "localidade_id": 3106200,
                "localidade_nome": "Belo Horizonte",
                "ano": 2024,
                "populacao": 2530701,
                "fonte": "IBGE",
                "latency_ms": 100,
                "cost_brl": 0.0,
            }
        )

        result = mock_client.ibge.populacao(3106200)

        assert isinstance(result, Populacao)
        assert result.populacao == 2530701
        assert result.ano == 2024

    def test_populacao_with_year(self, mock_client, mock_response):
        """Get population for specific year."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "localidade_id": 3106200,
                "ano": 2020,
                "populacao": 2500000,
                "fonte": "IBGE",
                "latency_ms": 100,
                "cost_brl": 0.0,
            }
        )

        result = mock_client.ibge.populacao(3106200, ano=2020)
        assert result.ano == 2020

    def test_pib(self, mock_client, mock_response):
        """Get GDP per capita."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "localidade_id": 3106200,
                "localidade_nome": "Belo Horizonte",
                "ano": 2021,
                "pib_per_capita": 42500.50,
                "unidade": "R$",
                "fonte": "IBGE",
                "latency_ms": 150,
                "cost_brl": 0.0,
            }
        )

        result = mock_client.ibge.pib(3106200)

        assert isinstance(result, PIB)
        assert result.pib_per_capita == 42500.50
        assert result.unidade == "R$"

    def test_pib_with_year(self, mock_client, mock_response):
        """Get GDP for specific year."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "localidade_id": 3106200,
                "ano": 2019,
                "pib_per_capita": 38000.00,
                "unidade": "R$",
                "fonte": "IBGE",
                "latency_ms": 150,
                "cost_brl": 0.0,
            }
        )

        result = mock_client.ibge.pib(3106200, ano=2019)
        assert result.ano == 2019

    def test_indicadores(self, mock_client, mock_response):
        """Get social indicators."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "localidade_id": 3106200,
                "indicadores": {
                    "populacao": 2530701,
                    "pib_per_capita": 42500.50,
                    "idh": 0.810,
                    "taxa_analfabetismo": 2.5,
                },
                "fonte": "IBGE",
                "latency_ms": 200,
                "cost_brl": 0.0,
            }
        )

        result = mock_client.ibge.indicadores(3106200)

        assert isinstance(result, Indicadores)
        assert result.indicadores["idh"] == 0.810
        assert "populacao" in result.indicadores

    def test_health(self, mock_client, mock_response):
        """Check IBGE API health."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "status": "healthy",
                "api": "up",
            }
        )

        health = mock_client.ibge.health()

        assert health["status"] == "healthy"

    def test_empty_response_handling(self, mock_client, mock_response):
        """Handle empty responses gracefully."""
        mock_client._mock_http.request.return_value = mock_response({})

        # Estados
        result = mock_client.ibge.estados()
        assert result == []

        # Regioes
        result = mock_client.ibge.regioes()
        assert result == []

        # Municipios
        result = mock_client.ibge.municipios("MG")
        assert result == []

        # Mesorregioes
        result = mock_client.ibge.mesorregioes("MG")
        assert result == []

        # Microrregioes
        result = mock_client.ibge.microrregioes("MG")
        assert result == []

    def test_estado_empty_response(self, mock_client, mock_response):
        """Handle empty estado response."""
        mock_client._mock_http.request.return_value = mock_response({})

        result = mock_client.ibge.estado("MG")
        assert result.sigla == ""
        assert result.nome == ""

    def test_municipio_empty_response(self, mock_client, mock_response):
        """Handle empty municipio response."""
        mock_client._mock_http.request.return_value = mock_response({})

        result = mock_client.ibge.municipio(3106200)
        assert result.id == 0
        assert result.nome == ""

    def test_populacao_empty_response(self, mock_client, mock_response):
        """Handle empty populacao response."""
        mock_client._mock_http.request.return_value = mock_response({})

        result = mock_client.ibge.populacao(3106200)
        assert result.populacao is None
        assert result.ano == 0

    def test_pib_empty_response(self, mock_client, mock_response):
        """Handle empty PIB response."""
        mock_client._mock_http.request.return_value = mock_response({})

        result = mock_client.ibge.pib(3106200)
        assert result.pib_per_capita is None
        assert result.unidade == "R$"

    def test_indicadores_empty_response(self, mock_client, mock_response):
        """Handle empty indicadores response."""
        mock_client._mock_http.request.return_value = mock_response({})

        result = mock_client.ibge.indicadores(3106200)
        assert result.indicadores == {}
