"""
Neural LAB - AI Solutions Platform
CENSEC Async Resource - Central Notarial de Serviços Eletrônicos Compartilhados.

Versão assíncrona do CENSECResource.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from typing import Any, BinaryIO

from .censec import (
    BuscaEscrituraResult,
    BuscaProcuracaoResult,
    BuscaTestamentoResult,
    EscrituraResult,
    ProcuracaoResult,
    RegistroAtoResult,
    SinalPublicoResult,
    StatusAto,
    TestamentoResult,
    TipoAtoNotarial,
    TipoProcuracao,
    TipoTestamento,
)


class AsyncCENSECResource:
    """
    CENSEC Async - Central Notarial de Serviços Eletrônicos Compartilhados.

    Versão assíncrona para uso com AsyncNeuralLabClient.

    Usage:
        async with AsyncNeuralLabClient(api_key="...") as client:
            # Buscar testamentos
            result = await client.censec.buscar_testamentos(
                cartorio_id="uuid",
                cpf_testador="123.456.789-00"
            )

            # Consultar procuração
            proc = await client.censec.consultar_procuracao(
                cartorio_id="uuid",
                codigo="ABC123"
            )
    """

    def __init__(self, client):
        self._client = client

    # =========================================================================
    # RCTO - Testamentos
    # =========================================================================

    async def buscar_testamentos(
        self,
        cartorio_id: str,
        cpf_testador: str | None = None,
        nome_testador: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        tipo: str | None = None,
        uf: str | None = None,
        pagina: int = 1,
        por_pagina: int = 20,
    ) -> BuscaTestamentoResult:
        """Buscar testamentos no RCTO."""
        params = {
            "cartorio_id": str(cartorio_id),
            "pagina": pagina,
            "por_pagina": min(por_pagina, 50),
        }

        if cpf_testador:
            params["cpf_testador"] = "".join(filter(str.isdigit, cpf_testador))
        if nome_testador:
            params["nome_testador"] = nome_testador
        if data_inicio:
            params["data_inicio"] = data_inicio
        if data_fim:
            params["data_fim"] = data_fim
        if tipo:
            params["tipo"] = tipo
        if uf:
            params["uf"] = uf.upper()

        response = await self._client.get("/v1/censec/rcto/buscar", params=params)

        return BuscaTestamentoResult(
            total=response.get("total", 0),
            testamentos=response.get("testamentos", []),
            pagina=response.get("pagina", pagina),
            por_pagina=response.get("por_pagina", por_pagina),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def consultar_testamento(
        self,
        cartorio_id: str,
        codigo: str,
    ) -> TestamentoResult:
        """Consultar testamento específico."""
        response = await self._client.get(
            f"/v1/censec/rcto/{codigo}",
            params={"cartorio_id": str(cartorio_id)},
        )

        return TestamentoResult(
            id=response.get("id", ""),
            tipo=TipoTestamento(response.get("tipo", "publico")),
            testador_nome=response.get("testador_nome", ""),
            testador_cpf=response.get("testador_cpf"),
            data_lavratura=response.get("data_lavratura", ""),
            livro=response.get("livro", ""),
            folha=response.get("folha", ""),
            cartorio_nome=response.get("cartorio_nome", ""),
            cartorio_cns=response.get("cartorio_cns", ""),
            municipio=response.get("municipio", ""),
            uf=response.get("uf", ""),
            status=StatusAto(response.get("status", "vigente")),
            tem_codicilo=response.get("tem_codicilo", False),
            data_revogacao=response.get("data_revogacao"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def existe_testamento(
        self,
        cartorio_id: str,
        cpf: str,
    ) -> dict[str, Any]:
        """Verificar se pessoa possui testamento."""
        cpf_clean = "".join(filter(str.isdigit, cpf))
        return await self._client.get(
            f"/v1/censec/rcto/existe/{cpf_clean}",
            params={"cartorio_id": str(cartorio_id)},
        )

    async def registrar_testamento(
        self,
        cartorio_id: str,
        tipo: str,
        testador: dict[str, Any],
        data_lavratura: str,
        livro: str,
        folha: str,
        dados_testamento: dict[str, Any],
        tem_codicilo: bool = False,
    ) -> RegistroAtoResult:
        """Registrar testamento no RCTO."""
        response = await self._client.post(
            "/v1/censec/rcto/registrar",
            json={
                "cartorio_id": str(cartorio_id),
                "tipo": tipo,
                "testador": testador,
                "data_lavratura": data_lavratura,
                "livro": livro,
                "folha": folha,
                "dados_testamento": dados_testamento,
                "tem_codicilo": tem_codicilo,
            },
        )

        return RegistroAtoResult(
            id=response.get("id", ""),
            protocolo=response.get("protocolo", ""),
            tipo=TipoAtoNotarial.TESTAMENTO,
            status=response.get("status", "registrado"),
            data_registro=response.get("data_registro", ""),
            mensagem=response.get("mensagem", ""),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def revogar_testamento(
        self,
        cartorio_id: str,
        codigo_testamento: str,
        motivo: str,
        novo_testamento_codigo: str | None = None,
    ) -> dict[str, Any]:
        """Registrar revogação de testamento."""
        return await self._client.post(
            "/v1/censec/rcto/revogar",
            json={
                "cartorio_id": str(cartorio_id),
                "codigo_testamento": codigo_testamento,
                "motivo": motivo,
                "novo_testamento_codigo": novo_testamento_codigo,
            },
        )

    # =========================================================================
    # CENPROC/CEP - Procurações
    # =========================================================================

    async def buscar_procuracoes(
        self,
        cartorio_id: str,
        cpf_outorgante: str | None = None,
        cpf_outorgado: str | None = None,
        nome_outorgante: str | None = None,
        tipo: str | None = None,
        vigentes_apenas: bool = True,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        pagina: int = 1,
        por_pagina: int = 20,
    ) -> BuscaProcuracaoResult:
        """Buscar procurações no CENPROC."""
        params = {
            "cartorio_id": str(cartorio_id),
            "vigentes_apenas": str(vigentes_apenas).lower(),
            "pagina": pagina,
            "por_pagina": min(por_pagina, 50),
        }

        if cpf_outorgante:
            params["cpf_outorgante"] = "".join(filter(str.isdigit, cpf_outorgante))
        if cpf_outorgado:
            params["cpf_outorgado"] = "".join(filter(str.isdigit, cpf_outorgado))
        if nome_outorgante:
            params["nome_outorgante"] = nome_outorgante
        if tipo:
            params["tipo"] = tipo
        if data_inicio:
            params["data_inicio"] = data_inicio
        if data_fim:
            params["data_fim"] = data_fim

        response = await self._client.get(
            "/v1/censec/procuracoes/buscar", params=params
        )

        return BuscaProcuracaoResult(
            total=response.get("total", 0),
            procuracoes=response.get("procuracoes", []),
            pagina=response.get("pagina", pagina),
            por_pagina=response.get("por_pagina", por_pagina),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def consultar_procuracao(
        self,
        cartorio_id: str,
        codigo: str,
    ) -> ProcuracaoResult:
        """Consultar procuração específica."""
        response = await self._client.get(
            f"/v1/censec/procuracoes/{codigo}",
            params={"cartorio_id": str(cartorio_id)},
        )

        return ProcuracaoResult(
            id=response.get("id", ""),
            tipo=TipoProcuracao(response.get("tipo", "ad_negotia")),
            outorgante=response.get("outorgante", {}),
            outorgado=response.get("outorgado", {}),
            poderes=response.get("poderes", []),
            data_lavratura=response.get("data_lavratura", ""),
            data_validade=response.get("data_validade"),
            livro=response.get("livro", ""),
            folha=response.get("folha", ""),
            cartorio_nome=response.get("cartorio_nome", ""),
            cartorio_cns=response.get("cartorio_cns", ""),
            municipio=response.get("municipio", ""),
            uf=response.get("uf", ""),
            status=StatusAto(response.get("status", "vigente")),
            substabelecimentos=response.get("substabelecimentos", []),
            data_revogacao=response.get("data_revogacao"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def verificar_procuracao_vigente(
        self,
        cartorio_id: str,
        codigo: str,
    ) -> dict[str, Any]:
        """Verificar se procuração está vigente."""
        return await self._client.get(
            f"/v1/censec/procuracoes/{codigo}/verificar",
            params={"cartorio_id": str(cartorio_id)},
        )

    async def registrar_procuracao(
        self,
        cartorio_id: str,
        tipo: str,
        outorgante: dict[str, Any],
        outorgado: dict[str, Any],
        poderes: list[str],
        data_lavratura: str,
        livro: str,
        folha: str,
        data_validade: str | None = None,
        dados_adicionais: dict[str, Any] | None = None,
    ) -> RegistroAtoResult:
        """Registrar procuração no CENPROC."""
        payload = {
            "cartorio_id": str(cartorio_id),
            "tipo": tipo,
            "outorgante": outorgante,
            "outorgado": outorgado,
            "poderes": poderes,
            "data_lavratura": data_lavratura,
            "livro": livro,
            "folha": folha,
        }

        if data_validade:
            payload["data_validade"] = data_validade
        if dados_adicionais:
            payload["dados_adicionais"] = dados_adicionais

        response = await self._client.post(
            "/v1/censec/procuracoes/registrar", json=payload
        )

        return RegistroAtoResult(
            id=response.get("id", ""),
            protocolo=response.get("protocolo", ""),
            tipo=TipoAtoNotarial.PROCURACAO,
            status=response.get("status", "registrado"),
            data_registro=response.get("data_registro", ""),
            mensagem=response.get("mensagem", ""),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def registrar_substabelecimento(
        self,
        cartorio_id: str,
        codigo_procuracao: str,
        novo_outorgado: dict[str, Any],
        poderes_substabelecidos: list[str],
        com_reserva: bool = True,
        data_lavratura: str = None,
    ) -> RegistroAtoResult:
        """Registrar substabelecimento de procuração."""
        response = await self._client.post(
            "/v1/censec/procuracoes/substabelecer",
            json={
                "cartorio_id": str(cartorio_id),
                "codigo_procuracao": codigo_procuracao,
                "novo_outorgado": novo_outorgado,
                "poderes_substabelecidos": poderes_substabelecidos,
                "com_reserva": com_reserva,
                "data_lavratura": data_lavratura,
            },
        )

        return RegistroAtoResult(
            id=response.get("id", ""),
            protocolo=response.get("protocolo", ""),
            tipo=TipoAtoNotarial.SUBSTABELECIMENTO,
            status=response.get("status", "registrado"),
            data_registro=response.get("data_registro", ""),
            mensagem=response.get("mensagem", ""),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def revogar_procuracao(
        self,
        cartorio_id: str,
        codigo_procuracao: str,
        motivo: str,
        data_revogacao: str | None = None,
    ) -> RegistroAtoResult:
        """Registrar revogação de procuração."""
        response = await self._client.post(
            "/v1/censec/procuracoes/revogar",
            json={
                "cartorio_id": str(cartorio_id),
                "codigo_procuracao": codigo_procuracao,
                "motivo": motivo,
                "data_revogacao": data_revogacao,
            },
        )

        return RegistroAtoResult(
            id=response.get("id", ""),
            protocolo=response.get("protocolo", ""),
            tipo=TipoAtoNotarial.REVOGACAO,
            status=response.get("status", "registrado"),
            data_registro=response.get("data_registro", ""),
            mensagem=response.get("mensagem", ""),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    # =========================================================================
    # CESDI - Escrituras
    # =========================================================================

    async def buscar_escrituras(
        self,
        cartorio_id: str,
        cpf_parte: str | None = None,
        nome_parte: str | None = None,
        tipo: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        uf: str | None = None,
        pagina: int = 1,
        por_pagina: int = 20,
    ) -> BuscaEscrituraResult:
        """Buscar escrituras no CEP/CESDI."""
        params = {
            "cartorio_id": str(cartorio_id),
            "pagina": pagina,
            "por_pagina": min(por_pagina, 50),
        }

        if cpf_parte:
            params["cpf_parte"] = "".join(filter(str.isdigit, cpf_parte))
        if nome_parte:
            params["nome_parte"] = nome_parte
        if tipo:
            params["tipo"] = tipo
        if data_inicio:
            params["data_inicio"] = data_inicio
        if data_fim:
            params["data_fim"] = data_fim
        if uf:
            params["uf"] = uf.upper()

        response = await self._client.get("/v1/censec/escrituras/buscar", params=params)

        return BuscaEscrituraResult(
            total=response.get("total", 0),
            escrituras=response.get("escrituras", []),
            pagina=response.get("pagina", pagina),
            por_pagina=response.get("por_pagina", por_pagina),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def consultar_escritura(
        self,
        cartorio_id: str,
        codigo: str,
    ) -> EscrituraResult:
        """Consultar escritura específica."""
        response = await self._client.get(
            f"/v1/censec/escrituras/{codigo}",
            params={"cartorio_id": str(cartorio_id)},
        )

        return EscrituraResult(
            id=response.get("id", ""),
            tipo=TipoAtoNotarial(response.get("tipo", "escritura_publica")),
            partes=response.get("partes", []),
            objeto=response.get("objeto", ""),
            valor=response.get("valor"),
            data_lavratura=response.get("data_lavratura", ""),
            livro=response.get("livro", ""),
            folha=response.get("folha", ""),
            cartorio_nome=response.get("cartorio_nome", ""),
            cartorio_cns=response.get("cartorio_cns", ""),
            municipio=response.get("municipio", ""),
            uf=response.get("uf", ""),
            status=StatusAto(response.get("status", "vigente")),
            imovel=response.get("imovel"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def registrar_escritura(
        self,
        cartorio_id: str,
        tipo: str,
        partes: list[dict[str, Any]],
        objeto: str,
        data_lavratura: str,
        livro: str,
        folha: str,
        valor: float | None = None,
        imovel: dict[str, Any] | None = None,
        dados_adicionais: dict[str, Any] | None = None,
    ) -> RegistroAtoResult:
        """Registrar escritura no CESDI/CEP."""
        payload = {
            "cartorio_id": str(cartorio_id),
            "tipo": tipo,
            "partes": partes,
            "objeto": objeto,
            "data_lavratura": data_lavratura,
            "livro": livro,
            "folha": folha,
        }

        if valor:
            payload["valor"] = valor
        if imovel:
            payload["imovel"] = imovel
        if dados_adicionais:
            payload["dados_adicionais"] = dados_adicionais

        response = await self._client.post(
            "/v1/censec/escrituras/registrar", json=payload
        )

        return RegistroAtoResult(
            id=response.get("id", ""),
            protocolo=response.get("protocolo", ""),
            tipo=TipoAtoNotarial(tipo),
            status=response.get("status", "registrado"),
            data_registro=response.get("data_registro", ""),
            mensagem=response.get("mensagem", ""),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    # =========================================================================
    # CNSIP - Sinal Público
    # =========================================================================

    async def consultar_sinal_publico(
        self,
        cartorio_id: str,
        cns_cartorio: str,
    ) -> SinalPublicoResult:
        """Consultar sinal público de um cartório."""
        response = await self._client.get(
            f"/v1/censec/cnsip/{cns_cartorio}",
            params={"cartorio_id": str(cartorio_id)},
        )

        return SinalPublicoResult(
            id=response.get("id", ""),
            notario_nome=response.get("notario_nome", ""),
            notario_cpf=response.get("notario_cpf", ""),
            cartorio_nome=response.get("cartorio_nome", ""),
            cartorio_cns=cns_cartorio,
            uf=response.get("uf", ""),
            sinal_base64=response.get("sinal_base64", ""),
            data_cadastro=response.get("data_cadastro", ""),
            status=response.get("status", "ativo"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def registrar_sinal_publico(
        self,
        cartorio_id: str,
        sinal_imagem: BinaryIO,
        notario_cpf: str,
    ) -> dict[str, Any]:
        """Registrar/atualizar sinal público."""
        return await self._client.post(
            "/v1/censec/cnsip/registrar",
            files={"sinal": sinal_imagem},
            data={
                "cartorio_id": str(cartorio_id),
                "notario_cpf": "".join(filter(str.isdigit, notario_cpf)),
            },
        )

    # =========================================================================
    # Utilidades
    # =========================================================================

    async def health(self) -> dict[str, Any]:
        """Verificar saúde da integração CENSEC."""
        return await self._client.get("/v1/censec/health")

    async def get_estatisticas(
        self,
        cartorio_id: str,
        periodo: str = "mes",
    ) -> dict[str, Any]:
        """Obter estatísticas de uso."""
        return await self._client.get(
            "/v1/censec/estatisticas",
            params={
                "cartorio_id": str(cartorio_id),
                "periodo": periodo,
            },
        )
