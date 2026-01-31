"""
Neural LAB - ONR/SREI Async Integration
Versão assíncrona da integração com ONR.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from typing import TYPE_CHECKING, Any

from .onr import (
    BuscaPropriedadeResult,
    CertidaoResult,
    IndisponibilidadeResult,
    MatriculaInfo,
    OficioResult,
    PenhoraResult,
    ProtocoloResult,
    StatusCertidao,
    StatusProtocolo,
    TipoCertidao,
    TipoPenhora,
    TipoProtocolo,
)

if TYPE_CHECKING:
    from neural_lab.async_client import AsyncNeuralLabClient


class AsyncONRResource:
    """
    Async ONR/SREI Resource - Registro de Imóveis.

    Versão assíncrona da integração com ONR.

    Example:
        >>> async with AsyncNeuralLabClient(api_key="nl_merc_xxx") as client:
        ...     # Consultar matrícula
        ...     matricula = await client.onr.consultar_matricula(
        ...         cartorio_id="123",
        ...         cns="12345",
        ...         matricula="1234"
        ...     )
        ...
        ...     # Buscar propriedades
        ...     props = await client.onr.buscar_propriedades(
        ...         cartorio_id="123",
        ...         cpf="123.456.789-00"
        ...     )
    """

    ENDPOINT_PREFIX = "/v1/onr"

    def __init__(self, client: "AsyncNeuralLabClient"):
        """Initialize async ONR resource."""
        self._client = client

    # =========================================================================
    # Matrículas
    # =========================================================================

    async def consultar_matricula(
        self,
        cartorio_id: str,
        cns: str,
        matricula: str,
        incluir_historico: bool = False,
    ) -> MatriculaInfo:
        """
        Consultar informações de uma matrícula.

        Args:
            cartorio_id: ID do cartório solicitante.
            cns: CNS da serventia.
            matricula: Número da matrícula.
            incluir_historico: Incluir histórico.

        Returns:
            MatriculaInfo: Dados da matrícula.
        """
        params = {"incluir_historico": incluir_historico}

        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/serventias/{cns}/matriculas/{matricula}",
            params=params,
        )

        return MatriculaInfo(
            matricula=response.get("matricula", matricula),
            serventia=response.get("serventia", ""),
            cns=response.get("cns", cns),
            uf=response.get("uf", ""),
            municipio=response.get("municipio", ""),
            area=response.get("area"),
            endereco=response.get("endereco"),
            proprietarios=response.get("proprietarios", []),
            onus=response.get("onus", []),
            averbacoes=response.get("averbacoes", []),
            atualizado_em=response.get("atualizado_em"),
            raw_response=response,
        )

    async def visualizar_matricula(
        self,
        cartorio_id: str,
        cns: str,
        matricula: str,
    ) -> dict[str, Any]:
        """Visualizar matrícula (versão resumida)."""
        return await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/serventias/{cns}/matriculas/{matricula}/visualizar"
        )

    # =========================================================================
    # Certidões
    # =========================================================================

    async def solicitar_certidao(
        self,
        cartorio_id: str,
        cns_destino: str,
        matricula: str,
        tipo: TipoCertidao,
        finalidade: str | None = None,
        urgente: bool = False,
    ) -> CertidaoResult:
        """
        Solicitar certidão de imóvel.

        Args:
            cartorio_id: ID do cartório solicitante.
            cns_destino: CNS da serventia destino.
            matricula: Número da matrícula.
            tipo: Tipo de certidão.
            finalidade: Finalidade da certidão.
            urgente: Emissão urgente.

        Returns:
            CertidaoResult: Dados do pedido.
        """
        payload = {
            "matricula": matricula,
            "tipo": tipo.value,
            "urgente": urgente,
        }

        if finalidade:
            payload["finalidade"] = finalidade

        response = await self._client.post(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/serventias/{cns_destino}/certidoes",
            json=payload,
        )

        return CertidaoResult(
            success=response.get("success", True),
            pedido_id=response.get("pedido_id", ""),
            tipo=tipo,
            matricula=matricula,
            serventia=response.get("serventia", ""),
            status=StatusCertidao(response.get("status", "solicitada")),
            solicitado_em=response.get("solicitado_em", ""),
            validade=response.get("validade"),
            url_download=response.get("url_download"),
            codigo_verificacao=response.get("codigo_verificacao"),
            valor=response.get("valor"),
            raw_response=response,
        )

    async def consultar_certidao(
        self,
        cartorio_id: str,
        pedido_id: str,
    ) -> CertidaoResult:
        """Consultar status de pedido de certidão."""
        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/certidoes/{pedido_id}"
        )

        return CertidaoResult(
            success=response.get("success", True),
            pedido_id=pedido_id,
            tipo=TipoCertidao(response.get("tipo", "matricula")),
            matricula=response.get("matricula", ""),
            serventia=response.get("serventia", ""),
            status=StatusCertidao(response.get("status", "em_processamento")),
            solicitado_em=response.get("solicitado_em", ""),
            validade=response.get("validade"),
            url_download=response.get("url_download"),
            codigo_verificacao=response.get("codigo_verificacao"),
            valor=response.get("valor"),
            raw_response=response,
        )

    async def download_certidao(
        self,
        cartorio_id: str,
        pedido_id: str,
    ) -> bytes:
        """Download do PDF da certidão."""
        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/certidoes/{pedido_id}/download"
        )
        return response.get("arquivo_bytes", b"")

    # =========================================================================
    # Busca de Propriedades
    # =========================================================================

    async def buscar_propriedades(
        self,
        cartorio_id: str,
        cpf: str | None = None,
        cnpj: str | None = None,
        uf: str | None = None,
    ) -> BuscaPropriedadeResult:
        """Buscar propriedades por CPF ou CNPJ."""
        params = {}
        if cpf:
            params["cpf"] = cpf
        if cnpj:
            params["cnpj"] = cnpj
        if uf:
            params["uf"] = uf

        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/propriedades",
            params=params,
        )

        return BuscaPropriedadeResult(
            success=response.get("success", True),
            cpf_cnpj=cpf or cnpj or "",
            total=response.get("total", 0),
            imoveis=response.get("imoveis", []),
            raw_response=response,
        )

    # =========================================================================
    # e-Protocolo
    # =========================================================================

    async def criar_protocolo(
        self,
        cartorio_id: str,
        cns_destino: str,
        matricula: str,
        tipo: TipoProtocolo,
        documento_id: str,
        titulo: str,
        descricao: str | None = None,
        partes: list[dict[str, Any]] | None = None,
    ) -> ProtocoloResult:
        """Criar e-Protocolo."""
        payload = {
            "matricula": matricula,
            "tipo": tipo.value,
            "documento_id": documento_id,
            "titulo": titulo,
        }

        if descricao:
            payload["descricao"] = descricao
        if partes:
            payload["partes"] = partes

        response = await self._client.post(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/serventias/{cns_destino}/protocolos",
            json=payload,
        )

        return ProtocoloResult(
            success=response.get("success", True),
            protocolo=response.get("protocolo", ""),
            numero_prenotacao=response.get("numero_prenotacao", ""),
            tipo=tipo,
            matricula=matricula,
            serventia=response.get("serventia", ""),
            status=StatusProtocolo(response.get("status", "prenotado")),
            prenotado_em=response.get("prenotado_em", ""),
            prazo_exigencia=response.get("prazo_exigencia"),
            exigencias=response.get("exigencias", []),
            registrado_em=response.get("registrado_em"),
            raw_response=response,
        )

    async def consultar_protocolo(
        self,
        cartorio_id: str,
        protocolo: str,
    ) -> ProtocoloResult:
        """Consultar status de protocolo."""
        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/protocolos/{protocolo}"
        )

        return ProtocoloResult(
            success=response.get("success", True),
            protocolo=protocolo,
            numero_prenotacao=response.get("numero_prenotacao", ""),
            tipo=TipoProtocolo(response.get("tipo", "registro")),
            matricula=response.get("matricula", ""),
            serventia=response.get("serventia", ""),
            status=StatusProtocolo(response.get("status", "em_analise")),
            prenotado_em=response.get("prenotado_em", ""),
            prazo_exigencia=response.get("prazo_exigencia"),
            exigencias=response.get("exigencias", []),
            registrado_em=response.get("registrado_em"),
            raw_response=response,
        )

    async def responder_exigencia(
        self,
        cartorio_id: str,
        protocolo: str,
        documento_id: str,
        observacao: str | None = None,
    ) -> ProtocoloResult:
        """Responder exigência de protocolo."""
        payload = {"documento_id": documento_id}
        if observacao:
            payload["observacao"] = observacao

        response = await self._client.post(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/protocolos/{protocolo}/exigencia",
            json=payload,
        )

        return ProtocoloResult(
            success=response.get("success", True),
            protocolo=protocolo,
            numero_prenotacao=response.get("numero_prenotacao", ""),
            tipo=TipoProtocolo(response.get("tipo", "registro")),
            matricula=response.get("matricula", ""),
            serventia=response.get("serventia", ""),
            status=StatusProtocolo(response.get("status", "em_analise")),
            prenotado_em=response.get("prenotado_em", ""),
            prazo_exigencia=response.get("prazo_exigencia"),
            exigencias=response.get("exigencias", []),
            registrado_em=response.get("registrado_em"),
            raw_response=response,
        )

    # =========================================================================
    # Penhora Online
    # =========================================================================

    async def consultar_penhora(
        self,
        cartorio_id: str,
        cns: str,
        matricula: str,
    ) -> list[PenhoraResult]:
        """Consultar penhoras de uma matrícula."""
        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/serventias/{cns}/matriculas/{matricula}/penhoras"
        )

        penhoras = []
        for item in response.get("penhoras", []):
            penhoras.append(
                PenhoraResult(
                    success=True,
                    codigo=item.get("codigo", ""),
                    tipo=TipoPenhora(item.get("tipo", "judicial")),
                    matricula=matricula,
                    serventia=item.get("serventia", ""),
                    valor=item.get("valor"),
                    processo=item.get("processo"),
                    vara=item.get("vara"),
                    credor=item.get("credor"),
                    devedor=item.get("devedor"),
                    registrado_em=item.get("registrado_em"),
                    baixado_em=item.get("baixado_em"),
                )
            )

        return penhoras

    async def registrar_penhora(
        self,
        cartorio_id: str,
        cns: str,
        matricula: str,
        tipo: TipoPenhora,
        processo: str,
        vara: str,
        credor: str,
        devedor: str,
        valor: float | None = None,
        observacao: str | None = None,
    ) -> PenhoraResult:
        """Registrar penhora em matrícula."""
        payload = {
            "tipo": tipo.value,
            "processo": processo,
            "vara": vara,
            "credor": credor,
            "devedor": devedor,
        }

        if valor:
            payload["valor"] = valor
        if observacao:
            payload["observacao"] = observacao

        response = await self._client.post(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/serventias/{cns}/matriculas/{matricula}/penhoras",
            json=payload,
        )

        return PenhoraResult(
            success=response.get("success", True),
            codigo=response.get("codigo", ""),
            tipo=tipo,
            matricula=matricula,
            serventia=response.get("serventia", ""),
            valor=valor,
            processo=processo,
            vara=vara,
            credor=credor,
            devedor=devedor,
            registrado_em=response.get("registrado_em"),
            raw_response=response,
        )

    # =========================================================================
    # CNIB
    # =========================================================================

    async def consultar_indisponibilidade(
        self,
        cartorio_id: str,
        cpf: str | None = None,
        cnpj: str | None = None,
    ) -> IndisponibilidadeResult:
        """Consultar indisponibilidade de bens na CNIB."""
        params = {}
        if cpf:
            params["cpf"] = cpf
        if cnpj:
            params["cnpj"] = cnpj

        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/cnib",
            params=params,
        )

        return IndisponibilidadeResult(
            success=response.get("success", True),
            cpf_cnpj=cpf or cnpj or "",
            nome=response.get("nome", ""),
            possui_indisponibilidade=response.get("possui_indisponibilidade", False),
            indisponibilidades=response.get("indisponibilidades", []),
            consultado_em=response.get("consultado_em", ""),
            raw_response=response,
        )

    # =========================================================================
    # Ofício Eletrônico
    # =========================================================================

    async def enviar_oficio(
        self,
        cartorio_id: str,
        cns_destino: str,
        assunto: str,
        conteudo: str,
        documentos: list[str] | None = None,
        urgente: bool = False,
    ) -> OficioResult:
        """Enviar ofício eletrônico."""
        payload = {
            "cns_destino": cns_destino,
            "assunto": assunto,
            "conteudo": conteudo,
            "urgente": urgente,
        }

        if documentos:
            payload["documentos"] = documentos

        response = await self._client.post(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/oficios",
            json=payload,
        )

        return OficioResult(
            success=response.get("success", True),
            oficio_id=response.get("oficio_id", ""),
            tipo=response.get("tipo", "enviado"),
            origem=response.get("origem", ""),
            destino=response.get("destino", ""),
            assunto=assunto,
            status=response.get("status", "enviado"),
            enviado_em=response.get("enviado_em", ""),
            raw_response=response,
        )

    async def consultar_oficio(
        self,
        cartorio_id: str,
        oficio_id: str,
    ) -> OficioResult:
        """Consultar ofício eletrônico."""
        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/oficios/{oficio_id}"
        )

        return OficioResult(
            success=response.get("success", True),
            oficio_id=oficio_id,
            tipo=response.get("tipo", ""),
            origem=response.get("origem", ""),
            destino=response.get("destino", ""),
            assunto=response.get("assunto", ""),
            status=response.get("status", ""),
            enviado_em=response.get("enviado_em", ""),
            respondido_em=response.get("respondido_em"),
            resposta=response.get("resposta"),
            raw_response=response,
        )

    async def listar_oficios(
        self,
        cartorio_id: str,
        tipo: str | None = None,
        status: str | None = None,
        pagina: int = 1,
        por_pagina: int = 50,
    ) -> dict[str, Any]:
        """Listar ofícios eletrônicos."""
        params = {
            "pagina": pagina,
            "por_pagina": por_pagina,
        }

        if tipo:
            params["tipo"] = tipo
        if status:
            params["status"] = status

        return await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/oficios",
            params=params,
        )
