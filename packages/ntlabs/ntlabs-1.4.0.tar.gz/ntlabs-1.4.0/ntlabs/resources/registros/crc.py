"""
Neural LAB - AI Solutions Platform
CRC Nacional Resource - Central de Informações do Registro Civil.

Integração com a CRC Nacional (ARPEN-Brasil) para:
- Consulta de certidões (nascimento, casamento, óbito)
- Verificação de autenticidade
- e-Proclamas (editais de casamento)
- Livro D Eletrônico
- Gestão de certificados ICP-Brasil (A3)

Provimento CNJ nº 46/2015 - Base legal da CRC Nacional.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, BinaryIO

from ...base import DataclassMixin


class TipoCertidao(str, Enum):
    """Tipos de certidão do registro civil."""

    NASCIMENTO = "nascimento"
    CASAMENTO = "casamento"
    OBITO = "obito"
    INTEIRO_TEOR = "inteiro_teor"


class StatusCertidao(str, Enum):
    """Status de uma certidão."""

    VALIDA = "valida"
    CANCELADA = "cancelada"
    AVERBADA = "averbada"
    NAO_ENCONTRADA = "nao_encontrada"


class TipoCertificado(str, Enum):
    """Tipos de certificado ICP-Brasil para cartórios."""

    E_CPF_A3 = "e-cpf-a3"  # Pessoa física (tabelião)
    E_CNPJ_A3 = "e-cnpj-a3"  # Pessoa jurídica (cartório)


@dataclass
class CertidaoResult(DataclassMixin):
    """Resultado de consulta de certidão."""

    matricula: str
    tipo: TipoCertidao
    livro: str
    folha: str
    termo: str
    data_registro: str
    cartorio_nome: str
    cartorio_cns: str
    municipio: str
    uf: str
    status: StatusCertidao
    dados: dict[str, Any]
    hash_validacao: str | None = None
    url_verificacao: str | None = None
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class BuscaCertidaoResult(DataclassMixin):
    """Resultado de busca de certidões."""

    total: int
    certidoes: list[dict[str, Any]]
    pagina: int
    por_pagina: int
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class VerificacaoResult(DataclassMixin):
    """Resultado de verificação de autenticidade."""

    autentica: bool
    matricula: str
    tipo: TipoCertidao
    data_emissao: str | None
    cartorio_nome: str | None
    mensagem: str
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class ProclamaResult(DataclassMixin):
    """Resultado de envio de proclama (edital de casamento)."""

    id: str
    protocolo: str
    status: str
    data_publicacao: str | None
    prazo_final: str | None
    nubente1: dict[str, str]
    nubente2: dict[str, str]
    cartorio_cns: str
    mensagem: str
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class LivroDResult(DataclassMixin):
    """Registro no Livro D Eletrônico (casamentos com proclamas de outros cartórios)."""

    id: str
    numero_registro: str
    data_registro: str
    proclama_origem: str
    cartorio_origem_cns: str
    cartorio_destino_cns: str
    status: str
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class SegundaViaResult(DataclassMixin):
    """Resultado de solicitação de segunda via."""

    id: str
    protocolo: str
    status: str
    matricula: str
    tipo: TipoCertidao
    solicitante: dict[str, str]
    valor_emolumentos: float
    prazo_entrega: str | None
    url_pagamento: str | None
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class AverbacaoResult(DataclassMixin):
    """Resultado de averbação em certidão."""

    id: str
    matricula: str
    tipo_averbacao: str
    data_averbacao: str
    conteudo: str
    status: str
    latency_ms: int = 0
    cost_brl: float = 0.0


@dataclass
class CertificadoInfo(DataclassMixin):
    """Informações do certificado ICP-Brasil do cartório."""

    id: str
    tipo: TipoCertificado
    titular_nome: str
    titular_cpf_cnpj: str | None
    emissor: str
    valido_de: datetime
    valido_ate: datetime
    status: str
    crc_validado: bool
    cartorio_cns: str | None


@dataclass
class CertificadoUploadResult(DataclassMixin):
    """Resultado do upload de certificado."""

    success: bool
    certificado_id: str | None = None
    certificado_info: CertificadoInfo | None = None
    error: str | None = None


class CRCResource:
    """
    CRC Nacional - Central de Informações do Registro Civil.

    Integração com a plataforma nacional de registro civil (ARPEN-Brasil).
    Requer certificado digital ICP-Brasil A3 do cartório.

    Usage:
        # Upload do certificado do cartório (feito uma vez)
        result = client.crc.upload_certificate(
            cartorio_id="uuid",
            certificate=pfx_bytes,
            password="senha123"
        )

        # Consultar certidão por matrícula
        certidao = client.crc.consultar_certidao(
            cartorio_id="uuid",
            tipo="nascimento",
            matricula="123456 01 55 2020 1 00001 001 0000001-00"
        )

        # Buscar certidões por dados pessoais
        resultados = client.crc.buscar_certidoes(
            cartorio_id="uuid",
            tipo="nascimento",
            nome="João da Silva",
            data_nascimento="1990-05-15"
        )

        # Verificar autenticidade
        verificacao = client.crc.verificar_autenticidade(
            codigo_verificacao="ABC123XYZ",
            matricula="123456..."
        )

        # Enviar proclama (edital de casamento)
        proclama = client.crc.enviar_proclama(
            cartorio_id="uuid",
            nubente1={"nome": "...", "cpf": "..."},
            nubente2={"nome": "...", "cpf": "..."}
        )
    """

    def __init__(self, client):
        self._client = client

    # =========================================================================
    # Gestão de Certificados
    # =========================================================================

    def upload_certificate(
        self,
        cartorio_id: str,
        certificate: BinaryIO,
        password: str,
        store_password: bool = False,
    ) -> CertificadoUploadResult:
        """
        Upload de certificado ICP-Brasil A3 do cartório.

        O certificado é necessário para autenticar operações na CRC Nacional.

        Args:
            cartorio_id: UUID do cartório no sistema
            certificate: Arquivo PKCS#12 (.pfx/.p12)
            password: Senha do certificado
            store_password: Armazenar senha criptografada (para operações automáticas)

        Returns:
            CertificadoUploadResult com informações do certificado
        """
        response = self._client.post(
            "/v1/crc/certificates/upload",
            files={"certificate": certificate},
            data={
                "cartorio_id": str(cartorio_id),
                "password": password,
                "store_password": str(store_password).lower(),
            },
        )

        if not response.get("success"):
            return CertificadoUploadResult(
                success=False,
                error=response.get("error", "Upload falhou"),
            )

        cert_data = response.get("certificate", {})
        return CertificadoUploadResult(
            success=True,
            certificado_id=cert_data.get("id"),
            certificado_info=CertificadoInfo(
                id=cert_data.get("id", ""),
                tipo=TipoCertificado(cert_data.get("tipo", "e-cnpj-a3")),
                titular_nome=cert_data.get("titular_nome", ""),
                titular_cpf_cnpj=cert_data.get("titular_cpf_cnpj"),
                emissor=cert_data.get("emissor", ""),
                valido_de=datetime.fromisoformat(
                    cert_data.get("valido_de", datetime.now().isoformat())
                ),
                valido_ate=datetime.fromisoformat(
                    cert_data.get("valido_ate", datetime.now().isoformat())
                ),
                status=cert_data.get("status", "active"),
                crc_validado=cert_data.get("crc_validado", False),
                cartorio_cns=cert_data.get("cartorio_cns"),
            ),
        )

    def get_certificates(self, cartorio_id: str) -> list[CertificadoInfo]:
        """
        Listar certificados de um cartório.

        Args:
            cartorio_id: UUID do cartório

        Returns:
            Lista de certificados
        """
        response = self._client.get(
            "/v1/crc/certificates",
            params={"cartorio_id": str(cartorio_id)},
        )

        return [
            CertificadoInfo(
                id=cert.get("id", ""),
                tipo=TipoCertificado(cert.get("tipo", "e-cnpj-a3")),
                titular_nome=cert.get("titular_nome", ""),
                titular_cpf_cnpj=cert.get("titular_cpf_cnpj"),
                emissor=cert.get("emissor", ""),
                valido_de=datetime.fromisoformat(
                    cert.get("valido_de", datetime.now().isoformat())
                ),
                valido_ate=datetime.fromisoformat(
                    cert.get("valido_ate", datetime.now().isoformat())
                ),
                status=cert.get("status", "active"),
                crc_validado=cert.get("crc_validado", False),
                cartorio_cns=cert.get("cartorio_cns"),
            )
            for cert in response.get("certificates", [])
        ]

    def has_valid_certificate(self, cartorio_id: str) -> bool:
        """
        Verificar se cartório possui certificado válido.

        Args:
            cartorio_id: UUID do cartório

        Returns:
            True se possui certificado válido e ativo
        """
        response = self._client.get(
            "/v1/crc/certificates/validate",
            params={"cartorio_id": str(cartorio_id)},
        )
        return response.get("valid", False)

    def revoke_certificate(self, certificado_id: str, motivo: str) -> bool:
        """
        Revogar certificado.

        Args:
            certificado_id: UUID do certificado
            motivo: Motivo da revogação

        Returns:
            True se revogado com sucesso
        """
        response = self._client.post(
            "/v1/crc/certificates/revoke",
            json={
                "certificado_id": str(certificado_id),
                "motivo": motivo,
            },
        )
        return response.get("success", False)

    # =========================================================================
    # Consulta de Certidões
    # =========================================================================

    def consultar_certidao(
        self,
        cartorio_id: str,
        tipo: str,
        matricula: str,
    ) -> CertidaoResult:
        """
        Consultar certidão por matrícula.

        Args:
            cartorio_id: UUID do cartório (para autenticação)
            tipo: Tipo de certidão (nascimento, casamento, obito)
            matricula: Matrícula da certidão (formato CRC)

        Returns:
            CertidaoResult com dados da certidão
        """
        response = self._client.get(
            "/v1/crc/certidao",
            params={
                "cartorio_id": str(cartorio_id),
                "tipo": tipo,
                "matricula": matricula,
            },
        )

        return CertidaoResult(
            matricula=response.get("matricula", matricula),
            tipo=TipoCertidao(response.get("tipo", tipo)),
            livro=response.get("livro", ""),
            folha=response.get("folha", ""),
            termo=response.get("termo", ""),
            data_registro=response.get("data_registro", ""),
            cartorio_nome=response.get("cartorio_nome", ""),
            cartorio_cns=response.get("cartorio_cns", ""),
            municipio=response.get("municipio", ""),
            uf=response.get("uf", ""),
            status=StatusCertidao(response.get("status", "valida")),
            dados=response.get("dados", {}),
            hash_validacao=response.get("hash_validacao"),
            url_verificacao=response.get("url_verificacao"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def buscar_certidoes(
        self,
        cartorio_id: str,
        tipo: str,
        nome: str | None = None,
        cpf: str | None = None,
        data_nascimento: str | None = None,
        nome_mae: str | None = None,
        nome_pai: str | None = None,
        municipio: str | None = None,
        uf: str | None = None,
        pagina: int = 1,
        por_pagina: int = 20,
    ) -> BuscaCertidaoResult:
        """
        Buscar certidões por dados pessoais.

        Args:
            cartorio_id: UUID do cartório (para autenticação)
            tipo: Tipo de certidão (nascimento, casamento, obito)
            nome: Nome da pessoa
            cpf: CPF (somente dígitos)
            data_nascimento: Data de nascimento (YYYY-MM-DD)
            nome_mae: Nome da mãe
            nome_pai: Nome do pai
            municipio: Município do registro
            uf: UF do registro
            pagina: Número da página
            por_pagina: Resultados por página (máx 50)

        Returns:
            BuscaCertidaoResult com lista de certidões encontradas
        """
        params = {
            "cartorio_id": str(cartorio_id),
            "tipo": tipo,
            "pagina": pagina,
            "por_pagina": min(por_pagina, 50),
        }

        if nome:
            params["nome"] = nome
        if cpf:
            params["cpf"] = "".join(filter(str.isdigit, cpf))
        if data_nascimento:
            params["data_nascimento"] = data_nascimento
        if nome_mae:
            params["nome_mae"] = nome_mae
        if nome_pai:
            params["nome_pai"] = nome_pai
        if municipio:
            params["municipio"] = municipio
        if uf:
            params["uf"] = uf.upper()

        response = self._client.get("/v1/crc/certidoes/buscar", params=params)

        return BuscaCertidaoResult(
            total=response.get("total", 0),
            certidoes=response.get("certidoes", []),
            pagina=response.get("pagina", pagina),
            por_pagina=response.get("por_pagina", por_pagina),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def verificar_autenticidade(
        self,
        codigo_verificacao: str,
        matricula: str | None = None,
    ) -> VerificacaoResult:
        """
        Verificar autenticidade de certidão.

        Pode ser usado sem autenticação (consulta pública).

        Args:
            codigo_verificacao: Código de verificação impresso na certidão
            matricula: Matrícula (opcional, aumenta precisão)

        Returns:
            VerificacaoResult com status de autenticidade
        """
        params = {"codigo": codigo_verificacao}
        if matricula:
            params["matricula"] = matricula

        response = self._client.get("/v1/crc/verificar", params=params)

        return VerificacaoResult(
            autentica=response.get("autentica", False),
            matricula=response.get("matricula", ""),
            tipo=TipoCertidao(response.get("tipo", "nascimento")),
            data_emissao=response.get("data_emissao"),
            cartorio_nome=response.get("cartorio_nome"),
            mensagem=response.get("mensagem", ""),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    # =========================================================================
    # Segunda Via
    # =========================================================================

    def solicitar_segunda_via(
        self,
        cartorio_id: str,
        tipo: str,
        matricula: str,
        solicitante: dict[str, str],
        motivo: str,
        formato: str = "digital",
        endereco_entrega: dict[str, str] | None = None,
    ) -> SegundaViaResult:
        """
        Solicitar segunda via de certidão.

        Args:
            cartorio_id: UUID do cartório
            tipo: Tipo de certidão
            matricula: Matrícula da certidão original
            solicitante: Dados do solicitante (nome, cpf, email, telefone)
            motivo: Motivo da solicitação
            formato: 'digital' ou 'fisica'
            endereco_entrega: Endereço para entrega (se física)

        Returns:
            SegundaViaResult com protocolo e informações
        """
        payload = {
            "cartorio_id": str(cartorio_id),
            "tipo": tipo,
            "matricula": matricula,
            "solicitante": solicitante,
            "motivo": motivo,
            "formato": formato,
        }

        if endereco_entrega:
            payload["endereco_entrega"] = endereco_entrega

        response = self._client.post("/v1/crc/segunda-via", json=payload)

        return SegundaViaResult(
            id=response.get("id", ""),
            protocolo=response.get("protocolo", ""),
            status=response.get("status", "pendente"),
            matricula=matricula,
            tipo=TipoCertidao(tipo),
            solicitante=solicitante,
            valor_emolumentos=response.get("valor_emolumentos", 0),
            prazo_entrega=response.get("prazo_entrega"),
            url_pagamento=response.get("url_pagamento"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def consultar_segunda_via(self, protocolo: str) -> SegundaViaResult:
        """
        Consultar status de solicitação de segunda via.

        Args:
            protocolo: Número do protocolo

        Returns:
            SegundaViaResult com status atualizado
        """
        response = self._client.get(f"/v1/crc/segunda-via/{protocolo}")

        return SegundaViaResult(
            id=response.get("id", ""),
            protocolo=protocolo,
            status=response.get("status", ""),
            matricula=response.get("matricula", ""),
            tipo=TipoCertidao(response.get("tipo", "nascimento")),
            solicitante=response.get("solicitante", {}),
            valor_emolumentos=response.get("valor_emolumentos", 0),
            prazo_entrega=response.get("prazo_entrega"),
            url_pagamento=response.get("url_pagamento"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    # =========================================================================
    # Averbações
    # =========================================================================

    def registrar_averbacao(
        self,
        cartorio_id: str,
        matricula: str,
        tipo_averbacao: str,
        conteudo: str,
        documento_base: dict[str, Any] | None = None,
    ) -> AverbacaoResult:
        """
        Registrar averbação em certidão.

        Args:
            cartorio_id: UUID do cartório
            matricula: Matrícula da certidão
            tipo_averbacao: Tipo (divorcio, obito, retificacao, reconhecimento_paternidade)
            conteudo: Conteúdo da averbação
            documento_base: Documento que fundamenta a averbação

        Returns:
            AverbacaoResult com confirmação
        """
        payload = {
            "cartorio_id": str(cartorio_id),
            "matricula": matricula,
            "tipo_averbacao": tipo_averbacao,
            "conteudo": conteudo,
        }

        if documento_base:
            payload["documento_base"] = documento_base

        response = self._client.post("/v1/crc/averbacao", json=payload)

        return AverbacaoResult(
            id=response.get("id", ""),
            matricula=matricula,
            tipo_averbacao=tipo_averbacao,
            data_averbacao=response.get("data_averbacao", ""),
            conteudo=conteudo,
            status=response.get("status", "registrada"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    # =========================================================================
    # e-Proclamas (Editais de Casamento)
    # =========================================================================

    def enviar_proclama(
        self,
        cartorio_id: str,
        nubente1: dict[str, Any],
        nubente2: dict[str, Any],
        data_casamento: str | None = None,
        regime_bens: str = "comunhao_parcial",
        observacoes: str | None = None,
    ) -> ProclamaResult:
        """
        Enviar proclama (edital de casamento) para publicação.

        Conforme Provimento CNJ 46/2015, os proclamas devem ser
        publicados eletronicamente na CRC Nacional.

        Args:
            cartorio_id: UUID do cartório
            nubente1: Dados do primeiro nubente (nome, cpf, naturalidade, etc)
            nubente2: Dados do segundo nubente
            data_casamento: Data prevista do casamento (YYYY-MM-DD)
            regime_bens: Regime de bens (comunhao_parcial, comunhao_universal, separacao_total, participacao_final)
            observacoes: Observações adicionais

        Returns:
            ProclamaResult com protocolo e prazo
        """
        payload = {
            "cartorio_id": str(cartorio_id),
            "nubente1": nubente1,
            "nubente2": nubente2,
            "regime_bens": regime_bens,
        }

        if data_casamento:
            payload["data_casamento"] = data_casamento
        if observacoes:
            payload["observacoes"] = observacoes

        response = self._client.post("/v1/crc/proclama", json=payload)

        return ProclamaResult(
            id=response.get("id", ""),
            protocolo=response.get("protocolo", ""),
            status=response.get("status", "publicado"),
            data_publicacao=response.get("data_publicacao"),
            prazo_final=response.get("prazo_final"),
            nubente1=nubente1,
            nubente2=nubente2,
            cartorio_cns=response.get("cartorio_cns", ""),
            mensagem=response.get("mensagem", ""),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def consultar_proclama(self, protocolo: str) -> ProclamaResult:
        """
        Consultar status de proclama.

        Args:
            protocolo: Número do protocolo

        Returns:
            ProclamaResult com status atualizado
        """
        response = self._client.get(f"/v1/crc/proclama/{protocolo}")

        return ProclamaResult(
            id=response.get("id", ""),
            protocolo=protocolo,
            status=response.get("status", ""),
            data_publicacao=response.get("data_publicacao"),
            prazo_final=response.get("prazo_final"),
            nubente1=response.get("nubente1", {}),
            nubente2=response.get("nubente2", {}),
            cartorio_cns=response.get("cartorio_cns", ""),
            mensagem=response.get("mensagem", ""),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    def cancelar_proclama(
        self,
        cartorio_id: str,
        protocolo: str,
        motivo: str,
    ) -> dict[str, Any]:
        """
        Cancelar proclama publicado.

        Args:
            cartorio_id: UUID do cartório
            protocolo: Número do protocolo
            motivo: Motivo do cancelamento

        Returns:
            Confirmação do cancelamento
        """
        return self._client.post(
            "/v1/crc/proclama/cancelar",
            json={
                "cartorio_id": str(cartorio_id),
                "protocolo": protocolo,
                "motivo": motivo,
            },
        )

    # =========================================================================
    # Livro D Eletrônico
    # =========================================================================

    def registrar_livro_d(
        self,
        cartorio_id: str,
        proclama_protocolo: str,
        data_casamento: str,
        dados_casamento: dict[str, Any],
    ) -> LivroDResult:
        """
        Registrar casamento no Livro D Eletrônico.

        O Livro D é usado quando os proclamas foram publicados
        por cartório diferente do que celebra o casamento.

        Args:
            cartorio_id: UUID do cartório que celebra
            proclama_protocolo: Protocolo do proclama (de outro cartório)
            data_casamento: Data do casamento (YYYY-MM-DD)
            dados_casamento: Dados adicionais do casamento

        Returns:
            LivroDResult com número do registro
        """
        response = self._client.post(
            "/v1/crc/livro-d",
            json={
                "cartorio_id": str(cartorio_id),
                "proclama_protocolo": proclama_protocolo,
                "data_casamento": data_casamento,
                "dados_casamento": dados_casamento,
            },
        )

        return LivroDResult(
            id=response.get("id", ""),
            numero_registro=response.get("numero_registro", ""),
            data_registro=response.get("data_registro", ""),
            proclama_origem=proclama_protocolo,
            cartorio_origem_cns=response.get("cartorio_origem_cns", ""),
            cartorio_destino_cns=response.get("cartorio_destino_cns", ""),
            status=response.get("status", "registrado"),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    # =========================================================================
    # Utilidades
    # =========================================================================

    def health(self) -> dict[str, Any]:
        """
        Verificar saúde da integração CRC.

        Returns:
            Status da conexão com CRC Nacional
        """
        return self._client.get("/v1/crc/health")

    def get_cartorios(
        self,
        uf: str | None = None,
        municipio: str | None = None,
        tipo: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Listar cartórios de registro civil.

        Args:
            uf: Filtrar por UF
            municipio: Filtrar por município
            tipo: Tipo de cartório

        Returns:
            Lista de cartórios
        """
        params = {}
        if uf:
            params["uf"] = uf.upper()
        if municipio:
            params["municipio"] = municipio
        if tipo:
            params["tipo"] = tipo

        response = self._client.get("/v1/crc/cartorios", params=params)
        return response.get("cartorios", [])
