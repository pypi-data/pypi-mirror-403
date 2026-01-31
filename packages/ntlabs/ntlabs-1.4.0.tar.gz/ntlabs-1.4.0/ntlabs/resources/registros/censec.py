"""
Neural LAB - AI Solutions Platform
CENSEC Resource - Central Notarial de Serviços Eletrônicos Compartilhados.

Integração com a CENSEC (CNB-CF) para:
- RCTO: Registro Central de Testamentos Online
- CESDI: Escrituras de Separações, Divórcios e Inventários
- CEP: Central de Escrituras e Procurações
- CENPROC: Central de Procurações
- CNSIP: Central Nacional de Sinal Público

Provimento CNJ nº 18/2012 e atualizações.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, BinaryIO

from ...base import DataclassMixin


class TipoTestamento(str, Enum):
    """Tipos de testamento."""

    PUBLICO = "publico"
    CERRADO = "cerrado"
    PARTICULAR = "particular"
    MARITIMO = "maritimo"
    AERONAUTICO = "aeronautico"
    MILITAR = "militar"


class TipoAtoNotarial(str, Enum):
    """Tipos de atos notariais."""

    ESCRITURA_PUBLICA = "escritura_publica"
    PROCURACAO = "procuracao"
    SUBSTABELECIMENTO = "substabelecimento"
    REVOGACAO = "revogacao"
    TESTAMENTO = "testamento"
    ATA_NOTARIAL = "ata_notarial"
    INVENTARIO = "inventario"
    DIVORCIO = "divorcio"
    SEPARACAO = "separacao"
    UNIAO_ESTAVEL = "uniao_estavel"
    DISSOLUCAO_UNIAO = "dissolucao_uniao"


class StatusAto(str, Enum):
    """Status de um ato notarial."""

    VIGENTE = "vigente"
    REVOGADO = "revogado"
    CANCELADO = "cancelado"
    SUBSTITUIDO = "substituido"


class TipoProcuracao(str, Enum):
    """Tipos de procuração."""

    AD_JUDICIA = "ad_judicia"
    AD_NEGOTIA = "ad_negotia"
    AD_JUDICIA_ET_EXTRA = "ad_judicia_et_extra"
    PLENOS_PODERES = "plenos_poderes"
    ESPECIFICA = "especifica"


@dataclass
class TestamentoResult(DataclassMixin):
    """Resultado de consulta de testamento no RCTO."""

    id: str
    tipo: TipoTestamento
    testador_nome: str
    testador_cpf: str | None
    data_lavratura: str
    livro: str
    folha: str
    cartorio_nome: str
    cartorio_cns: str
    municipio: str
    uf: str
    status: StatusAto
    tem_codicilo: bool
    data_revogacao: str | None = None
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class BuscaTestamentoResult(DataclassMixin):
    """Resultado de busca de testamentos."""

    total: int
    testamentos: list[dict[str, Any]]
    pagina: int
    por_pagina: int
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class ProcuracaoResult(DataclassMixin):
    """Resultado de consulta de procuração no CENPROC/CEP."""

    id: str
    tipo: TipoProcuracao
    outorgante: dict[str, Any]
    outorgado: dict[str, Any]
    poderes: list[str]
    data_lavratura: str
    data_validade: str | None
    livro: str
    folha: str
    cartorio_nome: str
    cartorio_cns: str
    municipio: str
    uf: str
    status: StatusAto
    substabelecimentos: list[dict[str, Any]]
    data_revogacao: str | None = None
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class BuscaProcuracaoResult(DataclassMixin):
    """Resultado de busca de procurações."""

    total: int
    procuracoes: list[dict[str, Any]]
    pagina: int
    por_pagina: int
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class EscrituraResult(DataclassMixin):
    """Resultado de consulta de escritura no CEP/CESDI."""

    id: str
    tipo: TipoAtoNotarial
    partes: list[dict[str, Any]]
    objeto: str
    valor: float | None
    data_lavratura: str
    livro: str
    folha: str
    cartorio_nome: str
    cartorio_cns: str
    municipio: str
    uf: str
    status: StatusAto
    imovel: dict[str, Any] | None = None
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class BuscaEscrituraResult(DataclassMixin):
    """Resultado de busca de escrituras."""

    total: int
    escrituras: list[dict[str, Any]]
    pagina: int
    por_pagina: int
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class SinalPublicoResult(DataclassMixin):
    """Informações de sinal público no CNSIP."""

    id: str
    notario_nome: str
    notario_cpf: str
    cartorio_nome: str
    cartorio_cns: str
    uf: str
    sinal_base64: str
    data_cadastro: str
    status: str
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class RegistroAtoResult(DataclassMixin):
    """Resultado de registro de ato no CENSEC."""

    id: str
    protocolo: str
    tipo: TipoAtoNotarial
    status: str
    data_registro: str
    mensagem: str
    latency_ms: int = 0
    cost_brl: float = 0.0


class CENSECResource:
    """
    CENSEC - Central Notarial de Serviços Eletrônicos Compartilhados.

    Integração com a plataforma do CNB-CF para consulta e registro de:
    - Testamentos (RCTO)
    - Procurações (CENPROC)
    - Escrituras (CEP)
    - Separações, Divórcios, Inventários (CESDI)
    - Sinais Públicos (CNSIP)

    Requer certificado digital ICP-Brasil do cartório.

    Usage:
        # Consultar testamento por CPF do testador
        testamentos = client.censec.buscar_testamentos(
            cartorio_id="uuid",
            cpf_testador="123.456.789-00"
        )

        # Consultar procuração
        procuracao = client.censec.consultar_procuracao(
            cartorio_id="uuid",
            codigo="ABC123"
        )

        # Registrar novo testamento
        result = client.censec.registrar_testamento(
            cartorio_id="uuid",
            tipo="publico",
            testador={...},
            dados={...}
        )

        # Verificar se pessoa tem testamento
        existe = client.censec.existe_testamento(
            cartorio_id="uuid",
            cpf="123.456.789-00"
        )
    """

    def __init__(self, client):
        self._client = client

    # =========================================================================
    # RCTO - Registro Central de Testamentos Online
    # =========================================================================

    def buscar_testamentos(
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
        """
        Buscar testamentos no RCTO.

        Args:
            cartorio_id: UUID do cartório (para autenticação)
            cpf_testador: CPF do testador
            nome_testador: Nome do testador
            data_inicio: Data inicial (YYYY-MM-DD)
            data_fim: Data final (YYYY-MM-DD)
            tipo: Tipo de testamento
            uf: UF do cartório
            pagina: Número da página
            por_pagina: Resultados por página

        Returns:
            BuscaTestamentoResult com lista de testamentos
        """
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

        response = self._client.get("/v1/censec/rcto/buscar", params=params)

        return BuscaTestamentoResult(
            total=response.get("total", 0),
            testamentos=response.get("testamentos", []),
            pagina=response.get("pagina", pagina),
            por_pagina=response.get("por_pagina", por_pagina),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def consultar_testamento(
        self,
        cartorio_id: str,
        codigo: str,
    ) -> TestamentoResult:
        """
        Consultar testamento específico.

        Args:
            cartorio_id: UUID do cartório
            codigo: Código do testamento no RCTO

        Returns:
            TestamentoResult com dados do testamento
        """
        response = self._client.get(
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

    def existe_testamento(
        self,
        cartorio_id: str,
        cpf: str,
    ) -> dict[str, Any]:
        """
        Verificar se pessoa possui testamento registrado.

        Args:
            cartorio_id: UUID do cartório
            cpf: CPF da pessoa

        Returns:
            Dict com existe (bool) e quantidade
        """
        cpf_clean = "".join(filter(str.isdigit, cpf))
        response = self._client.get(
            f"/v1/censec/rcto/existe/{cpf_clean}",
            params={"cartorio_id": str(cartorio_id)},
        )
        return response

    def registrar_testamento(
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
        """
        Registrar testamento no RCTO.

        Args:
            cartorio_id: UUID do cartório
            tipo: Tipo de testamento (publico, cerrado, particular)
            testador: Dados do testador (nome, cpf, data_nascimento, etc)
            data_lavratura: Data da lavratura (YYYY-MM-DD)
            livro: Número do livro
            folha: Número da folha
            dados_testamento: Dados adicionais do testamento
            tem_codicilo: Se possui codicilo

        Returns:
            RegistroAtoResult com protocolo
        """
        response = self._client.post(
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

    def revogar_testamento(
        self,
        cartorio_id: str,
        codigo_testamento: str,
        motivo: str,
        novo_testamento_codigo: str | None = None,
    ) -> dict[str, Any]:
        """
        Registrar revogação de testamento.

        Args:
            cartorio_id: UUID do cartório
            codigo_testamento: Código do testamento a revogar
            motivo: Motivo da revogação
            novo_testamento_codigo: Código do novo testamento (se houver)

        Returns:
            Confirmação da revogação
        """
        return self._client.post(
            "/v1/censec/rcto/revogar",
            json={
                "cartorio_id": str(cartorio_id),
                "codigo_testamento": codigo_testamento,
                "motivo": motivo,
                "novo_testamento_codigo": novo_testamento_codigo,
            },
        )

    # =========================================================================
    # CENPROC/CEP - Central de Procurações
    # =========================================================================

    def buscar_procuracoes(
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
        """
        Buscar procurações no CENPROC.

        Args:
            cartorio_id: UUID do cartório
            cpf_outorgante: CPF do outorgante
            cpf_outorgado: CPF do outorgado
            nome_outorgante: Nome do outorgante
            tipo: Tipo de procuração
            vigentes_apenas: Apenas procurações vigentes
            data_inicio: Data inicial
            data_fim: Data final
            pagina: Número da página
            por_pagina: Resultados por página

        Returns:
            BuscaProcuracaoResult com lista de procurações
        """
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

        response = self._client.get("/v1/censec/procuracoes/buscar", params=params)

        return BuscaProcuracaoResult(
            total=response.get("total", 0),
            procuracoes=response.get("procuracoes", []),
            pagina=response.get("pagina", pagina),
            por_pagina=response.get("por_pagina", por_pagina),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def consultar_procuracao(
        self,
        cartorio_id: str,
        codigo: str,
    ) -> ProcuracaoResult:
        """
        Consultar procuração específica.

        Args:
            cartorio_id: UUID do cartório
            codigo: Código da procuração

        Returns:
            ProcuracaoResult com dados completos
        """
        response = self._client.get(
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

    def verificar_procuracao_vigente(
        self,
        cartorio_id: str,
        codigo: str,
    ) -> dict[str, Any]:
        """
        Verificar se procuração está vigente.

        Args:
            cartorio_id: UUID do cartório
            codigo: Código da procuração

        Returns:
            Dict com vigente (bool), status e data_verificacao
        """
        return self._client.get(
            f"/v1/censec/procuracoes/{codigo}/verificar",
            params={"cartorio_id": str(cartorio_id)},
        )

    def registrar_procuracao(
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
        """
        Registrar procuração no CENPROC.

        Args:
            cartorio_id: UUID do cartório
            tipo: Tipo de procuração
            outorgante: Dados do outorgante
            outorgado: Dados do outorgado
            poderes: Lista de poderes concedidos
            data_lavratura: Data da lavratura
            livro: Número do livro
            folha: Número da folha
            data_validade: Data de validade (opcional)
            dados_adicionais: Dados extras

        Returns:
            RegistroAtoResult com protocolo
        """
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

        response = self._client.post("/v1/censec/procuracoes/registrar", json=payload)

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

    def registrar_substabelecimento(
        self,
        cartorio_id: str,
        codigo_procuracao: str,
        novo_outorgado: dict[str, Any],
        poderes_substabelecidos: list[str],
        com_reserva: bool = True,
        data_lavratura: str = None,
    ) -> RegistroAtoResult:
        """
        Registrar substabelecimento de procuração.

        Args:
            cartorio_id: UUID do cartório
            codigo_procuracao: Código da procuração original
            novo_outorgado: Dados do novo outorgado
            poderes_substabelecidos: Poderes sendo substabelecidos
            com_reserva: Com reserva de poderes
            data_lavratura: Data da lavratura

        Returns:
            RegistroAtoResult
        """
        response = self._client.post(
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

    def revogar_procuracao(
        self,
        cartorio_id: str,
        codigo_procuracao: str,
        motivo: str,
        data_revogacao: str | None = None,
    ) -> RegistroAtoResult:
        """
        Registrar revogação de procuração.

        Args:
            cartorio_id: UUID do cartório
            codigo_procuracao: Código da procuração
            motivo: Motivo da revogação
            data_revogacao: Data da revogação

        Returns:
            RegistroAtoResult
        """
        response = self._client.post(
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
    # CESDI - Separações, Divórcios e Inventários
    # =========================================================================

    def buscar_escrituras(
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
        """
        Buscar escrituras no CEP/CESDI.

        Args:
            cartorio_id: UUID do cartório
            cpf_parte: CPF de uma das partes
            nome_parte: Nome de uma das partes
            tipo: Tipo de escritura (divorcio, inventario, etc)
            data_inicio: Data inicial
            data_fim: Data final
            uf: UF do cartório
            pagina: Número da página
            por_pagina: Resultados por página

        Returns:
            BuscaEscrituraResult com lista de escrituras
        """
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

        response = self._client.get("/v1/censec/escrituras/buscar", params=params)

        return BuscaEscrituraResult(
            total=response.get("total", 0),
            escrituras=response.get("escrituras", []),
            pagina=response.get("pagina", pagina),
            por_pagina=response.get("por_pagina", por_pagina),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def consultar_escritura(
        self,
        cartorio_id: str,
        codigo: str,
    ) -> EscrituraResult:
        """
        Consultar escritura específica.

        Args:
            cartorio_id: UUID do cartório
            codigo: Código da escritura

        Returns:
            EscrituraResult com dados completos
        """
        response = self._client.get(
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

    def registrar_escritura(
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
        """
        Registrar escritura no CESDI/CEP.

        Args:
            cartorio_id: UUID do cartório
            tipo: Tipo (divorcio, inventario, separacao, etc)
            partes: Lista de partes envolvidas
            objeto: Objeto da escritura
            data_lavratura: Data da lavratura
            livro: Número do livro
            folha: Número da folha
            valor: Valor (se aplicável)
            imovel: Dados do imóvel (se aplicável)
            dados_adicionais: Dados extras

        Returns:
            RegistroAtoResult com protocolo
        """
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

        response = self._client.post("/v1/censec/escrituras/registrar", json=payload)

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
    # CNSIP - Central Nacional de Sinal Público
    # =========================================================================

    def consultar_sinal_publico(
        self,
        cartorio_id: str,
        cns_cartorio: str,
    ) -> SinalPublicoResult:
        """
        Consultar sinal público de um cartório.

        Args:
            cartorio_id: UUID do cartório consultante
            cns_cartorio: CNS do cartório a consultar

        Returns:
            SinalPublicoResult com imagem do sinal
        """
        response = self._client.get(
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

    def registrar_sinal_publico(
        self,
        cartorio_id: str,
        sinal_imagem: BinaryIO,
        notario_cpf: str,
    ) -> dict[str, Any]:
        """
        Registrar/atualizar sinal público do cartório.

        Args:
            cartorio_id: UUID do cartório
            sinal_imagem: Imagem do sinal público
            notario_cpf: CPF do notário

        Returns:
            Confirmação do registro
        """
        return self._client.post(
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

    def health(self) -> dict[str, Any]:
        """
        Verificar saúde da integração CENSEC.

        Returns:
            Status da conexão com CENSEC
        """
        return self._client.get("/v1/censec/health")

    def get_estatisticas(
        self,
        cartorio_id: str,
        periodo: str = "mes",
    ) -> dict[str, Any]:
        """
        Obter estatísticas de uso do CENSEC.

        Args:
            cartorio_id: UUID do cartório
            periodo: Período (dia, semana, mes, ano)

        Returns:
            Estatísticas de consultas e registros
        """
        return self._client.get(
            "/v1/censec/estatisticas",
            params={
                "cartorio_id": str(cartorio_id),
                "periodo": periodo,
            },
        )
