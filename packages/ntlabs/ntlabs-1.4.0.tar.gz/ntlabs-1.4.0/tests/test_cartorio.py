"""
NTLabs SDK - Cartorio Resource Tests
Tests for the CartorioResource class (notary AI features).

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import io

from ntlabs.resources.cartorio import (
    CartorioResource,
    DocumentGeneration,
    OCRResult,
    ValidationResult,
)


class TestOCRResult:
    """Tests for OCRResult dataclass."""

    def test_create_result(self):
        """Create OCR result."""
        result = OCRResult(
            text="Nome: João Silva\nData: 01/01/2000",
            structured_data={"nome": "João Silva", "data_nascimento": "2000-01-01"},
            confidence=0.95,
            document_type="certidao_nascimento",
        )
        assert result.confidence == 0.95
        assert result.structured_data["nome"] == "João Silva"


class TestDocumentGeneration:
    """Tests for DocumentGeneration dataclass."""

    def test_create_document(self):
        """Create generated document."""
        doc = DocumentGeneration(
            content="ESCRITURA PÚBLICA DE COMPRA E VENDA...",
            document_type="escritura_compra_venda",
            metadata={"valor": 500000, "matricula": "12345"},
        )
        assert doc.document_type == "escritura_compra_venda"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_create_validation(self):
        """Create validation result."""
        result = ValidationResult(
            is_valid=True,
            message="CPF válido",
            details={"nome": "João Silva", "situacao": "Regular"},
        )
        assert result.is_valid is True


class TestCartorioResource:
    """Tests for CartorioResource."""

    def test_initialization(self, mock_client):
        """CartorioResource initializes with client."""
        cartorio = CartorioResource(mock_client)
        assert cartorio._client == mock_client

    def test_ocr_certidao_nascimento(self, mock_client, mock_response):
        """OCR birth certificate."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "text": "CERTIDÃO DE NASCIMENTO...",
                "dados": {
                    "nome": "João Silva",
                    "data_nascimento": "2000-01-15",
                    "nome_pai": "José Silva",
                    "nome_mae": "Maria Silva",
                },
                "confidence": 0.92,
            }
        )

        image = io.BytesIO(b"fake image")
        result = mock_client.cartorio.ocr_certidao(image, tipo="nascimento")

        assert isinstance(result, OCRResult)
        assert result.document_type == "certidao_nascimento"
        assert result.structured_data["nome"] == "João Silva"

    def test_ocr_certidao_casamento(self, mock_client, mock_response):
        """OCR marriage certificate."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "text": "CERTIDÃO DE CASAMENTO...",
                "dados": {
                    "conjuge1": "João Silva",
                    "conjuge2": "Maria Souza",
                    "data_casamento": "2020-05-20",
                },
                "confidence": 0.88,
            }
        )

        image = io.BytesIO(b"fake image")
        result = mock_client.cartorio.ocr_certidao(image, tipo="casamento")

        assert result.document_type == "certidao_casamento"

    def test_ocr_certidao_obito(self, mock_client, mock_response):
        """OCR death certificate."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "text": "CERTIDÃO DE ÓBITO...",
                "dados": {
                    "nome": "José Silva",
                    "data_obito": "2023-08-10",
                },
                "confidence": 0.90,
            }
        )

        image = io.BytesIO(b"fake image")
        result = mock_client.cartorio.ocr_certidao(image, tipo="obito")

        assert result.document_type == "certidao_obito"

    def test_ocr_escritura(self, mock_client, mock_response):
        """OCR public deed."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "text": "ESCRITURA PÚBLICA...",
                "dados": {
                    "tipo": "compra_venda",
                    "vendedor": "João Silva",
                    "comprador": "Maria Souza",
                    "valor": 500000.00,
                },
                "confidence": 0.85,
            }
        )

        image = io.BytesIO(b"fake image")
        result = mock_client.cartorio.ocr_escritura(image)

        assert isinstance(result, OCRResult)
        assert result.document_type == "escritura"

    def test_ocr_procuracao(self, mock_client, mock_response):
        """OCR power of attorney."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "text": "PROCURAÇÃO...",
                "dados": {
                    "outorgante": "João Silva",
                    "outorgado": "Pedro Santos",
                    "poderes": ["representar", "assinar"],
                },
                "confidence": 0.87,
            }
        )

        image = io.BytesIO(b"fake image")
        result = mock_client.cartorio.ocr_procuracao(image)

        assert isinstance(result, OCRResult)
        assert result.document_type == "procuracao"

    def test_generate_escritura(self, mock_client, mock_response):
        """Generate deed draft."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "content": "ESCRITURA PÚBLICA DE COMPRA E VENDA...",
                "metadata": {"matricula": "12345", "cartorio": "1º Ofício"},
            }
        )

        result = mock_client.cartorio.generate_escritura(
            tipo="compra_venda",
            vendedor={"nome": "João Silva", "cpf": "123.456.789-00"},
            comprador={"nome": "Maria Souza", "cpf": "987.654.321-00"},
            imovel={"matricula": "12345", "endereco": "Rua A, 100"},
            valor=500000.00,
        )

        assert isinstance(result, DocumentGeneration)
        assert result.document_type == "escritura_compra_venda"

    def test_generate_procuracao(self, mock_client, mock_response):
        """Generate power of attorney."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "content": "PROCURAÇÃO\n\nPelo presente instrumento...",
                "metadata": {"tipo": "publica"},
            }
        )

        result = mock_client.cartorio.generate_procuracao(
            outorgante={"nome": "João Silva", "cpf": "123.456.789-00"},
            outorgado={"nome": "Pedro Santos", "cpf": "111.222.333-44"},
            poderes=["representar em juízo", "movimentar conta bancária"],
            prazo=365,
        )

        assert isinstance(result, DocumentGeneration)
        assert result.document_type == "procuracao"

    def test_generate_procuracao_indefinite(self, mock_client, mock_response):
        """Generate indefinite power of attorney."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "content": "PROCURAÇÃO...",
                "metadata": {},
            }
        )

        result = mock_client.cartorio.generate_procuracao(
            outorgante={"nome": "João Silva"},
            outorgado={"nome": "Pedro Santos"},
            poderes=["vender imóveis"],
            prazo=None,  # Indefinite
        )

        assert isinstance(result, DocumentGeneration)

    def test_generate_ata(self, mock_client, mock_response):
        """Generate notarial minutes."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "content": "ATA NOTARIAL\n\nAos quinze dias do mês de janeiro...",
                "metadata": {"livro": "123", "folha": "456"},
            }
        )

        result = mock_client.cartorio.generate_ata(
            tipo="notarial",
            fatos="Constatação de obras irregulares",
            local="Rua A, 100, Centro",
            data_hora="2026-01-15T14:00:00",
            interessados=[
                {"nome": "João Silva", "qualificacao": "Proprietário"},
            ],
        )

        assert isinstance(result, DocumentGeneration)
        assert result.document_type == "ata_notarial"

    def test_generate_ata_assembleia(self, mock_client, mock_response):
        """Generate assembly minutes."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "content": "ATA DE ASSEMBLEIA...",
                "metadata": {},
            }
        )

        result = mock_client.cartorio.generate_ata(
            tipo="assembleia",
            fatos="Eleição de síndico",
            local="Salão de festas do condomínio",
            data_hora="2026-01-15T19:00:00",
            interessados=[
                {"nome": "Condomínio XYZ", "qualificacao": "Condomínio"},
            ],
        )

        assert result.document_type == "ata_assembleia"

    def test_validate_cpf(self, mock_client, mock_response):
        """Validate CPF."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "is_valid": True,
                "message": "CPF válido e regular",
                "details": {
                    "nome": "João Silva",
                    "situacao": "Regular",
                    "data_inscricao": "2000-01-01",
                },
            }
        )

        result = mock_client.cartorio.validate_cpf("123.456.789-00")

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.details["nome"] == "João Silva"

    def test_validate_cpf_invalid(self, mock_client, mock_response):
        """Validate invalid CPF."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "is_valid": False,
                "message": "CPF com situação irregular",
                "details": {"situacao": "Suspensa"},
            }
        )

        result = mock_client.cartorio.validate_cpf("111.111.111-11")

        assert result.is_valid is False

    def test_check_restricoes_cpf(self, mock_client, mock_response):
        """Check restrictions by CPF."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "protestos": [
                    {"valor": 1500.00, "cartorio": "1º Protesto", "data": "2023-05-10"}
                ],
                "acoes": [],
                "total": 1,
            }
        )

        result = mock_client.cartorio.check_restricoes(cpf="123.456.789-00")

        assert "protestos" in result
        assert len(result["protestos"]) == 1

    def test_check_restricoes_cnpj(self, mock_client, mock_response):
        """Check restrictions by CNPJ."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "protestos": [],
                "acoes": [],
                "total": 0,
            }
        )

        result = mock_client.cartorio.check_restricoes(cnpj="12.345.678/0001-90")

        assert result["total"] == 0

    def test_search_imoveis(self, mock_client, mock_response):
        """Search properties."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "resultados": [
                    {
                        "matricula": "12345",
                        "endereco": "Rua A, 100",
                        "proprietario": "João Silva",
                        "area": 250.00,
                    },
                    {
                        "matricula": "12346",
                        "endereco": "Rua A, 102",
                        "proprietario": "Maria Souza",
                        "area": 300.00,
                    },
                ]
            }
        )

        result = mock_client.cartorio.search_imoveis(
            query="Rua A Centro Belo Horizonte",
        )

        assert len(result) == 2
        assert result[0]["matricula"] == "12345"

    def test_search_imoveis_with_municipio(self, mock_client, mock_response):
        """Search properties filtered by municipality."""
        mock_client._mock_http.request.return_value = mock_response({"resultados": []})

        result = mock_client.cartorio.search_imoveis(
            query="apartamento 3 quartos",
            municipio="Belo Horizonte",
        )

        assert result == []

    def test_empty_response_handling(self, mock_client, mock_response):
        """Handle empty responses gracefully."""
        mock_client._mock_http.request.return_value = mock_response({})

        # OCR
        image = io.BytesIO(b"fake image")
        result = mock_client.cartorio.ocr_certidao(image)
        assert result.text == ""
        assert result.confidence == 0.0

        # Search
        result = mock_client.cartorio.search_imoveis(query="test")
        assert result == []

        # Validation
        result = mock_client.cartorio.validate_cpf("123")
        assert result.is_valid is False
        assert result.message == ""
