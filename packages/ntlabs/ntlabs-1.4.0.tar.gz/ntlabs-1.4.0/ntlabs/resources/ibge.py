"""
Neural LAB - AI Solutions Platform
IBGE Resource - Complete access to Brazilian geographic and demographic data.

Integrates with:
- IBGE Localidades API (States, Municipalities, Regions)
- IBGE Agregados API (Population, GDP, Social Indicators)

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from dataclasses import dataclass
from typing import Any

from ..base import DataclassMixin


@dataclass
class Estado(DataclassMixin):
    """Brazilian state information."""

    id: int
    sigla: str
    nome: str
    regiao: dict[str, Any]
    latency_ms: int
    cost_brl: float


@dataclass
class Regiao(DataclassMixin):
    """Brazilian region information."""

    id: int
    sigla: str
    nome: str
    latency_ms: int
    cost_brl: float


@dataclass
class Municipio(DataclassMixin):
    """Municipality basic information."""

    id: int
    nome: str


@dataclass
class MunicipioDetails(DataclassMixin):
    """Municipality detailed information."""

    id: int
    nome: str
    microrregiao: dict[str, Any] | None
    mesorregiao: dict[str, Any] | None
    uf: dict[str, Any] | None
    regiao: dict[str, Any] | None
    regiao_imediata: dict[str, Any] | None
    regiao_intermediaria: dict[str, Any] | None
    latency_ms: int
    cost_brl: float


@dataclass
class Mesorregiao(DataclassMixin):
    """Mesoregion information."""

    id: int
    nome: str


@dataclass
class Microrregiao(DataclassMixin):
    """Microregion information."""

    id: int
    nome: str
    mesorregiao: dict[str, Any]


@dataclass
class Populacao(DataclassMixin):
    """Population data."""

    localidade_id: int
    localidade_nome: str | None
    ano: int
    populacao: int | None
    fonte: str
    latency_ms: int
    cost_brl: float


@dataclass
class PIB(DataclassMixin):
    """GDP (PIB) data."""

    localidade_id: int
    localidade_nome: str | None
    ano: int
    pib_per_capita: float | None
    unidade: str
    fonte: str
    latency_ms: int
    cost_brl: float


@dataclass
class Indicadores(DataclassMixin):
    """Social indicators summary."""

    localidade_id: int
    indicadores: dict[str, Any]
    fonte: str
    latency_ms: int
    cost_brl: float


class IBGEResource:
    """
    IBGE Resource for Brazilian geographic and demographic data.

    Provides complete access to:
    - States (estados)
    - Municipalities (municípios)
    - Regions (regiões)
    - Mesoregions (mesorregiões)
    - Microregions (microrregiões)
    - Population estimates
    - GDP per capita
    - Social indicators

    Usage:
        # List states
        states = client.ibge.estados()
        for state in states:
            print(f"{state.sigla}: {state.nome}")

        # Get state details
        mg = client.ibge.estado("MG")
        print(mg.nome)  # "Minas Gerais"

        # List municipalities in a state
        cities = client.ibge.municipios("MG")
        print(f"MG has {len(cities)} municipalities")

        # Get municipality details
        bh = client.ibge.municipio(3106200)  # Belo Horizonte
        print(f"{bh.nome} - {bh.uf['sigla']}")

        # Get population
        pop = client.ibge.populacao(3106200)
        print(f"Population: {pop.populacao:,}")

        # Get GDP per capita
        pib = client.ibge.pib(3106200)
        print(f"PIB per capita: R$ {pib.pib_per_capita:,.2f}")

        # Get social indicators
        ind = client.ibge.indicadores(3106200)
        print(ind.indicadores)
    """

    def __init__(self, client):
        self._client = client

    def estados(self) -> list[Estado]:
        """
        List all Brazilian states.

        Returns:
            List of Estado objects with all 27 Brazilian states
        """
        response = self._client.get("/v1/ibge/estados")

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

    def estado(self, uf: str) -> Estado:
        """
        Get state details by UF code.

        Args:
            uf: State code (e.g., MG, SP, RJ)

        Returns:
            Estado with full details
        """
        response = self._client.get(f"/v1/ibge/estados/{uf.upper()}")

        return Estado(
            id=response.get("id", 0),
            sigla=response.get("sigla", ""),
            nome=response.get("nome", ""),
            regiao=response.get("regiao", {}),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def regioes(self) -> list[Regiao]:
        """
        List all Brazilian regions.

        Returns:
            List of 5 regions (Norte, Nordeste, Sudeste, Sul, Centro-Oeste)
        """
        response = self._client.get("/v1/ibge/regioes")

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

    def municipios(self, uf: str) -> list[Municipio]:
        """
        List all municipalities in a state.

        Args:
            uf: State code (e.g., MG, SP, RJ)

        Returns:
            List of municipalities in the state
        """
        response = self._client.get(f"/v1/ibge/municipios/{uf.upper()}")

        return [
            Municipio(
                id=m.get("id", 0),
                nome=m.get("nome", ""),
            )
            for m in response.get("municipios", [])
        ]

    def municipio(self, codigo: int) -> MunicipioDetails:
        """
        Get municipality details by IBGE code.

        Args:
            codigo: IBGE municipality code (e.g., 3106200 for Belo Horizonte)

        Returns:
            MunicipioDetails with full information
        """
        response = self._client.get(f"/v1/ibge/municipio/{codigo}")

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

    def mesorregioes(self, uf: str) -> list[Mesorregiao]:
        """
        List all mesoregions in a state.

        Args:
            uf: State code (e.g., MG, SP, RJ)

        Returns:
            List of mesoregions in the state
        """
        response = self._client.get(f"/v1/ibge/mesorregioes/{uf.upper()}")

        return [
            Mesorregiao(
                id=m.get("id", 0),
                nome=m.get("nome", ""),
            )
            for m in response.get("mesorregioes", [])
        ]

    def microrregioes(self, uf: str) -> list[Microrregiao]:
        """
        List all microregions in a state.

        Args:
            uf: State code (e.g., MG, SP, RJ)

        Returns:
            List of microregions in the state
        """
        response = self._client.get(f"/v1/ibge/microrregioes/{uf.upper()}")

        return [
            Microrregiao(
                id=m.get("id", 0),
                nome=m.get("nome", ""),
                mesorregiao=m.get("mesorregiao", {}),
            )
            for m in response.get("microrregioes", [])
        ]

    def populacao(self, codigo: int, ano: int | None = None) -> Populacao:
        """
        Get estimated population for a municipality or state.

        Args:
            codigo: IBGE code (2 digits for state, 7 for municipality)
            ano: Reference year (default: current year)

        Returns:
            Populacao with population estimate
        """
        params = {}
        if ano:
            params["ano"] = ano

        response = self._client.get(f"/v1/ibge/populacao/{codigo}", params=params)

        return Populacao(
            localidade_id=response.get("localidade_id", codigo),
            localidade_nome=response.get("localidade_nome"),
            ano=response.get("ano", 0),
            populacao=response.get("populacao"),
            fonte=response.get("fonte", "IBGE"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def pib(self, codigo: int, ano: int | None = None) -> PIB:
        """
        Get GDP (PIB) per capita for a municipality.

        Args:
            codigo: IBGE municipality code (7 digits)
            ano: Reference year (default: latest available, usually 2 years ago)

        Returns:
            PIB with GDP per capita data
        """
        params = {}
        if ano:
            params["ano"] = ano

        response = self._client.get(f"/v1/ibge/pib/{codigo}", params=params)

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

    def indicadores(self, codigo: int) -> Indicadores:
        """
        Get social indicators for a municipality.

        Includes: population, GDP per capita, and other available indicators.

        Args:
            codigo: IBGE municipality code (7 digits)

        Returns:
            Indicadores with all available social indicators
        """
        response = self._client.get(f"/v1/ibge/indicadores/{codigo}")

        return Indicadores(
            localidade_id=response.get("localidade_id", codigo),
            indicadores=response.get("indicadores", {}),
            fonte=response.get("fonte", "IBGE"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def health(self) -> dict[str, Any]:
        """
        Check IBGE API health.

        Returns:
            Health status with API availability
        """
        return self._client.get("/v1/ibge/health")
