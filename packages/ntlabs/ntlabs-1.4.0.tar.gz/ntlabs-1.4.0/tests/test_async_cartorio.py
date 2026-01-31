"""
NTLabs SDK - Async Cartório Resource Tests
Tests for the AsyncCartorioResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
import io
from unittest.mock import AsyncMock, MagicMock

from ntlabs.resources.async_cartorio import AsyncCartorioResource
from ntlabs.resources.cartorio import OCRResult, DocumentGeneration, ValidationResult


@pytest.mark.asyncio
class TestAsyncCartorioResource:
    """Tests for AsyncCartorioResource."""

    async def test_initialization(self):
        """AsyncCartorioResource initializes with client."""
        mock_client = AsyncMock()
        cartorio = AsyncCartorioResource(mock_client)
        assert cartorio._client == mock_client


@pytest.mark.asyncio
class TestAsyncCartorioOCR:
    """Tests for async OCR operations."""

    async def test_ocr_certidao(self, ocr_response):
        """OCR from birth certificate."""
        mock_client = AsyncMock()
        mock_client.post.return_value = ocr_response

        cartorio = AsyncCartorioResource(mock_client)
        image = io.BytesIO(b"fake_image_data")
        result = await cartorio.ocr_certidao(image, tipo="nascimento")

        assert isinstance(result, OCRResult)
        assert result.text == ocr_response["text"]
        assert result.structured_data == ocr_response["dados"]
        assert result.confidence == 0.95
        assert result.document_type == "certidao_nascimento"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/cartorio/ocr/certidao"

    async def test_ocr_certidao_casamento(self, ocr_response):
        """OCR from marriage certificate."""
        mock_client = AsyncMock()
        mock_client.post.return_value = ocr_response

        cartorio = AsyncCartorioResource(mock_client)
        image = io.BytesIO(b"fake_image_data")
        result = await cartorio.ocr_certidao(image, tipo="casamento")

        assert result.document_type == "certidao_casamento"

    async def test_ocr_escritura(self, ocr_response):
        """OCR from public deed."""
        mock_client = AsyncMock()
        mock_client.post.return_value = ocr_response

        cartorio = AsyncCartorioResource(mock_client)
        image = io.BytesIO(b"fake_image_data")
        result = await cartorio.ocr_escritura(image)

        assert isinstance(result, OCRResult)
        assert result.document_type == "escritura"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/cartorio/ocr/escritura"

    async def test_ocr_procuracao(self, ocr_response):
        """OCR from power of attorney."""
        mock_client = AsyncMock()
        mock_client.post.return_value = ocr_response

        cartorio = AsyncCartorioResource(mock_client)
        image = io.BytesIO(b"fake_image_data")
        result = await cartorio.ocr_procuracao(image)

        assert isinstance(result, OCRResult)
        assert result.document_type == "procuracao"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/cartorio/ocr/procuracao"


@pytest.mark.asyncio
class TestAsyncCartorioGeneration:
    """Tests for async document generation."""

    async def test_generate_escritura(self, document_generation_response):
        """Generate deed draft."""
        mock_client = AsyncMock()
        mock_client.post.return_value = document_generation_response

        cartorio = AsyncCartorioResource(mock_client)
        result = await cartorio.generate_escritura(
            tipo="compra_venda",
            vendedor={"nome": "João Silva", "cpf": "12345678909"},
            comprador={"nome": "Maria Souza", "cpf": "98765432100"},
            imovel={"endereco": "Rua Teste, 123", "matricula": "1234"},
            valor=250000.00,
        )

        assert isinstance(result, DocumentGeneration)
        assert result.content == document_generation_response["content"]
        assert result.document_type == "escritura_compra_venda"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/cartorio/generate/escritura"

    async def test_generate_escritura_with_kwargs(self, document_generation_response):
        """Generate deed with additional kwargs."""
        mock_client = AsyncMock()
        mock_client.post.return_value = document_generation_response

        cartorio = AsyncCartorioResource(mock_client)
        result = await cartorio.generate_escritura(
            tipo="compra_venda",
            vendedor={"nome": "João Silva", "cpf": "12345678909"},
            comprador={"nome": "Maria Souza", "cpf": "98765432100"},
            imovel={"endereco": "Rua Teste, 123"},
            valor=250000.00,
            corretor="Carlos Corretor",
            observacoes="Pagamento em 3 parcelas",
        )

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["corretor"] == "Carlos Corretor"
        assert call_args[1]["json"]["observacoes"] == "Pagamento em 3 parcelas"

    async def test_generate_procuracao(self, document_generation_response):
        """Generate power of attorney draft."""
        mock_client = AsyncMock()
        mock_client.post.return_value = document_generation_response

        cartorio = AsyncCartorioResource(mock_client)
        result = await cartorio.generate_procuracao(
            outorgante={"nome": "João Silva", "cpf": "12345678909"},
            outorgado={"nome": "Maria Souza", "cpf": "98765432100"},
            poderes=["administrar", "vender", "comprar"],
            prazo=365,
        )

        assert isinstance(result, DocumentGeneration)
        assert result.document_type == "procuracao"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/cartorio/generate/procuracao"
        assert call_args[1]["json"]["poderes"] == ["administrar", "vender", "comprar"]
        assert call_args[1]["json"]["prazo"] == 365

    async def test_generate_ata(self, document_generation_response):
        """Generate notarial minutes."""
        mock_client = AsyncMock()
        mock_client.post.return_value = document_generation_response

        cartorio = AsyncCartorioResource(mock_client)
        result = await cartorio.generate_ata(
            tipo="constatacao",
            fatos="Constato que o imóvel encontra-se abandonado...",
            local="Rua das Flores, 123 - Belo Horizonte/MG",
            data_hora="2026-01-27T14:00:00",
            interessados=[{"nome": "João Silva", "cpf": "12345678909"}],
        )

        assert isinstance(result, DocumentGeneration)
        assert result.document_type == "ata_constatacao"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/cartorio/generate/ata"

    async def test_generate_document(self, chat_response):
        """Generate document using LLM."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "choices": [{"message": {"content": "CONTRATO DE LOCAÇÃO..."}}]
        }

        cartorio = AsyncCartorioResource(mock_client)
        result = await cartorio.generate_document(
            document_type="contrato_locacao",
            data={"locador": "João", "locatario": "Maria", "valor": 2000},
        )

        assert result == "CONTRATO DE LOCAÇÃO..."
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/llm/completions"


