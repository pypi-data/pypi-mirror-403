"""
Neural LAB - AI Solutions Platform
Async Cartório Resource - Notary AI features.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from typing import Any, BinaryIO

from .cartorio import DocumentGeneration, OCRResult, ValidationResult


class AsyncCartorioResource:
    """Async notary AI resource for Mercurius integration."""

    def __init__(self, client):
        self._client = client

    async def ocr_certidao(
        self,
        image: BinaryIO,
        tipo: str = "nascimento",
        **kwargs,
    ) -> OCRResult:
        """OCR extraction from certificates."""
        files = {"file": image}
        data = {"tipo": tipo}

        response = await self._client.post(
            "/v1/cartorio/ocr/certidao",
            files=files,
            data=data,
        )

        return OCRResult(
            text=response.get("text", ""),
            structured_data=response.get("dados", {}),
            confidence=response.get("confidence", 0.0),
            document_type=f"certidao_{tipo}",
        )

    async def ocr_escritura(self, image: BinaryIO, **kwargs) -> OCRResult:
        """OCR extraction from public deeds."""
        files = {"file": image}
        response = await self._client.post("/v1/cartorio/ocr/escritura", files=files)

        return OCRResult(
            text=response.get("text", ""),
            structured_data=response.get("dados", {}),
            confidence=response.get("confidence", 0.0),
            document_type="escritura",
        )

    async def ocr_procuracao(self, image: BinaryIO, **kwargs) -> OCRResult:
        """OCR extraction from power of attorney."""
        files = {"file": image}
        response = await self._client.post("/v1/cartorio/ocr/procuracao", files=files)

        return OCRResult(
            text=response.get("text", ""),
            structured_data=response.get("dados", {}),
            confidence=response.get("confidence", 0.0),
            document_type="procuracao",
        )

    async def generate_escritura(
        self,
        tipo: str,
        vendedor: dict[str, Any],
        comprador: dict[str, Any],
        imovel: dict[str, Any],
        valor: float,
        **kwargs,
    ) -> DocumentGeneration:
        """Generate deed draft."""
        response = await self._client.post(
            "/v1/cartorio/generate/escritura",
            json={
                "tipo": tipo,
                "vendedor": vendedor,
                "comprador": comprador,
                "imovel": imovel,
                "valor": valor,
                **kwargs,
            },
        )

        return DocumentGeneration(
            content=response.get("content", ""),
            document_type=f"escritura_{tipo}",
            metadata=response.get("metadata", {}),
        )

    async def generate_procuracao(
        self,
        outorgante: dict[str, Any],
        outorgado: dict[str, Any],
        poderes: list[str],
        prazo: int | None = None,
        **kwargs,
    ) -> DocumentGeneration:
        """Generate power of attorney draft."""
        response = await self._client.post(
            "/v1/cartorio/generate/procuracao",
            json={
                "outorgante": outorgante,
                "outorgado": outorgado,
                "poderes": poderes,
                "prazo": prazo,
                **kwargs,
            },
        )

        return DocumentGeneration(
            content=response.get("content", ""),
            document_type="procuracao",
            metadata=response.get("metadata", {}),
        )

    async def generate_ata(
        self,
        tipo: str,
        fatos: str,
        local: str,
        data_hora: str,
        interessados: list[dict[str, Any]],
        **kwargs,
    ) -> DocumentGeneration:
        """Generate notarial minutes."""
        response = await self._client.post(
            "/v1/cartorio/generate/ata",
            json={
                "tipo": tipo,
                "fatos": fatos,
                "local": local,
                "data_hora": data_hora,
                "interessados": interessados,
                **kwargs,
            },
        )

        return DocumentGeneration(
            content=response.get("content", ""),
            document_type=f"ata_{tipo}",
            metadata=response.get("metadata", {}),
        )

    async def generate_document(
        self,
        document_type: str,
        data: dict[str, Any],
        template: str | None = None,
    ) -> str:
        """
        Generate a legal document using AI.

        Extracted from Sistema Mercurius.

        Args:
            document_type: Type (escritura, certidao, procuracao, etc.)
            data: Document data (parties, property, values, etc.)
            template: Optional template to follow

        Returns:
            Generated document text
        """
        system_prompt = f"""Você é um especialista em documentos cartorários brasileiros.
Gere um(a) {document_type} seguindo rigorosamente as normas do Provimento CNJ 100/2020.
Use linguagem jurídica formal e precisa.
Inclua todas as cláusulas obrigatórias para este tipo de documento."""

        if template:
            system_prompt += f"\n\nSiga este modelo como referência:\n{template}"

        messages = [
            {
                "role": "user",
                "content": f"Gere o documento com os seguintes dados:\n{data}",
            }
        ]

        response = await self._client.post(
            "/v1/llm/completions",
            json={
                "messages": [{"role": "system", "content": system_prompt}] + messages,
                "max_tokens": 4096,
                "temperature": 0.2,
            },
        )

        return response.get("choices", [{}])[0].get("message", {}).get("content", "")

    async def validate_cpf(self, cpf: str, **kwargs) -> ValidationResult:
        """Validate CPF and check biographical data."""
        response = await self._client.post(
            "/v1/cartorio/validate/cpf",
            json={"cpf": cpf, **kwargs},
        )

        return ValidationResult(
            is_valid=response.get("is_valid", False),
            message=response.get("message", ""),
            details=response.get("details", {}),
        )

    async def check_restricoes(
        self,
        cpf: str | None = None,
        cnpj: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Check for restrictions (protests, lawsuits)."""
        response = await self._client.post(
            "/v1/cartorio/check/restricoes",
            json={"cpf": cpf, "cnpj": cnpj, **kwargs},
        )
        return response

    async def search_imoveis(
        self,
        query: str,
        municipio: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Semantic search in property records."""
        response = await self._client.post(
            "/v1/cartorio/search/imoveis",
            json={"query": query, "municipio": municipio, **kwargs},
        )
        return response.get("resultados", [])
