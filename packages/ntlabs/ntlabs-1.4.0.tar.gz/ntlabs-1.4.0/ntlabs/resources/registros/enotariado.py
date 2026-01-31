"""
Neural LAB - e-Notariado Integration
Integração com a plataforma e-Notariado do CNB (Colégio Notarial do Brasil).

Fluxo de Assinaturas para atos notariais eletrônicos conforme Provimento CNJ nº 149/2023.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from neural_lab.client import NeuralLabClient


class TipoDocumento(str, Enum):
    """Tipos de documentos no e-Notariado."""

    ESCRITURA = "Deed"  # Escritura pública
    PROCURACAO = "PowerOfAttorney"  # Procuração
    ATA_NOTARIAL = "NotarialMinutes"  # Ata notarial
    TESTAMENTO = "Will"  # Testamento
    SUBSTABELECIMENTO = "SubPowerOfAttorney"  # Substabelecimento
    REVOGACAO = "Revocation"  # Revogação de procuração
    APOSTILA = "Apostille"  # Apostilamento


class TipoAssinatura(str, Enum):
    """Tipos de assinatura suportados."""

    ICP_BRASIL = "IcpBrasil"  # Certificado ICP-Brasil A3
    NOTARIZADO = "Notarized"  # Certificado Notarizado e-Notariado
    VIDEOCONFERENCIA = "VideoConference"  # Assinatura por videoconferência
    PRESENCIAL = "InPerson"  # Assinatura presencial


class StatusFluxo(str, Enum):
    """Status do fluxo de assinaturas."""

    CRIADO = "Created"  # Fluxo criado
    AGUARDANDO = "Pending"  # Aguardando assinaturas
    EM_ANDAMENTO = "InProgress"  # Em andamento
    CONCLUIDO = "Concluded"  # Todas assinaturas concluídas
    CANCELADO = "Canceled"  # Fluxo cancelado
    EXPIRADO = "Expired"  # Fluxo expirado


class TipoParticipante(str, Enum):
    """Tipos de participantes no fluxo."""

    OUTORGANTE = "Grantor"  # Quem concede (vendedor, mandante)
    OUTORGADO = "Grantee"  # Quem recebe (comprador, mandatário)
    TESTEMUNHA = "Witness"  # Testemunha
    TABELIAO = "Notary"  # Tabelião
    PREPOSTO = "Clerk"  # Preposto do cartório
    INTERVENIENTE = "Intervening"  # Interveniente


@dataclass
class Participante:
    """Participante de um fluxo de assinaturas."""

    nome: str
    cpf: str
    email: str
    tipo: TipoParticipante
    tipo_assinatura: TipoAssinatura = TipoAssinatura.NOTARIZADO
    telefone: str | None = None
    ordem: int = 1  # Ordem de assinatura (para fluxos sequenciais)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            k: v.value if isinstance(v, Enum) else v
            for k, v in asdict(self).items()
            if v is not None
        }


@dataclass
class UploadResult:
    """Resultado do upload de documento."""

    success: bool
    upload_id: str
    filename: str
    size_bytes: int
    content_type: str
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class FluxoAssinaturaResult:
    """Resultado da criação de um fluxo de assinaturas."""

    success: bool
    fluxo_id: str
    mne: str | None  # Matrícula Notarial Eletrônica
    status: StatusFluxo
    tipo_documento: TipoDocumento
    participantes: list[dict[str, Any]]
    criado_em: str
    expira_em: str | None = None
    url_assinatura: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["status"] = (
            self.status.value if isinstance(self.status, Enum) else self.status
        )
        result["tipo_documento"] = (
            self.tipo_documento.value
            if isinstance(self.tipo_documento, Enum)
            else self.tipo_documento
        )
        return result


@dataclass
class ConsultaFluxoResult:
    """Resultado da consulta de um fluxo."""

    success: bool
    fluxo_id: str
    mne: str | None
    status: StatusFluxo
    tipo_documento: TipoDocumento
    participantes: list[dict[str, Any]]
    assinaturas_pendentes: int
    assinaturas_concluidas: int
    criado_em: str
    atualizado_em: str
    concluido_em: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["status"] = (
            self.status.value if isinstance(self.status, Enum) else self.status
        )
        result["tipo_documento"] = (
            self.tipo_documento.value
            if isinstance(self.tipo_documento, Enum)
            else self.tipo_documento
        )
        return result


@dataclass
class ListaFluxosResult:
    """Resultado da listagem de fluxos."""

    success: bool
    fluxos: list[ConsultaFluxoResult]
    total: int
    pagina: int
    por_pagina: int
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["fluxos"] = [
            f.to_dict() if hasattr(f, "to_dict") else f for f in self.fluxos
        ]
        return result


@dataclass
class DownloadResult:
    """Resultado do download de documento assinado."""

    success: bool
    fluxo_id: str
    mne: str
    arquivo_bytes: bytes
    nome_arquivo: str
    content_type: str
    hash_arquivo: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (without bytes)."""
        result = {k: v for k, v in asdict(self).items() if k != "arquivo_bytes"}
        result["tamanho_bytes"] = len(self.arquivo_bytes)
        return result


