"""
Neural LAB - ONR/SREI Integration
Integração com o Operador Nacional do Sistema de Registro Eletrônico de Imóveis.

RI Digital - Portal unificado de serviços dos Registros de Imóveis do Brasil.

Services:
    - Certidões (matrícula, negativa, Livro 3)
    - Visualização de matrículas
    - e-Protocolo
    - Penhora Online
    - Ofício Eletrônico
    - Central de Indisponibilidade de Bens (CNIB)

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from neural_lab.client import NeuralLabClient


class TipoCertidao(str, Enum):
    """Tipos de certidão de registro de imóveis."""

    MATRICULA = "matricula"  # Certidão de matrícula
    MATRICULA_ATUALIZADA = "matricula_atualizada"  # Com últimos 30 dias
    ONUS_ACOES = "onus_acoes"  # Certidão de ônus e ações
    NEGATIVA = "negativa"  # Certidão negativa de propriedade
    PROPRIEDADE = "propriedade"  # Certidão de propriedade
    LIVRO_3 = "livro_3"  # Certidão do Livro 3 (registro auxiliar)
    INTEIRO_TEOR = "inteiro_teor"  # Certidão de inteiro teor
    TRANSCRICAO = "transcricao"  # Certidão de transcrição


class StatusCertidao(str, Enum):
    """Status do pedido de certidão."""

    SOLICITADA = "solicitada"
    EM_PROCESSAMENTO = "em_processamento"
    DISPONIVEL = "disponivel"
    EXPIRADA = "expirada"
    CANCELADA = "cancelada"
    ERRO = "erro"


class TipoProtocolo(str, Enum):
    """Tipos de protocolo."""

    REGISTRO = "registro"  # Registro de documento
    AVERBACAO = "averbacao"  # Averbação
    CANCELAMENTO = "cancelamento"  # Cancelamento de registro
    RETIFICACAO = "retificacao"  # Retificação


class StatusProtocolo(str, Enum):
    """Status do protocolo."""

    PRENOTADO = "prenotado"
    EM_ANALISE = "em_analise"
    EXIGENCIA = "exigencia"
    REGISTRADO = "registrado"
    DEVOLVIDO = "devolvido"
    CANCELADO = "cancelado"


class TipoPenhora(str, Enum):
    """Tipos de penhora."""

    JUDICIAL = "judicial"
    ADMINISTRATIVA = "administrativa"
    ARRESTO = "arresto"
    SEQUESTRO = "sequestro"


class StatusIndisponibilidade(str, Enum):
    """Status de indisponibilidade de bens."""

    ATIVA = "ativa"
    CANCELADA = "cancelada"
    SUSPENSA = "suspensa"


@dataclass
class MatriculaInfo:
    """Informações de uma matrícula de imóvel."""

    matricula: str
    serventia: str
    cns: str  # Código Nacional da Serventia
    uf: str
    municipio: str
    area: float | None = None
    endereco: str | None = None
    proprietarios: list[dict[str, Any]] = field(default_factory=list)
    onus: list[dict[str, Any]] = field(default_factory=list)
    averbacoes: list[dict[str, Any]] = field(default_factory=list)
    atualizado_em: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CertidaoResult:
    """Resultado de pedido de certidão."""

    success: bool
    pedido_id: str
    tipo: TipoCertidao
    matricula: str
    serventia: str
    status: StatusCertidao
    solicitado_em: str
    validade: str | None = None
    url_download: str | None = None
    codigo_verificacao: str | None = None
    valor: float | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["tipo"] = self.tipo.value if isinstance(self.tipo, Enum) else self.tipo
        result["status"] = (
            self.status.value if isinstance(self.status, Enum) else self.status
        )
        return result


@dataclass
class BuscaPropriedadeResult:
    """Resultado de busca de propriedades."""

    success: bool
    cpf_cnpj: str
    total: int
    imoveis: list[dict[str, Any]]
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProtocoloResult:
    """Resultado de e-Protocolo."""

    success: bool
    protocolo: str
    numero_prenotacao: str
    tipo: TipoProtocolo
    matricula: str
    serventia: str
    status: StatusProtocolo
    prenotado_em: str
    prazo_exigencia: str | None = None
    exigencias: list[str] = field(default_factory=list)
    registrado_em: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["tipo"] = self.tipo.value if isinstance(self.tipo, Enum) else self.tipo
        result["status"] = (
            self.status.value if isinstance(self.status, Enum) else self.status
        )
        return result


@dataclass
class PenhoraResult:
    """Resultado de consulta/registro de penhora."""

    success: bool
    codigo: str
    tipo: TipoPenhora
    matricula: str
    serventia: str
    valor: float | None = None
    processo: str | None = None
    vara: str | None = None
    credor: str | None = None
    devedor: str | None = None
    registrado_em: str | None = None
    baixado_em: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result["tipo"] = self.tipo.value if isinstance(self.tipo, Enum) else self.tipo
        return result


@dataclass
class IndisponibilidadeResult:
    """Resultado de consulta na CNIB."""

    success: bool
    cpf_cnpj: str
    nome: str
    possui_indisponibilidade: bool
    indisponibilidades: list[dict[str, Any]]
    consultado_em: str
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class OficioResult:
    """Resultado de ofício eletrônico."""

    success: bool
    oficio_id: str
    tipo: str
    origem: str
    destino: str
    assunto: str
    status: str
    enviado_em: str
    respondido_em: str | None = None
    resposta: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ONRResource:
    """
    ONR/SREI Resource - Registro de Imóveis.

    Integração com o Operador Nacional do Sistema de Registro Eletrônico de Imóveis.

    Serviços:
        - Certidões de imóveis
        - Visualização de matrículas
        - e-Protocolo
        - Penhora Online
        - Ofício Eletrônico
        - CNIB (Central de Indisponibilidade de Bens)

    Requisitos:
        - Credenciamento junto ao ONR
        - Certificado digital ICP-Brasil
        - Créditos no RI Digital

    Regulamentação: Provimento CNJ 89/2019, 124/2021

    Example:
        >>> client = NeuralLabClient(api_key="nl_merc_xxx")
        >>>
        >>> # Consultar matrícula
        >>> matricula = client.onr.consultar_matricula(
        ...     cartorio_id="123",
        ...     cns="12345",
        ...     matricula="1234"
        ... )
        >>>
        >>> # Solicitar certidão
        >>> certidao = client.onr.solicitar_certidao(
        ...     cartorio_id="123",
        ...     cns_destino="12345",
        ...     matricula="1234",
        ...     tipo=TipoCertidao.MATRICULA_ATUALIZADA
        ... )
        >>>
        >>> # Buscar propriedades por CPF
        >>> props = client.onr.buscar_propriedades("123", cpf="123.456.789-00")
    """

    ENDPOINT_PREFIX = "/v1/onr"

    def __init__(self, client: "NeuralLabClient"):
        """Initialize ONR resource."""
        self._client = client

    # =========================================================================
    # Matrículas
    # =========================================================================

    def consultar_matricula(
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
            cns: CNS da serventia (Código Nacional da Serventia).
            matricula: Número da matrícula.
            incluir_historico: Incluir histórico de alterações.

        Returns:
            MatriculaInfo: Dados da matrícula.

        Example:
            >>> info = client.onr.consultar_matricula(
            ...     cartorio_id="123",
            ...     cns="12345",
            ...     matricula="1234"
            ... )
            >>> print(f"Proprietários: {info.proprietarios}")
        """
        params = {"incluir_historico": incluir_historico}

        response = self._client.get(
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

    def visualizar_matricula(
        self,
        cartorio_id: str,
        cns: str,
        matricula: str,
    ) -> dict[str, Any]:
        """
        Visualizar matrícula (versão resumida gratuita).

        A visualização mostra dados básicos sem valor de certidão.

        Args:
            cartorio_id: ID do cartório.
            cns: CNS da serventia.
            matricula: Número da matrícula.

        Returns:
            Dict com dados básicos da matrícula.
        """
        return self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/serventias/{cns}/matriculas/{matricula}/visualizar"
        )

    # =========================================================================
    # Certidões
    # =========================================================================

    def solicitar_certidao(
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
            cns_destino: CNS da serventia onde está a matrícula.
            matricula: Número da matrícula.
            tipo: Tipo de certidão desejada.
            finalidade: Finalidade da certidão (opcional).
            urgente: Solicitar emissão urgente (custo adicional).

        Returns:
            CertidaoResult: Dados do pedido.

        Example:
            >>> certidao = client.onr.solicitar_certidao(
            ...     cartorio_id="123",
            ...     cns_destino="12345",
            ...     matricula="1234",
            ...     tipo=TipoCertidao.ONUS_ACOES
            ... )
        """
        payload = {
            "matricula": matricula,
            "tipo": tipo.value,
            "urgente": urgente,
        }

        if finalidade:
            payload["finalidade"] = finalidade

        response = self._client.post(
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

    def consultar_certidao(
        self,
        cartorio_id: str,
        pedido_id: str,
    ) -> CertidaoResult:
        """
        Consultar status de pedido de certidão.

        Args:
            cartorio_id: ID do cartório.
            pedido_id: ID do pedido.

        Returns:
            CertidaoResult: Status atualizado.
        """
        response = self._client.get(
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

    def download_certidao(
        self,
        cartorio_id: str,
        pedido_id: str,
    ) -> bytes:
        """
        Download do PDF da certidão.

        Args:
            cartorio_id: ID do cartório.
            pedido_id: ID do pedido.

        Returns:
            bytes: Conteúdo do PDF.
        """
        response = self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/certidoes/{pedido_id}/download"
        )
        return response.get("arquivo_bytes", b"")

    # =========================================================================
    # Busca de Propriedades
    # =========================================================================

    def buscar_propriedades(
        self,
        cartorio_id: str,
        cpf: str | None = None,
        cnpj: str | None = None,
        uf: str | None = None,
    ) -> BuscaPropriedadeResult:
        """
        Buscar propriedades por CPF ou CNPJ.

        Retorna lista de imóveis registrados em nome da pessoa/empresa.

        Args:
            cartorio_id: ID do cartório solicitante.
            cpf: CPF do proprietário.
            cnpj: CNPJ do proprietário.
            uf: Filtrar por UF (opcional).

        Returns:
            BuscaPropriedadeResult: Lista de imóveis.

        Example:
            >>> props = client.onr.buscar_propriedades(
            ...     cartorio_id="123",
            ...     cpf="123.456.789-00"
            ... )
            >>> print(f"Imóveis encontrados: {props.total}")
        """
        params = {}
        if cpf:
            params["cpf"] = cpf
        if cnpj:
            params["cnpj"] = cnpj
        if uf:
            params["uf"] = uf

        response = self._client.get(
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

    def criar_protocolo(
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
        """
        Criar e-Protocolo (prenotação eletrônica).

        Args:
            cartorio_id: ID do cartório solicitante.
            cns_destino: CNS do RI destino.
            matricula: Número da matrícula.
            tipo: Tipo de protocolo.
            documento_id: ID do documento (do e-Notariado ou upload).
            titulo: Título do protocolo.
            descricao: Descrição adicional.
            partes: Lista de partes envolvidas.

        Returns:
            ProtocoloResult: Dados da prenotação.

        Example:
            >>> protocolo = client.onr.criar_protocolo(
            ...     cartorio_id="123",
            ...     cns_destino="12345",
            ...     matricula="1234",
            ...     tipo=TipoProtocolo.REGISTRO,
            ...     documento_id="doc-abc",
            ...     titulo="Escritura de Compra e Venda"
            ... )
        """
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

        response = self._client.post(
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

    def consultar_protocolo(
        self,
        cartorio_id: str,
        protocolo: str,
    ) -> ProtocoloResult:
        """
        Consultar status de protocolo.

        Args:
            cartorio_id: ID do cartório.
            protocolo: Número do protocolo.

        Returns:
            ProtocoloResult: Status atualizado.
        """
        response = self._client.get(
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

    def responder_exigencia(
        self,
        cartorio_id: str,
        protocolo: str,
        documento_id: str,
        observacao: str | None = None,
    ) -> ProtocoloResult:
        """
        Responder exigência de protocolo.

        Args:
            cartorio_id: ID do cartório.
            protocolo: Número do protocolo.
            documento_id: ID do documento com a resposta.
            observacao: Observação adicional.

        Returns:
            ProtocoloResult: Status atualizado.
        """
        payload = {"documento_id": documento_id}
        if observacao:
            payload["observacao"] = observacao

        response = self._client.post(
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

    def consultar_penhora(
        self,
        cartorio_id: str,
        cns: str,
        matricula: str,
    ) -> list[PenhoraResult]:
        """
        Consultar penhoras de uma matrícula.

        Args:
            cartorio_id: ID do cartório.
            cns: CNS da serventia.
            matricula: Número da matrícula.

        Returns:
            List[PenhoraResult]: Lista de penhoras ativas.
        """
        response = self._client.get(
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

    def registrar_penhora(
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
        """
        Registrar penhora em matrícula.

        Args:
            cartorio_id: ID do cartório.
            cns: CNS da serventia.
            matricula: Número da matrícula.
            tipo: Tipo de penhora.
            processo: Número do processo.
            vara: Vara de origem.
            credor: Nome do credor.
            devedor: Nome do devedor.
            valor: Valor da penhora.
            observacao: Observação adicional.

        Returns:
            PenhoraResult: Dados da penhora registrada.
        """
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

        response = self._client.post(
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
    # CNIB - Central de Indisponibilidade de Bens
    # =========================================================================

    def consultar_indisponibilidade(
        self,
        cartorio_id: str,
        cpf: str | None = None,
        cnpj: str | None = None,
    ) -> IndisponibilidadeResult:
        """
        Consultar indisponibilidade de bens na CNIB.

        Args:
            cartorio_id: ID do cartório.
            cpf: CPF da pessoa.
            cnpj: CNPJ da empresa.

        Returns:
            IndisponibilidadeResult: Dados de indisponibilidade.

        Example:
            >>> result = client.onr.consultar_indisponibilidade(
            ...     cartorio_id="123",
            ...     cpf="123.456.789-00"
            ... )
            >>> if result.possui_indisponibilidade:
            ...     print("Existem ordens de indisponibilidade!")
        """
        params = {}
        if cpf:
            params["cpf"] = cpf
        if cnpj:
            params["cnpj"] = cnpj

        response = self._client.get(
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

    def enviar_oficio(
        self,
        cartorio_id: str,
        cns_destino: str,
        assunto: str,
        conteudo: str,
        documentos: list[str] | None = None,
        urgente: bool = False,
    ) -> OficioResult:
        """
        Enviar ofício eletrônico.

        Args:
            cartorio_id: ID do cartório remetente.
            cns_destino: CNS do cartório destinatário.
            assunto: Assunto do ofício.
            conteudo: Conteúdo do ofício.
            documentos: Lista de IDs de documentos anexos.
            urgente: Marcar como urgente.

        Returns:
            OficioResult: Dados do ofício enviado.
        """
        payload = {
            "cns_destino": cns_destino,
            "assunto": assunto,
            "conteudo": conteudo,
            "urgente": urgente,
        }

        if documentos:
            payload["documentos"] = documentos

        response = self._client.post(
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

    def consultar_oficio(
        self,
        cartorio_id: str,
        oficio_id: str,
    ) -> OficioResult:
        """
        Consultar ofício eletrônico.

        Args:
            cartorio_id: ID do cartório.
            oficio_id: ID do ofício.

        Returns:
            OficioResult: Dados do ofício.
        """
        response = self._client.get(
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

    def listar_oficios(
        self,
        cartorio_id: str,
        tipo: str | None = None,
        status: str | None = None,
        pagina: int = 1,
        por_pagina: int = 50,
    ) -> dict[str, Any]:
        """
        Listar ofícios eletrônicos.

        Args:
            cartorio_id: ID do cartório.
            tipo: Filtrar por tipo (enviado, recebido).
            status: Filtrar por status.
            pagina: Página.
            por_pagina: Itens por página.

        Returns:
            Dict com lista de ofícios.
        """
        params = {
            "pagina": pagina,
            "por_pagina": por_pagina,
        }

        if tipo:
            params["tipo"] = tipo
        if status:
            params["status"] = status

        return self._client.get(
            f"{self.ENDPOINT_PREFIX}/cartorios/{cartorio_id}/oficios",
            params=params,
        )
