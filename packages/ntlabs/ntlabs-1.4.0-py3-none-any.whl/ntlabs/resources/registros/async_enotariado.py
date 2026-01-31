"""
Neural LAB - e-Notariado Async Integration
Versão assíncrona da integração com e-Notariado.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from typing import TYPE_CHECKING, Any

from .enotariado import (
    CancelamentoResult,
    ConsultaFluxoResult,
    DownloadResult,
    FluxoAssinaturaResult,
    ListaFluxosResult,
    Participante,
    StatusFluxo,
    TipoDocumento,
    TipoParticipante,
    UploadResult,
)

if TYPE_CHECKING:
    from neural_lab.async_client import AsyncNeuralLabClient


class AsyncENotariadoResource:
    """
    Async e-Notariado Resource - Fluxo de Assinaturas.

    Versão assíncrona da integração com e-Notariado.

    Example:
        >>> async with AsyncNeuralLabClient(api_key="nl_merc_xxx") as client:
        ...     # Upload
        ...     upload = await client.enotariado.upload_documento(
        ...         cartorio_id="123",
        ...         arquivo=pdf_bytes,
        ...         nome_arquivo="escritura.pdf"
        ...     )
        ...
        ...     # Criar fluxo
        ...     fluxo = await client.enotariado.criar_fluxo(
        ...         cartorio_id="123",
        ...         upload_id=upload.upload_id,
        ...         tipo=TipoDocumento.ESCRITURA,
        ...         participantes=[...]
        ...     )
    """

    ENDPOINT_PREFIX = "/v1/enotariado"

    def __init__(self, client: "AsyncNeuralLabClient"):
        """Initialize async e-Notariado resource."""
        self._client = client

    # =========================================================================
    # Upload de Documentos
    # =========================================================================

    async def upload_documento(
        self,
        cartorio_id: str,
        arquivo: bytes,
        nome_arquivo: str,
        content_type: str = "application/pdf",
    ) -> UploadResult:
        """
        Upload assíncrono de documento PDF/A.

        Args:
            cartorio_id: ID do cartório.
            arquivo: Bytes do arquivo PDF/A.
            nome_arquivo: Nome do arquivo.
            content_type: Tipo MIME.

        Returns:
            UploadResult: Dados do upload.
        """
        response = await self._client.post(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/uploads",
            files={"arquivo": (nome_arquivo, arquivo, content_type)},
        )

        return UploadResult(
            success=response.get("success", True),
            upload_id=response.get("upload_id", ""),
            filename=response.get("filename", nome_arquivo),
            size_bytes=response.get("size_bytes", len(arquivo)),
            content_type=response.get("content_type", content_type),
            raw_response=response,
        )

    # =========================================================================
    # Fluxos de Assinaturas
    # =========================================================================

    async def criar_fluxo(
        self,
        cartorio_id: str,
        upload_id: str,
        tipo: TipoDocumento,
        participantes: list[Participante],
        titulo: str | None = None,
        descricao: str | None = None,
        assinatura_sequencial: bool = False,
        expira_em_dias: int = 30,
        notificar_participantes: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> FluxoAssinaturaResult:
        """
        Criar fluxo de assinaturas assíncrono.

        Args:
            cartorio_id: ID do cartório.
            upload_id: ID do documento.
            tipo: Tipo do documento.
            participantes: Lista de participantes.
            titulo: Título do documento.
            descricao: Descrição do ato.
            assinatura_sequencial: Assinaturas em ordem.
            expira_em_dias: Dias até expiração.
            notificar_participantes: Enviar notificações.
            metadata: Dados adicionais.

        Returns:
            FluxoAssinaturaResult: Dados do fluxo criado.
        """
        payload = {
            "upload_id": upload_id,
            "tipo_documento": tipo.value,
            "participantes": [p.to_dict() for p in participantes],
            "assinatura_sequencial": assinatura_sequencial,
            "expira_em_dias": expira_em_dias,
            "notificar_participantes": notificar_participantes,
        }

        if titulo:
            payload["titulo"] = titulo
        if descricao:
            payload["descricao"] = descricao
        if metadata:
            payload["metadata"] = metadata

        response = await self._client.post(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/fluxos",
            json=payload,
        )

        return FluxoAssinaturaResult(
            success=response.get("success", True),
            fluxo_id=response.get("fluxo_id", ""),
            mne=response.get("mne"),
            status=StatusFluxo(response.get("status", "Created")),
            tipo_documento=tipo,
            participantes=response.get("participantes", []),
            criado_em=response.get("criado_em", ""),
            expira_em=response.get("expira_em"),
            url_assinatura=response.get("url_assinatura"),
            raw_response=response,
        )

    async def consultar_fluxo(
        self,
        cartorio_id: str,
        fluxo_id: str,
    ) -> ConsultaFluxoResult:
        """
        Consultar status de um fluxo.

        Args:
            cartorio_id: ID do cartório.
            fluxo_id: ID do fluxo.

        Returns:
            ConsultaFluxoResult: Status detalhado.
        """
        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/fluxos/{fluxo_id}"
        )

        return ConsultaFluxoResult(
            success=response.get("success", True),
            fluxo_id=fluxo_id,
            mne=response.get("mne"),
            status=StatusFluxo(response.get("status", "Pending")),
            tipo_documento=TipoDocumento(response.get("tipo_documento", "Deed")),
            participantes=response.get("participantes", []),
            assinaturas_pendentes=response.get("assinaturas_pendentes", 0),
            assinaturas_concluidas=response.get("assinaturas_concluidas", 0),
            criado_em=response.get("criado_em", ""),
            atualizado_em=response.get("atualizado_em", ""),
            concluido_em=response.get("concluido_em"),
            raw_response=response,
        )

    async def listar_fluxos(
        self,
        cartorio_id: str,
        status: StatusFluxo | None = None,
        tipo: TipoDocumento | None = None,
        concluidos: bool | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        pagina: int = 1,
        por_pagina: int = 50,
    ) -> ListaFluxosResult:
        """
        Listar fluxos de assinaturas.

        Args:
            cartorio_id: ID do cartório.
            status: Filtrar por status.
            tipo: Filtrar por tipo.
            concluidos: Filtrar concluídos.
            data_inicio: Data inicial.
            data_fim: Data final.
            pagina: Página.
            por_pagina: Itens por página.

        Returns:
            ListaFluxosResult: Lista paginada.
        """
        params = {
            "pagina": pagina,
            "por_pagina": min(por_pagina, 100),
        }

        if status:
            params["status"] = status.value
        if tipo:
            params["tipo_documento"] = tipo.value
        if concluidos is not None:
            params["concluidos"] = concluidos
        if data_inicio:
            params["data_inicio"] = data_inicio
        if data_fim:
            params["data_fim"] = data_fim

        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/fluxos",
            params=params,
        )

        fluxos = []
        for item in response.get("fluxos", []):
            fluxos.append(
                ConsultaFluxoResult(
                    success=True,
                    fluxo_id=item.get("fluxo_id", ""),
                    mne=item.get("mne"),
                    status=StatusFluxo(item.get("status", "Pending")),
                    tipo_documento=TipoDocumento(item.get("tipo_documento", "Deed")),
                    participantes=item.get("participantes", []),
                    assinaturas_pendentes=item.get("assinaturas_pendentes", 0),
                    assinaturas_concluidas=item.get("assinaturas_concluidas", 0),
                    criado_em=item.get("criado_em", ""),
                    atualizado_em=item.get("atualizado_em", ""),
                    concluido_em=item.get("concluido_em"),
                )
            )

        return ListaFluxosResult(
            success=response.get("success", True),
            fluxos=fluxos,
            total=response.get("total", len(fluxos)),
            pagina=pagina,
            por_pagina=por_pagina,
            raw_response=response,
        )

    # =========================================================================
    # Download de Documentos Assinados
    # =========================================================================

    async def download_assinado(
        self,
        cartorio_id: str,
        fluxo_id: str,
        incluir_assinaturas: bool = True,
    ) -> DownloadResult:
        """
        Download do documento assinado.

        Args:
            cartorio_id: ID do cartório.
            fluxo_id: ID do fluxo.
            incluir_assinaturas: Incluir detalhes de assinaturas.

        Returns:
            DownloadResult: Documento assinado.
        """
        params = {"incluir_assinaturas": incluir_assinaturas}

        response = await self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/fluxos/{fluxo_id}/download",
            params=params,
        )

        return DownloadResult(
            success=response.get("success", True),
            fluxo_id=fluxo_id,
            mne=response.get("mne", ""),
            arquivo_bytes=response.get("arquivo_bytes", b""),
            nome_arquivo=response.get("nome_arquivo", f"{fluxo_id}.pdf"),
            content_type=response.get("content_type", "application/pdf"),
            hash_arquivo=response.get("hash_arquivo"),
            raw_response={k: v for k, v in response.items() if k != "arquivo_bytes"},
        )

    # =========================================================================
    # Gerenciamento de Fluxos
    # =========================================================================

    async def cancelar_fluxo(
        self,
        cartorio_id: str,
        fluxo_id: str,
        motivo: str,
    ) -> CancelamentoResult:
        """
        Cancelar um fluxo de assinaturas.

        Args:
            cartorio_id: ID do cartório.
            fluxo_id: ID do fluxo.
            motivo: Motivo do cancelamento.

        Returns:
            CancelamentoResult: Confirmação.
        """
        response = await self._client.post(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/fluxos/{fluxo_id}/cancelar",
            json={"motivo": motivo},
        )

        return CancelamentoResult(
            success=response.get("success", True),
            fluxo_id=fluxo_id,
            status=StatusFluxo.CANCELADO,
            motivo=motivo,
            cancelado_em=response.get("cancelado_em", ""),
            raw_response=response,
        )

    async def reenviar_notificacao(
        self,
        cartorio_id: str,
        fluxo_id: str,
        participante_cpf: str | None = None,
    ) -> dict[str, Any]:
        """
        Reenviar notificação de assinatura.

        Args:
            cartorio_id: ID do cartório.
            fluxo_id: ID do fluxo.
            participante_cpf: CPF específico (opcional).

        Returns:
            Dict com confirmação.
        """
        payload = {}
        if participante_cpf:
            payload["participante_cpf"] = participante_cpf

        return await self._client.post(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/fluxos/{fluxo_id}/reenviar",
            json=payload,
        )

    # =========================================================================
    # Atos Notariais Específicos
    # =========================================================================

    async def criar_escritura(
        self,
        cartorio_id: str,
        upload_id: str,
        outorgantes: list[Participante],
        outorgados: list[Participante],
        testemunhas: list[Participante] | None = None,
        titulo: str = "Escritura Pública",
        livro: str | None = None,
        folha: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FluxoAssinaturaResult:
        """
        Criar fluxo para escritura pública.

        Args:
            cartorio_id: ID do cartório.
            upload_id: ID do documento.
            outorgantes: Lista de outorgantes.
            outorgados: Lista de outorgados.
            testemunhas: Lista de testemunhas.
            titulo: Título da escritura.
            livro: Número do livro.
            folha: Número da folha.
            metadata: Dados adicionais.

        Returns:
            FluxoAssinaturaResult: Fluxo criado.
        """
        participantes = []

        for i, p in enumerate(outorgantes):
            p.tipo = TipoParticipante.OUTORGANTE
            p.ordem = i + 1
            participantes.append(p)

        ordem_base = len(outorgantes)
        for i, p in enumerate(outorgados):
            p.tipo = TipoParticipante.OUTORGADO
            p.ordem = ordem_base + i + 1
            participantes.append(p)

        if testemunhas:
            ordem_base = len(outorgantes) + len(outorgados)
            for i, p in enumerate(testemunhas):
                p.tipo = TipoParticipante.TESTEMUNHA
                p.ordem = ordem_base + i + 1
                participantes.append(p)

        meta = metadata or {}
        if livro:
            meta["livro"] = livro
        if folha:
            meta["folha"] = folha

        return await self.criar_fluxo(
            cartorio_id=cartorio_id,
            upload_id=upload_id,
            tipo=TipoDocumento.ESCRITURA,
            participantes=participantes,
            titulo=titulo,
            assinatura_sequencial=True,
            metadata=meta if meta else None,
        )

    async def criar_procuracao(
        self,
        cartorio_id: str,
        upload_id: str,
        outorgante: Participante,
        outorgados: list[Participante],
        titulo: str = "Procuração Pública",
        poderes: str | None = None,
        validade_dias: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FluxoAssinaturaResult:
        """
        Criar fluxo para procuração pública.

        Args:
            cartorio_id: ID do cartório.
            upload_id: ID do documento.
            outorgante: Mandante.
            outorgados: Mandatários.
            titulo: Título da procuração.
            poderes: Descrição dos poderes.
            validade_dias: Validade em dias.
            metadata: Dados adicionais.

        Returns:
            FluxoAssinaturaResult: Fluxo criado.
        """
        outorgante.tipo = TipoParticipante.OUTORGANTE
        outorgante.ordem = 1

        participantes = [outorgante]
        for i, p in enumerate(outorgados):
            p.tipo = TipoParticipante.OUTORGADO
            p.ordem = i + 2
            participantes.append(p)

        meta = metadata or {}
        if poderes:
            meta["poderes"] = poderes
        if validade_dias:
            meta["validade_dias"] = validade_dias

        return await self.criar_fluxo(
            cartorio_id=cartorio_id,
            upload_id=upload_id,
            tipo=TipoDocumento.PROCURACAO,
            participantes=participantes,
            titulo=titulo,
            metadata=meta if meta else None,
        )

    async def criar_ata_notarial(
        self,
        cartorio_id: str,
        upload_id: str,
        solicitante: Participante,
        testemunhas: list[Participante] | None = None,
        titulo: str = "Ata Notarial",
        objeto: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> FluxoAssinaturaResult:
        """
        Criar fluxo para ata notarial.

        Args:
            cartorio_id: ID do cartório.
            upload_id: ID do documento.
            solicitante: Quem solicitou.
            testemunhas: Testemunhas.
            titulo: Título da ata.
            objeto: Objeto da constatação.
            metadata: Dados adicionais.

        Returns:
            FluxoAssinaturaResult: Fluxo criado.
        """
        solicitante.tipo = TipoParticipante.OUTORGANTE
        solicitante.ordem = 1

        participantes = [solicitante]
        if testemunhas:
            for i, t in enumerate(testemunhas):
                t.tipo = TipoParticipante.TESTEMUNHA
                t.ordem = i + 2
                participantes.append(t)

        meta = metadata or {}
        if objeto:
            meta["objeto"] = objeto

        return await self.criar_fluxo(
            cartorio_id=cartorio_id,
            upload_id=upload_id,
            tipo=TipoDocumento.ATA_NOTARIAL,
            participantes=participantes,
            titulo=titulo,
            metadata=meta if meta else None,
        )
