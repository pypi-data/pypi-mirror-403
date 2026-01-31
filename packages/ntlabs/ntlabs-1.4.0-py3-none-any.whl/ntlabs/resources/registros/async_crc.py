"""
Neural LAB - AI Solutions Platform
CRC Nacional Async Resource - Central de Informações do Registro Civil.

Versão assíncrona do CRCResource.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from datetime import datetime
from typing import Any, BinaryIO

from .crc import (
    AverbacaoResult,
    BuscaCertidaoResult,
    CertidaoResult,
    CertificadoInfo,
    CertificadoUploadResult,
    LivroDResult,
    ProclamaResult,
    SegundaViaResult,
    StatusCertidao,
    TipoCertidao,
    TipoCertificado,
    VerificacaoResult,
)


class AsyncCRCResource:
    """
    CRC Nacional Async - Central de Informações do Registro Civil.

    Versão assíncrona para uso com AsyncNeuralLabClient.

    Usage:
        async with AsyncNeuralLabClient(api_key="...") as client:
            # Upload do certificado
            result = await client.crc.upload_certificate(
                cartorio_id="uuid",
                certificate=pfx_bytes,
                password="senha123"
            )

            # Consultar certidão
            certidao = await client.crc.consultar_certidao(
                cartorio_id="uuid",
                tipo="nascimento",
                matricula="123456..."
            )
    """

    def __init__(self, client):
        self._client = client

    # =========================================================================
    # Gestão de Certificados
    # =========================================================================

    async def upload_certificate(
        self,
        cartorio_id: str,
        certificate: BinaryIO,
        password: str,
        store_password: bool = False,
    ) -> CertificadoUploadResult:
        """Upload de certificado ICP-Brasil A3 do cartório."""
        response = await self._client.post(
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

    async def get_certificates(self, cartorio_id: str) -> list[CertificadoInfo]:
        """Listar certificados de um cartório."""
        response = await self._client.get(
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

    async def has_valid_certificate(self, cartorio_id: str) -> bool:
        """Verificar se cartório possui certificado válido."""
        response = await self._client.get(
            "/v1/crc/certificates/validate",
            params={"cartorio_id": str(cartorio_id)},
        )
        return response.get("valid", False)

    async def revoke_certificate(self, certificado_id: str, motivo: str) -> bool:
        """Revogar certificado."""
        response = await self._client.post(
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

    async def consultar_certidao(
        self,
        cartorio_id: str,
        tipo: str,
        matricula: str,
    ) -> CertidaoResult:
        """Consultar certidão por matrícula."""
        response = await self._client.get(
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

    async def buscar_certidoes(
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
        """Buscar certidões por dados pessoais."""
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

        response = await self._client.get("/v1/crc/certidoes/buscar", params=params)

        return BuscaCertidaoResult(
            total=response.get("total", 0),
            certidoes=response.get("certidoes", []),
            pagina=response.get("pagina", pagina),
            por_pagina=response.get("por_pagina", por_pagina),
            latency_ms=response.get("latency_ms", 0),
            cost_brl=response.get("cost_brl", 0),
        )

    async def verificar_autenticidade(
        self,
        codigo_verificacao: str,
        matricula: str | None = None,
    ) -> VerificacaoResult:
        """Verificar autenticidade de certidão."""
        params = {"codigo": codigo_verificacao}
        if matricula:
            params["matricula"] = matricula

        response = await self._client.get("/v1/crc/verificar", params=params)

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

    async def solicitar_segunda_via(
        self,
        cartorio_id: str,
        tipo: str,
        matricula: str,
        solicitante: dict[str, str],
        motivo: str,
        formato: str = "digital",
        endereco_entrega: dict[str, str] | None = None,
    ) -> SegundaViaResult:
        """Solicitar segunda via de certidão."""
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

        response = await self._client.post("/v1/crc/segunda-via", json=payload)

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

    async def consultar_segunda_via(self, protocolo: str) -> SegundaViaResult:
        """Consultar status de solicitação de segunda via."""
        response = await self._client.get(f"/v1/crc/segunda-via/{protocolo}")

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

    async def registrar_averbacao(
        self,
        cartorio_id: str,
        matricula: str,
        tipo_averbacao: str,
        conteudo: str,
        documento_base: dict[str, Any] | None = None,
    ) -> AverbacaoResult:
        """Registrar averbação em certidão."""
        payload = {
            "cartorio_id": str(cartorio_id),
            "matricula": matricula,
            "tipo_averbacao": tipo_averbacao,
            "conteudo": conteudo,
        }

        if documento_base:
            payload["documento_base"] = documento_base

        response = await self._client.post("/v1/crc/averbacao", json=payload)

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
    # e-Proclamas
    # =========================================================================

    async def enviar_proclama(
        self,
        cartorio_id: str,
        nubente1: dict[str, Any],
        nubente2: dict[str, Any],
        data_casamento: str | None = None,
        regime_bens: str = "comunhao_parcial",
        observacoes: str | None = None,
    ) -> ProclamaResult:
        """Enviar proclama (edital de casamento) para publicação."""
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

        response = await self._client.post("/v1/crc/proclama", json=payload)

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

    async def consultar_proclama(self, protocolo: str) -> ProclamaResult:
        """Consultar status de proclama."""
        response = await self._client.get(f"/v1/crc/proclama/{protocolo}")

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

    async def cancelar_proclama(
        self,
        cartorio_id: str,
        protocolo: str,
        motivo: str,
    ) -> dict[str, Any]:
        """Cancelar proclama publicado."""
        return await self._client.post(
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

    async def registrar_livro_d(
        self,
        cartorio_id: str,
        proclama_protocolo: str,
        data_casamento: str,
        dados_casamento: dict[str, Any],
    ) -> LivroDResult:
        """Registrar casamento no Livro D Eletrônico."""
        response = await self._client.post(
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

    async def health(self) -> dict[str, Any]:
        """Verificar saúde da integração CRC."""
        return await self._client.get("/v1/crc/health")

    async def get_cartorios(
        self,
        uf: str | None = None,
        municipio: str | None = None,
        tipo: str | None = None,
    ) -> list[dict[str, Any]]:
        """Listar cartórios de registro civil."""
        params = {}
        if uf:
            params["uf"] = uf.upper()
        if municipio:
            params["municipio"] = municipio
        if tipo:
            params["tipo"] = tipo

        response = await self._client.get("/v1/crc/cartorios", params=params)
        return response.get("cartorios", [])
