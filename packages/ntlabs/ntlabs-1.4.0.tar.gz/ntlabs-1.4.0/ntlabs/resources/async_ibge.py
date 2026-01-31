"""
Neural LAB - AI Solutions Platform
Async IBGE Resource.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from typing import Any

from .ibge import (
    PIB,
    Estado,
    Indicadores,
    Mesorregiao,
    Microrregiao,
    Municipio,
    MunicipioDetails,
    Populacao,
    Regiao,
)


class AsyncIBGEResource:
    """Async IBGE resource for Brazilian geographic and demographic data."""

    def __init__(self, client):
        self._client = client

    async def estados(self) -> list[Estado]:
        """List all Brazilian states."""
        response = await self._client.get("/v1/ibge/estados")
        return [
            Estado(
                id=e.get("id", 0),
                sigla=e.get("sigla", ""),
                nome=e.get("nome", ""),
                regiao=e.get("regiao", {}),
                latency_ms=response.get("latency_ms", 0),
                cost_brl=response.get("cost_brl", 0),
            )
            for e in response.get("estados", [])
        ]

    async def estado(self, uf: str) -> Estado:
        """Get state details by UF code."""
        response = await self._client.get(f"/v1/ibge/estados/{uf.upper()}")
        return Estado(
            id=response.get("id", 0),
            sigla=response.get("sigla", ""),
            nome=response.get("nome", ""),
            regiao=response.get("regiao", {}),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def regioes(self) -> list[Regiao]:
        """List all Brazilian regions."""
        response = await self._client.get("/v1/ibge/regioes")
        return [
            Regiao(
                id=r.get("id", 0),
                sigla=r.get("sigla", ""),
                nome=r.get("nome", ""),
                latency_ms=response.get("latency_ms", 0),
                cost_brl=response.get("cost_brl", 0),
            )
            for r in response.get("regioes", [])
        ]

    async def municipios(self, uf: str) -> list[Municipio]:
        """List all municipalities in a state."""
        response = await self._client.get(f"/v1/ibge/municipios/{uf.upper()}")
        return [
            Municipio(id=m.get("id", 0), nome=m.get("nome", ""))
            for m in response.get("municipios", [])
        ]

    async def municipio(self, codigo: int) -> MunicipioDetails:
        """Get municipality details by IBGE code."""
        response = await self._client.get(f"/v1/ibge/municipio/{codigo}")
        return MunicipioDetails(
            id=response.get("id", 0),
            nome=response.get("nome", ""),
            microrregiao=response.get("microrregiao"),
            mesorregiao=response.get("mesorregiao"),
            uf=response.get("uf"),
            regiao=response.get("regiao"),
            regiao_imediata=response.get("regiao_imediata"),
            regiao_intermediaria=response.get("regiao_intermediaria"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def mesorregioes(self, uf: str) -> list[Mesorregiao]:
        """List all mesoregions in a state."""
        response = await self._client.get(f"/v1/ibge/mesorregioes/{uf.upper()}")
        return [
            Mesorregiao(id=m.get("id", 0), nome=m.get("nome", ""))
            for m in response.get("mesorregioes", [])
        ]

    async def microrregioes(self, uf: str) -> list[Microrregiao]:
        """List all microregions in a state."""
        response = await self._client.get(f"/v1/ibge/microrregioes/{uf.upper()}")
        return [
            Microrregiao(
                id=m.get("id", 0),
                nome=m.get("nome", ""),
                mesorregiao=m.get("mesorregiao", {}),
            )
            for m in response.get("microrregioes", [])
        ]

    async def populacao(self, codigo: int, ano: int | None = None) -> Populacao:
        """Get estimated population for a municipality or state."""
        params = {"ano": ano} if ano else {}
        response = await self._client.get(f"/v1/ibge/populacao/{codigo}", params=params)
        return Populacao(
            localidade_id=response.get("localidade_id", codigo),
            localidade_nome=response.get("localidade_nome"),
            ano=response.get("ano", 0),
            populacao=response.get("populacao"),
            fonte=response.get("fonte", "IBGE"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def pib(self, codigo: int, ano: int | None = None) -> PIB:
        """Get GDP (PIB) per capita for a municipality."""
        params = {"ano": ano} if ano else {}
        response = await self._client.get(f"/v1/ibge/pib/{codigo}", params=params)
        return PIB(
            localidade_id=response.get("localidade_id", codigo),
            localidade_nome=response.get("localidade_nome"),
            ano=response.get("ano", 0),
            pib_per_capita=response.get("pib_per_capita"),
            unidade=response.get("unidade", "R$"),
            fonte=response.get("fonte", "IBGE"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def indicadores(self, codigo: int) -> Indicadores:
        """Get social indicators for a municipality."""
        response = await self._client.get(f"/v1/ibge/indicadores/{codigo}")
        return Indicadores(
            localidade_id=response.get("localidade_id", codigo),
            indicadores=response.get("indicadores", {}),
            fonte=response.get("fonte", "IBGE"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def health(self) -> dict[str, Any]:
        """Check IBGE API health."""
        return await self._client.get("/v1/ibge/health")