@pytest.mark.asyncio
class TestAsyncCartorioValidation:
    """Tests for async validation operations."""

    async def test_validate_cpf_valid(self):
        """Validate valid CPF."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "is_valid": True,
            "message": "CPF válido",
            "details": {"nome": "João Silva", "nascimento": "1990-01-15"},
        }

        cartorio = AsyncCartorioResource(mock_client)
        result = await cartorio.validate_cpf("12345678909")

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.message == "CPF válido"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/cartorio/validate/cpf"

    async def test_validate_cpf_invalid(self):
        """Validate invalid CPF."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "is_valid": False,
            "message": "CPF inválido",
            "details": {},
        }

        cartorio = AsyncCartorioResource(mock_client)
        result = await cartorio.validate_cpf("11111111111")

        assert result.is_valid is False
        assert result.message == "CPF inválido"

    async def test_check_restricoes(self):
        """Check restrictions."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "protestos": [],
            "acoes": [],
            "cheques_sem_fundo": 0,
        }

        cartorio = AsyncCartorioResource(mock_client)
        result = await cartorio.check_restricoes(cpf="12345678909")

        assert "protestos" in result
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/cartorio/check/restricoes"

    async def test_search_imoveis(self):
        """Search properties."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "resultados": [
                {"matricula": "1234", "endereco": "Rua Teste, 123"},
            ]
        }

        cartorio = AsyncCartorioResource(mock_client)
        result = await cartorio.search_imoveis("apartamento 2 quartos", municipio="Belo Horizonte")

        assert len(result) == 1
        assert result[0]["matricula"] == "1234"
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/cartorio/search/imoveis"
        assert call_args[1]["json"]["query"] == "apartamento 2 quartos"
        assert call_args[1]["json"]["municipio"] == "Belo Horizonte"