@dataclass
class CancelamentoResult:
    """Resultado do cancelamento de um fluxo."""

    success: bool
    fluxo_id: str
    status: StatusFluxo
    motivo: str
    cancelado_em: str
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["status"] = (
            self.status.value if isinstance(self.status, Enum) else self.status
        )
        return result


class ENotariadoResource:
    """
    e-Notariado Resource - Fluxo de Assinaturas.

    Integração com a plataforma e-Notariado para atos notariais eletrônicos.

    Funcionalidades:
        - Upload de documentos PDF/A
        - Criação de fluxos de assinaturas
        - Consulta de status
        - Download de documentos assinados
        - Cancelamento de fluxos

    Requisitos:
        - API-KEY do cartório (gerada pelo Tabelião no e-Notariado)
        - Certificado digital ICP-Brasil ou Notarizado
        - Acordo de Cooperação Técnica (ACT) com CNB-CF

    Provimento: CNJ nº 149/2023

    Example:
        >>> client = NeuralLabClient(api_key="nl_merc_xxx")
        >>>
        >>> # Upload do documento
        >>> upload = client.enotariado.upload_documento(
        ...     cartorio_id="123",
        ...     arquivo=pdf_bytes,
        ...     nome_arquivo="escritura_venda.pdf"
        ... )
        >>>
        >>> # Criar fluxo de assinaturas
        >>> fluxo = client.enotariado.criar_fluxo(
        ...     cartorio_id="123",
        ...     upload_id=upload.upload_id,
        ...     tipo=TipoDocumento.ESCRITURA,
        ...     participantes=[
        ...         Participante(nome="João", cpf="123.456.789-00", email="joao@email.com", tipo=TipoParticipante.OUTORGANTE),
        ...         Participante(nome="Maria", cpf="987.654.321-00", email="maria@email.com", tipo=TipoParticipante.OUTORGADO),
        ...     ]
        ... )
        >>>
        >>> # Consultar status
        >>> status = client.enotariado.consultar_fluxo("123", fluxo.fluxo_id)
        >>>
        >>> # Download após conclusão
        >>> if status.status == StatusFluxo.CONCLUIDO:
        ...     doc = client.enotariado.download_assinado("123", fluxo.fluxo_id)
    """

    ENDPOINT_PREFIX = "/v1/enotariado"

    def __init__(self, client: "NeuralLabClient"):
        """Initialize e-Notariado resource."""
        self._client = client

    # =========================================================================
    # Upload de Documentos
    # =========================================================================

    def upload_documento(
        self,
        cartorio_id: str,
        arquivo: bytes,
        nome_arquivo: str,
        content_type: str = "application/pdf",
    ) -> UploadResult:
        """
        Upload de documento PDF/A para o e-Notariado.

        O documento deve estar no formato PDF/A (arquivamento de longo prazo).

        Args:
            cartorio_id: ID do cartório no sistema.
            arquivo: Bytes do arquivo PDF/A.
            nome_arquivo: Nome do arquivo.
            content_type: Tipo MIME (default: application/pdf).

        Returns:
            UploadResult: Dados do upload incluindo upload_id.

        Example:
            >>> with open("escritura.pdf", "rb") as f:
            ...     pdf_bytes = f.read()
            >>> upload = client.enotariado.upload_documento(
            ...     cartorio_id="123",
            ...     arquivo=pdf_bytes,
            ...     nome_arquivo="escritura_venda.pdf"
            ... )
            >>> print(upload.upload_id)
        """
        response = self._client.post(
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

    def criar_fluxo(
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
        Criar fluxo de assinaturas no e-Notariado.

        Args:
            cartorio_id: ID do cartório.
            upload_id: ID do documento (retornado pelo upload).
            tipo: Tipo do documento (escritura, procuração, etc).
            participantes: Lista de participantes do fluxo.
            titulo: Título do documento (opcional).
            descricao: Descrição do ato (opcional).
            assinatura_sequencial: Se True, participantes assinam em ordem.
            expira_em_dias: Dias até expiração (default: 30).
            notificar_participantes: Enviar notificação aos participantes.
            metadata: Dados adicionais do sistema do cartório.

        Returns:
            FluxoAssinaturaResult: Dados do fluxo criado.

        Example:
            >>> fluxo = client.enotariado.criar_fluxo(
            ...     cartorio_id="123",
            ...     upload_id="abc-123",
            ...     tipo=TipoDocumento.ESCRITURA,
            ...     participantes=[
            ...         Participante(
            ...             nome="João Silva",
            ...             cpf="123.456.789-00",
            ...             email="joao@email.com",
            ...             tipo=TipoParticipante.OUTORGANTE
            ...         ),
            ...     ],
            ...     titulo="Escritura de Compra e Venda"
            ... )
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

        response = self._client.post(
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

    def consultar_fluxo(
        self,
        cartorio_id: str,
        fluxo_id: str,
    ) -> ConsultaFluxoResult:
        """
        Consultar status de um fluxo de assinaturas.

        Args:
            cartorio_id: ID do cartório.
            fluxo_id: ID do fluxo.

        Returns:
            ConsultaFluxoResult: Status detalhado do fluxo.

        Example:
            >>> status = client.enotariado.consultar_fluxo("123", "fluxo-abc")
            >>> print(f"Status: {status.status}")
            >>> print(f"Pendentes: {status.assinaturas_pendentes}")
        """
        response = self._client.get(
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

    def listar_fluxos(
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
        Listar fluxos de assinaturas do cartório.

        Args:
            cartorio_id: ID do cartório.
            status: Filtrar por status.
            tipo: Filtrar por tipo de documento.
            concluidos: True para apenas concluídos, False para pendentes.
            data_inicio: Data inicial (YYYY-MM-DD).
            data_fim: Data final (YYYY-MM-DD).
            pagina: Página (default: 1).
            por_pagina: Itens por página (default: 50, max: 100).

        Returns:
            ListaFluxosResult: Lista paginada de fluxos.

        Example:
            >>> # Listar fluxos pendentes
            >>> fluxos = client.enotariado.listar_fluxos(
            ...     cartorio_id="123",
            ...     concluidos=False
            ... )
            >>> for f in fluxos.fluxos:
            ...     print(f"{f.fluxo_id}: {f.status}")
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

        response = self._client.get(
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

    def download_assinado(
        self,
        cartorio_id: str,
        fluxo_id: str,
        incluir_assinaturas: bool = True,
    ) -> DownloadResult:
        """
        Download do documento assinado.

        O documento só estará disponível após todas as assinaturas.

        Args:
            cartorio_id: ID do cartório.
            fluxo_id: ID do fluxo.
            incluir_assinaturas: Incluir página com detalhes das assinaturas.

        Returns:
            DownloadResult: Documento assinado em bytes.

        Example:
            >>> doc = client.enotariado.download_assinado("123", "fluxo-abc")
            >>> with open("escritura_assinada.pdf", "wb") as f:
            ...     f.write(doc.arquivo_bytes)
        """
        params = {"incluir_assinaturas": incluir_assinaturas}

        response = self._client.get(
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

    def cancelar_fluxo(
        self,
        cartorio_id: str,
        fluxo_id: str,
        motivo: str,
    ) -> CancelamentoResult:
        """
        Cancelar um fluxo de assinaturas.

        O fluxo só pode ser cancelado antes da conclusão.

        Args:
            cartorio_id: ID do cartório.
            fluxo_id: ID do fluxo.
            motivo: Motivo do cancelamento.

        Returns:
            CancelamentoResult: Confirmação do cancelamento.

        Example:
            >>> result = client.enotariado.cancelar_fluxo(
            ...     cartorio_id="123",
            ...     fluxo_id="fluxo-abc",
            ...     motivo="Erro nos dados do outorgante"
            ... )
        """
        response = self._client.post(
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

    def reenviar_notificacao(
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
            participante_cpf: CPF do participante específico (opcional).
                             Se não informado, reenvia para todos pendentes.

        Returns:
            Dict com confirmação do reenvio.

        Example:
            >>> client.enotariado.reenviar_notificacao(
            ...     cartorio_id="123",
            ...     fluxo_id="fluxo-abc",
            ...     participante_cpf="123.456.789-00"
            ... )
        """
        payload = {}
        if participante_cpf:
            payload["participante_cpf"] = participante_cpf

        return self._client.post(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/fluxos/{fluxo_id}/reenviar",
            json=payload,
        )

    # =========================================================================
    # Atos Notariais Específicos
    # =========================================================================

    def criar_escritura(
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

        Atalho para criar_fluxo com tipo ESCRITURA e participantes organizados.

        Args:
            cartorio_id: ID do cartório.
            upload_id: ID do documento PDF/A.
            outorgantes: Lista de outorgantes (vendedores, cedentes, etc).
            outorgados: Lista de outorgados (compradores, cessionários, etc).
            testemunhas: Lista de testemunhas (opcional).
            titulo: Título da escritura.
            livro: Número do livro (opcional).
            folha: Número da folha (opcional).
            metadata: Dados adicionais.

        Returns:
            FluxoAssinaturaResult: Fluxo criado.

        Example:
            >>> escritura = client.enotariado.criar_escritura(
            ...     cartorio_id="123",
            ...     upload_id="abc-123",
            ...     outorgantes=[Participante(...)],
            ...     outorgados=[Participante(...)],
            ...     titulo="Escritura de Compra e Venda - Imóvel Matrícula 12345"
            ... )
        """
        participantes = []

        # Outorgantes
        for i, p in enumerate(outorgantes):
            p.tipo = TipoParticipante.OUTORGANTE
            p.ordem = i + 1
            participantes.append(p)

        # Outorgados
        ordem_base = len(outorgantes)
        for i, p in enumerate(outorgados):
            p.tipo = TipoParticipante.OUTORGADO
            p.ordem = ordem_base + i + 1
            participantes.append(p)

        # Testemunhas
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

        return self.criar_fluxo(
            cartorio_id=cartorio_id,
            upload_id=upload_id,
            tipo=TipoDocumento.ESCRITURA,
            participantes=participantes,
            titulo=titulo,
            assinatura_sequencial=True,  # Escrituras geralmente são sequenciais
            metadata=meta if meta else None,
        )

    def criar_procuracao(
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
            upload_id: ID do documento PDF/A.
            outorgante: Mandante (quem concede poderes).
            outorgados: Mandatários (quem recebe poderes).
            titulo: Título da procuração.
            poderes: Descrição dos poderes concedidos.
            validade_dias: Validade em dias (se procuração com prazo).
            metadata: Dados adicionais.

        Returns:
            FluxoAssinaturaResult: Fluxo criado.

        Example:
            >>> procuracao = client.enotariado.criar_procuracao(
            ...     cartorio_id="123",
            ...     upload_id="abc-123",
            ...     outorgante=Participante(nome="João", ...),
            ...     outorgados=[Participante(nome="Maria", ...)],
            ...     poderes="Poderes amplos para venda de imóvel"
            ... )
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

        return self.criar_fluxo(
            cartorio_id=cartorio_id,
            upload_id=upload_id,
            tipo=TipoDocumento.PROCURACAO,
            participantes=participantes,
            titulo=titulo,
            metadata=meta if meta else None,
        )

    def criar_ata_notarial(
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
            upload_id: ID do documento PDF/A.
            solicitante: Quem solicitou a ata.
            testemunhas: Testemunhas (opcional).
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

        return self.criar_fluxo(
            cartorio_id=cartorio_id,
            upload_id=upload_id,
            tipo=TipoDocumento.ATA_NOTARIAL,
            participantes=participantes,
            titulo=titulo,
            metadata=meta if meta else None,
        )
