"""
NTLabs SDK - Gov Resource Tests
Tests for the GovResource class (Brazilian government APIs).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

from ntlabs.resources.gov import (
    CEPResult,
    CNPJResult,
    CPFValidation,
    GovResource,
    Municipio,
    MunicipioDetails,
)


class TestCNPJResult:
    """Tests for CNPJResult dataclass."""

    def test_create_result(self, cnpj_response):
        """Create CNPJ result."""
        result = CNPJResult(
            cnpj=cnpj_response["cnpj"],
            razao_social=cnpj_response["razao_social"],
            nome_fantasia=cnpj_response["nome_fantasia"],
            situacao=cnpj_response["situacao"],
            data_situacao=cnpj_response["data_situacao"],
            tipo=cnpj_response["tipo"],
            porte=cnpj_response["porte"],
            natureza_juridica=cnpj_response["natureza_juridica"],
            atividade_principal=cnpj_response["atividade_principal"],
            atividades_secundarias=cnpj_response["atividades_secundarias"],
            endereco=cnpj_response["endereco"],
            telefone=cnpj_response["telefone"],
            email=cnpj_response["email"],
            capital_social=cnpj_response["capital_social"],
            data_abertura=cnpj_response["data_abertura"],
            latency_ms=cnpj_response["latency_ms"],
            cost_brl=cnpj_response["cost_brl"],
        )
        assert result.razao_social == "EMPRESA TESTE LTDA"
        assert result.situacao == "ATIVA"


class TestCPFValidation:
    """Tests for CPFValidation dataclass."""

    def test_create_validation(self, cpf_response):
        """Create CPF validation result."""
        result = CPFValidation(
            cpf=cpf_response["cpf"],
            valid=cpf_response["valid"],
            reason=cpf_response["reason"],
            latency_ms=cpf_response["latency_ms"],
            cost_brl=cpf_response["cost_brl"],
        )
        assert result.cpf == "12345678909"
        assert result.valid is True


class TestCEPResult:
    """Tests for CEPResult dataclass."""

    def test_create_result(self, cep_response):
        """Create CEP result."""
        result = CEPResult(
            cep=cep_response["cep"],
            logradouro=cep_response["logradouro"],
            complemento=cep_response["complemento"],
            bairro=cep_response["bairro"],
            municipio=cep_response["municipio"],
            uf=cep_response["uf"],
            ibge=cep_response["ibge"],
            ddd=cep_response["ddd"],
            latency_ms=cep_response["latency_ms"],
            cost_brl=cep_response["cost_brl"],
        )
        assert result.logradouro == "Avenida Paulista"
        assert result.uf == "SP"


class TestGovResource:
    """Tests for GovResource."""

    def test_initialization(self, mock_client):
        """GovResource initializes with client."""
        gov = GovResource(mock_client)
        assert gov._client == mock_client

    def test_cnpj_lookup(self, mock_client, mock_response, cnpj_response):
        """Lookup CNPJ information."""
        mock_client._mock_http.request.return_value = mock_response(cnpj_response)

        result = mock_client.gov.cnpj("12.345.678/0001-90")

        assert isinstance(result, CNPJResult)
        assert result.razao_social == "EMPRESA TESTE LTDA"
        assert result.situacao == "ATIVA"
        assert result.porte == "PEQUENO"

    def test_cnpj_lookup_clean_number(self, mock_client, mock_response, cnpj_response):
        """CNPJ lookup cleans formatting."""
        mock_client._mock_http.request.return_value = mock_response(cnpj_response)

        result = mock_client.gov.cnpj("12345678000190")
        assert isinstance(result, CNPJResult)

    def test_cnpj_endereco(self, mock_client, mock_response, cnpj_response):
        """CNPJ lookup includes address."""
        mock_client._mock_http.request.return_value = mock_response(cnpj_response)

        result = mock_client.gov.cnpj("12345678000190")

        assert result.endereco["logradouro"] == "Rua Teste"
        assert result.endereco["municipio"] == "Belo Horizonte"
        assert result.endereco["uf"] == "MG"

    def test_cnpj_atividades(self, mock_client, mock_response, cnpj_response):
        """CNPJ lookup includes activities."""
        mock_client._mock_http.request.return_value = mock_response(cnpj_response)

        result = mock_client.gov.cnpj("12345678000190")

        assert len(result.atividade_principal) == 1
        assert result.atividade_principal[0]["codigo"] == "6201-5/01"

    def test_validate_cpf_valid(self, mock_client, mock_response, cpf_response):
        """Validate valid CPF."""
        mock_client._mock_http.request.return_value = mock_response(cpf_response)

        result = mock_client.gov.validate_cpf("123.456.789-09")

        assert isinstance(result, CPFValidation)
        assert result.valid is True
        assert result.reason is None

    def test_validate_cpf_invalid(self, mock_client, mock_response):
        """Validate invalid CPF."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "cpf": "11111111111",
                "valid": False,
                "reason": "Invalid check digit",
                "latency_ms": 5,
                "cost_brl": 0.0,
            }
        )

        result = mock_client.gov.validate_cpf("111.111.111-11")

        assert result.valid is False
        assert result.reason == "Invalid check digit"

    def test_validate_cpf_clean_number(self, mock_client, mock_response, cpf_response):
        """CPF validation cleans formatting."""
        mock_client._mock_http.request.return_value = mock_response(cpf_response)

        result = mock_client.gov.validate_cpf("12345678909")
        assert isinstance(result, CPFValidation)

    def test_cep_lookup(self, mock_client, mock_response, cep_response):
        """Lookup CEP information."""
        mock_client._mock_http.request.return_value = mock_response(cep_response)

        result = mock_client.gov.cep("01310-100")

        assert isinstance(result, CEPResult)
        assert result.logradouro == "Avenida Paulista"
        assert result.municipio == "São Paulo"
        assert result.uf == "SP"

    def test_cep_lookup_clean_number(self, mock_client, mock_response, cep_response):
        """CEP lookup cleans formatting."""
        mock_client._mock_http.request.return_value = mock_response(cep_response)

        result = mock_client.gov.cep("01310100")
        assert isinstance(result, CEPResult)

    def test_cep_ibge_code(self, mock_client, mock_response, cep_response):
        """CEP lookup includes IBGE code."""
        mock_client._mock_http.request.return_value = mock_response(cep_response)

        result = mock_client.gov.cep("01310100")
        assert result.ibge == "3550308"

    def test_municipios_list(self, mock_client, mock_response):
        """List municipalities by state."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "municipios": [
                    {"codigo_ibge": 3106200, "nome": "Belo Horizonte"},
                    {"codigo_ibge": 3106705, "nome": "Betim"},
                ]
            }
        )

        result = mock_client.gov.municipios("MG")

        assert len(result) == 2
        assert all(isinstance(m, Municipio) for m in result)
        assert result[0].nome == "Belo Horizonte"

    def test_municipios_uppercase(self, mock_client, mock_response):
        """Municipios converts UF to uppercase."""
        mock_client._mock_http.request.return_value = mock_response({"municipios": []})

        mock_client.gov.municipios("mg")
        call_args = mock_client._mock_http.request.call_args
        assert "MG" in str(call_args)

    def test_municipio_details(self, mock_client, mock_response):
        """Get municipality details."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "codigo_ibge": 3106200,
                "nome": "Belo Horizonte",
                "microrregiao": "Belo Horizonte",
                "mesorregiao": "Metropolitana de BH",
                "uf": {"id": 31, "sigla": "MG", "nome": "Minas Gerais"},
                "regiao": "Sudeste",
                "latency_ms": 100,
                "cost_brl": 0.0,
            }
        )

        result = mock_client.gov.municipio("3106200")

        assert isinstance(result, MunicipioDetails)
        assert result.nome == "Belo Horizonte"
        assert result.uf["sigla"] == "MG"

    def test_contratos_search(self, mock_client, mock_response):
        """Search government contracts."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "contratos": [
                    {"id": "1", "valor": 100000, "orgao": "26000"},
                ],
                "total": 1,
            }
        )

        result = mock_client.gov.contratos(orgao="26000", ano=2024)

        assert "contratos" in result
        assert len(result["contratos"]) == 1

    def test_contratos_with_cnpj(self, mock_client, mock_response):
        """Search contracts by CNPJ."""
        mock_client._mock_http.request.return_value = mock_response({"contratos": []})

        mock_client.gov.contratos(cnpj="12.345.678/0001-90")
        # Verify CNPJ was cleaned

    def test_contratos_pagination(self, mock_client, mock_response):
        """Contracts support pagination."""
        mock_client._mock_http.request.return_value = mock_response({"contratos": []})

        mock_client.gov.contratos(pagina=2, quantidade=50)

    def test_health(self, mock_client, mock_response):
        """Check government APIs health."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "status": "healthy",
                "apis": {
                    "receita_ws": "up",
                    "via_cep": "up",
                    "ibge": "up",
                },
            }
        )

        health = mock_client.gov.health()

        assert health["status"] == "healthy"
        assert health["apis"]["via_cep"] == "up"

    def test_empty_response_handling(self, mock_client, mock_response):
        """Handle empty responses gracefully."""
        mock_client._mock_http.request.return_value = mock_response({})

        # CNPJ
        result = mock_client.gov.cnpj("12345678000190")
        assert result.razao_social == ""
        assert result.latency_ms == 0

        # CPF
        result = mock_client.gov.validate_cpf("12345678909")
        assert result.valid is False

        # CEP
        result = mock_client.gov.cep("01310100")
        assert result.logradouro == ""

        # Municipios
        result = mock_client.gov.municipios("MG")
        assert result == []
