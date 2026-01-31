"""
Neural LAB - AI Solutions Platform
Async Government APIs Resource.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from typing import Any

from .gov import CEPResult, CNPJResult, CPFValidation, Municipio, MunicipioDetails


class AsyncGovResource:
    """Async government APIs resource for Brazilian government data."""

    def __init__(self, client):
        self._client = client

    async def cnpj(self, cnpj: str) -> CNPJResult:
        """Lookup CNPJ information."""
        cnpj_clean = "".join(filter(str.isdigit, cnpj))
        response = await self._client.get(f"/v1/gov/cnpj/{cnpj_clean}")

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
            endereco=response.get("endereco", {}),
            telefone=response.get("telefone"),
            email=response.get("email"),
            capital_social=response.get("capital_social"),
            data_abertura=response.get("data_abertura"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def validate_cpf(self, cpf: str) -> CPFValidation:
        """Validate CPF format and check digit."""
        cpf_clean = "".join(filter(str.isdigit, cpf))
        response = await self._client.get(f"/v1/gov/cpf/{cpf_clean}/validate")

        return CPFValidation(
            cpf=response.get("cpf", cpf),
            valid=response.get("valid", False),
            reason=response.get("reason"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def cep(self, cep: str) -> CEPResult:
        """Lookup address by CEP."""
        cep_clean = "".join(filter(str.isdigit, cep))
        response = await self._client.get(f"/v1/gov/cep/{cep_clean}")

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

    async def municipios(self, uf: str) -> list[Municipio]:
        """List all municipalities in a state."""
        response = await self._client.get(f"/v1/gov/ibge/municipios/{uf.upper()}")
        return [
            Municipio(
                codigo_ibge=m.get("codigo_ibge", 0),
                nome=m.get("nome", ""),
            )
            for m in response.get("municipios", [])
        ]

    async def municipio(self, codigo: str) -> MunicipioDetails:
        """Get municipality details by IBGE code."""
        response = await self._client.get(f"/v1/gov/ibge/municipio/{codigo}")

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

    async def contratos(
        self,
        orgao: str | None = None,
        ano: int | None = None,
        cnpj: str | None = None,
        pagina: int = 1,
        quantidade: int = 20,
    ) -> dict[str, Any]:
        """Search federal government contracts."""
        params = {"pagina": pagina, "quantidade": quantidade}
        if orgao:
            params["orgao"] = orgao
        if ano:
            params["ano"] = ano
        if cnpj:
            params["cnpj"] = "".join(filter(str.isdigit, cnpj))

        return await self._client.get("/v1/gov/transparencia/contratos", params=params)

    async def health(self) -> dict[str, Any]:
        """Check government APIs health."""
        return await self._client.get("/v1/gov/health")
