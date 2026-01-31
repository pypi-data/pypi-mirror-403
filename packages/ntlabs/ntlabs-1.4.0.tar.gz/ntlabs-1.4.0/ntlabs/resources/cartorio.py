"""
Neural LAB - AI Solutions Platform
Cartório Resource - Notary AI features (Mercurius integration).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from dataclasses import dataclass
from typing import Any, BinaryIO

from ..base import DataclassMixin


@dataclass
class OCRResult(DataclassMixin):
    """OCR extraction result."""

    text: str
    structured_data: dict[str, Any]
    confidence: float
    document_type: str


@dataclass
class DocumentGeneration(DataclassMixin):
    """Generated legal document."""

    content: str
    document_type: str
    metadata: dict[str, Any]


@dataclass
class ValidationResult(DataclassMixin):
    """Document/data validation result."""

    is_valid: bool
    message: str
    details: dict[str, Any]


class CartorioResource:
    """
    Notary AI resource for Mercurius integration.

    Usage:
        # OCR certidão
        result = client.cartorio.ocr_certidao(image_file)

        # Generate escritura
        minuta = client.cartorio.generate_escritura(dados)

        # Validate CPF
        validation = client.cartorio.validate_cpf("123.456.789-00")
    """

    def __init__(self, client):
        self._client = client

    def ocr_certidao(
        self,
        image: BinaryIO,
        tipo: str = "nascimento",
        **kwargs,
    ) -> OCRResult:
        """
        OCR extraction from certificates.

        Args:
            image: Image file (jpg, png, pdf)
            tipo: Certificate type (nascimento, casamento, obito)
            **kwargs: Additional parameters

        Returns:
            OCR result with structured data
        """
        files = {"file": image}
        data = {"tipo": tipo}

        response = self._client.post(
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

    def ocr_escritura(
        self,
        image: BinaryIO,
        **kwargs,
    ) -> OCRResult:
        """
        OCR extraction from public deeds.

        Args:
            image: Image file (jpg, png, pdf)
            **kwargs: Additional parameters

        Returns:
            OCR result with structured data
        """
        files = {"file": image}

        response = self._client.post(
            "/v1/cartorio/ocr/escritura",
            files=files,
        )

        return OCRResult(
            text=response.get("text", ""),
            structured_data=response.get("dados", {}),
            confidence=response.get("confidence", 0.0),
            document_type="escritura",
        )

    def ocr_procuracao(
        self,
        image: BinaryIO,
        **kwargs,
    ) -> OCRResult:
        """
        OCR extraction from power of attorney.

        Args:
            image: Image file (jpg, png, pdf)
            **kwargs: Additional parameters

        Returns:
            OCR result with structured data
        """
        files = {"file": image}

        response = self._client.post(
            "/v1/cartorio/ocr/procuracao",
            files=files,
        )

        return OCRResult(
            text=response.get("text", ""),
            structured_data=response.get("dados", {}),
            confidence=response.get("confidence", 0.0),
            document_type="procuracao",
        )

    def generate_escritura(
        self,
        tipo: str,
        vendedor: dict[str, Any],
        comprador: dict[str, Any],
        imovel: dict[str, Any],
        valor: float,
        **kwargs,
    ) -> DocumentGeneration:
        """
        Generate deed draft.

        Args:
            tipo: Deed type (compra_venda, doacao, permuta)
            vendedor: Seller info
            comprador: Buyer info
            imovel: Property info (matricula, endereco, area)
            valor: Transaction value
            **kwargs: Additional parameters

        Returns:
            Generated deed draft
        """
        response = self._client.post(
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

    def generate_procuracao(
        self,
        outorgante: dict[str, Any],
        outorgado: dict[str, Any],
        poderes: list[str],
        prazo: int | None = None,
        **kwargs,
    ) -> DocumentGeneration:
        """
        Generate power of attorney draft.

        Args:
            outorgante: Grantor info
            outorgado: Grantee info
            poderes: List of powers granted
            prazo: Validity in days (None = indefinite)
            **kwargs: Additional parameters

        Returns:
            Generated power of attorney draft
        """
        response = self._client.post(
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

    def generate_ata(
        self,
        tipo: str,
        fatos: str,
        local: str,
        data_hora: str,
        interessados: list[dict[str, Any]],
        **kwargs,
    ) -> DocumentGeneration:
        """
        Generate notarial minutes.

        Args:
            tipo: Type (notarial, assembleia, constatacao)
            fatos: Description of facts
            local: Location
            data_hora: Date and time
            interessados: Interested parties
            **kwargs: Additional parameters

        Returns:
            Generated notarial minutes
        """
        response = self._client.post(
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

    def validate_cpf(
        self,
        cpf: str,
        **kwargs,
    ) -> ValidationResult:
        """
        Validate CPF and check biographical data.

        Args:
            cpf: CPF number
            **kwargs: Additional parameters

        Returns:
            Validation result
        """
        response = self._client.post(
            "/v1/cartorio/validate/cpf",
            json={"cpf": cpf, **kwargs},
        )

        return ValidationResult(
            is_valid=response.get("is_valid", False),
            message=response.get("message", ""),
            details=response.get("details", {}),
        )

    def check_restricoes(
        self,
        cpf: str | None = None,
        cnpj: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Check for restrictions (protests, lawsuits).

        Args:
            cpf: CPF number
            cnpj: CNPJ number
            **kwargs: Additional parameters

        Returns:
            Restrictions found
        """
        response = self._client.post(
            "/v1/cartorio/check/restricoes",
            json={"cpf": cpf, "cnpj": cnpj, **kwargs},
        )

        return response

    def search_imoveis(
        self,
        query: str,
        municipio: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """
        Semantic search in property records.

        Args:
            query: Search query
            municipio: Municipality filter
            **kwargs: Additional parameters

        Returns:
            List of matching properties
        """
        response = self._client.post(
            "/v1/cartorio/search/imoveis",
            json={
                "query": query,
                "municipio": municipio,
                **kwargs,
            },
        )

        return response.get("resultados", [])
