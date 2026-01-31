"""
Neural LAB - AI Solutions Platform
Government APIs Resource - Brazilian government data access.

Integrates with:
- ReceitaWS (CNPJ lookup)
- ViaCEP (Address lookup)
- IBGE (Municipalities)
- Portal da Transparência (Federal contracts)

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from dataclasses import dataclass
from typing import Any

from ..base import DataclassMixin


@dataclass
class CNPJResult(DataclassMixin):
    """CNPJ lookup result."""

    cnpj: str
    razao_social: str
    nome_fantasia: str | None
    situacao: str
    data_situacao: str | None
    tipo: str
    porte: str
    natureza_juridica: str
    atividade_principal: list[dict[str, str]]
    atividades_secundarias: list[dict[str, str]]
    endereco: dict[str, str]
    telefone: str | None
    email: str | None
    capital_social: str | None
    data_abertura: str | None
    latency_ms: int
    cost_brl: float


@dataclass
class CPFValidation(DataclassMixin):
    """CPF validation result."""

    cpf: str
    valid: bool
    reason: str | None
    latency_ms: int
    cost_brl: float


@dataclass
class CEPResult(DataclassMixin):
    """CEP lookup result."""

    cep: str
    logradouro: str
    complemento: str | None
    bairro: str
    municipio: str
    uf: str
    ibge: str
    ddd: str | None
    latency_ms: int
    cost_brl: float


@dataclass
class Municipio(DataclassMixin):
    """Municipality info."""

    codigo_ibge: int
    nome: str


@dataclass
class MunicipioDetails(DataclassMixin):
    """Municipality details."""

    codigo_ibge: int
    nome: str
    microrregiao: str | None
    mesorregiao: str | None
    uf: dict[str, str]
    regiao: str | None
    latency_ms: int
    cost_brl: float


class GovResource:
    """
    Government APIs resource for Brazilian government data.

    Usage:
        # CNPJ lookup
        company = client.gov.cnpj("12.345.678/0001-90")
        print(company.razao_social)

        # CEP lookup
        address = client.gov.cep("01310-100")
        print(address.logradouro)

        # CPF validation
        result = client.gov.validate_cpf("123.456.789-09")
        print(result.valid)

        # List municipalities
        cities = client.gov.municipios("MG")
    """

    def __init__(self, client):
        self._client = client

    def cnpj(self, cnpj: str) -> CNPJResult:
        """
        Lookup CNPJ information.

        Args:
            cnpj: CNPJ number (with or without formatting)

        Returns:
            CNPJResult with company data
        """
        # Clean CNPJ for URL
        cnpj_clean = "".join(filter(str.isdigit, cnpj))

        response = self._client.get(f"/v1/gov/cnpj/{cnpj_clean}")

        endereco = response.get("endereco", {})

        return CNPJResult(
            cnpj=response.get("cnpj", cnpj),
            razao_social=response.get("razao_social", ""),
            nome_fantasia=response.get("nome_fantasia"),
            situacao=response.get("situacao", ""),
            data_situacao=response.get("data_situacao"),
            tipo=response.get("tipo", ""),
            porte=response.get("porte", ""),
            natureza_juridica=response.get("natureza_juridica", ""),
            atividade_principal=response.get("atividade_principal", []),
            atividades_secundarias=response.get("atividades_secundarias", []),
            endereco=endereco,
            telefone=response.get("telefone"),
            email=response.get("email"),
            capital_social=response.get("capital_social"),
            data_abertura=response.get("data_abertura"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def validate_cpf(self, cpf: str) -> CPFValidation:
        """
        Validate CPF format and check digit.

        Args:
            cpf: CPF number (with or without formatting)

        Returns:
            CPFValidation result
        """
        cpf_clean = "".join(filter(str.isdigit, cpf))

        response = self._client.get(f"/v1/gov/cpf/{cpf_clean}/validate")

        return CPFValidation(
            cpf=response.get("cpf", cpf),
            valid=response.get("valid", False),
            reason=response.get("reason"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def cep(self, cep: str) -> CEPResult:
        """
        Lookup address by CEP.

        Args:
            cep: CEP number (with or without formatting)

        Returns:
            CEPResult with address data
        """
        cep_clean = "".join(filter(str.isdigit, cep))

        response = self._client.get(f"/v1/gov/cep/{cep_clean}")

        return CEPResult(
            cep=response.get("cep", cep),
            logradouro=response.get("logradouro", ""),
            complemento=response.get("complemento"),
            bairro=response.get("bairro", ""),
            municipio=response.get("municipio", ""),
            uf=response.get("uf", ""),
            ibge=response.get("ibge", ""),
            ddd=response.get("ddd"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def municipios(self, uf: str) -> list[Municipio]:
        """
        List all municipalities in a state.

        Args:
            uf: State code (e.g., MG, SP, RJ)

        Returns:
            List of municipalities
        """
        response = self._client.get(f"/v1/gov/ibge/municipios/{uf.upper()}")

        return [
            Municipio(
                codigo_ibge=m.get("codigo_ibge", 0),
                nome=m.get("nome", ""),
            )
            for m in response.get("municipios", [])
        ]

    def municipio(self, codigo: str) -> MunicipioDetails:
        """
        Get municipality details by IBGE code.

        Args:
            codigo: IBGE municipality code

        Returns:
            MunicipioDetails with full data
        """
        response = self._client.get(f"/v1/gov/ibge/municipio/{codigo}")

        return MunicipioDetails(
            codigo_ibge=response.get("codigo_ibge", 0),
            nome=response.get("nome", ""),
            microrregiao=response.get("microrregiao"),
            mesorregiao=response.get("mesorregiao"),
            uf=response.get("uf", {}),
            regiao=response.get("regiao"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def contratos(
        self,
        orgao: str | None = None,
        ano: int | None = None,
        cnpj: str | None = None,
        pagina: int = 1,
        quantidade: int = 20,
    ) -> dict[str, Any]:
        """
        Search federal government contracts.

        Args:
            orgao: Agency code (e.g., 26000 for MEC)
            ano: Contract year
            cnpj: Supplier CNPJ
            pagina: Page number
            quantidade: Results per page (max 100)

        Returns:
            Contract search results
        """
        params = {
            "pagina": pagina,
            "quantidade": quantidade,
        }
        if orgao:
            params["orgao"] = orgao
        if ano:
            params["ano"] = ano
        if cnpj:
            params["cnpj"] = "".join(filter(str.isdigit, cnpj))

        return self._client.get("/v1/gov/transparencia/contratos", params=params)

    def health(self) -> dict[str, Any]:
        """
        Check government APIs health.

        Returns:
            Health status with API availability
        """
        return self._client.get("/v1/gov/health")
