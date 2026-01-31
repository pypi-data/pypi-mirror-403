"""
NTLabs - Neural Thinkers LAB SDK
Main SDK Client.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

import os

import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    ServiceUnavailableError,
)
from .resources.agents import AgentsResource
from .resources.auth import AuthResource
from .resources.bb import BBResource
from .resources.billing import BillingResource
from .resources.cartorio import CartorioResource
from .resources.chat import ChatResource
from .resources.email import EmailResource
from .resources.gov import GovResource
from .resources.ibge import IBGEResource
from .resources.registros import (
    CENSECResource,
    CRCResource,
    ENotariadoResource,
    ONRResource,
)
from .resources.rnds import RNDSResource
from .resources.saude import SaudeResource
from .resources.transcribe import TranscribeResource

DEFAULT_BASE_URL = "https://neural-lab-production.up.railway.app"
DEFAULT_TIMEOUT = 60.0


def _get_base_url() -> str:
    """
    Get base URL with Railway Private Network support.

    Priority:
    1. NTL_INTERNAL_URL (Railway Private Network, ~1-5ms latency)
    2. NTL_API_URL (Public URL)
    3. Default production URL
    """
    return os.getenv("NTL_INTERNAL_URL") or os.getenv("NTL_API_URL") or DEFAULT_BASE_URL


class NTLClient:
    """
    NTLabs API Client.

    Usage:
        client = NTLClient(api_key="ntl_hipo_xxx")

        # Chat (LLM)
        response = client.chat.complete(messages=[...])

        # Email
        client.email.send(to=["user@example.com"], subject="Olá", html="<h1>Hi</h1>")

        # Transcription
        result = client.transcribe.audio("audio.mp3")

        # Government APIs
        company = client.gov.cnpj("12.345.678/0001-90")
        address = client.gov.cep("01310-100")

        # Saúde (Hipocrates)
        transcription = client.saude.transcribe(audio)
        soap = client.saude.generate_soap(transcription)

        # Cartório (Mercurius)
        data = client.cartorio.ocr(image)
        minuta = client.cartorio.generate_escritura(dados)

        # Billing
        usage = client.billing.get_usage()
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        source_system: str | None = None,
    ):
        """
        Initialize the NTLabs client.

        Args:
            api_key: API key (ntl_hipo_xxx or ntl_merc_xxx).
                    Falls back to NTL_API_KEY env var.
            base_url: Base URL for the API.
                     Falls back to NTL_API_URL env var.
            timeout: Request timeout in seconds.
            source_system: Source system identifier (hipocrates, mercurius).
        """
        self.api_key = api_key or os.getenv("NTL_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Set NTL_API_KEY or pass api_key parameter."
            )

        self.base_url = (base_url or _get_base_url()).rstrip("/")

        self.timeout = timeout
        self.source_system = source_system or self._detect_source_system()

        # HTTP client
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "X-API-Key": self.api_key,
                "X-Source-System": self.source_system,
                "User-Agent": f"ntlabs-python/1.0.0 ({self.source_system})",
            },
            timeout=timeout,
        )

        # Authentication
        self.auth = AuthResource(self)

        # AI Agents (unified access to all product agents)
        self.agents = AgentsResource(self)

        # Gateway Services
        self.chat = ChatResource(self)
        self.email = EmailResource(self)
        self.transcribe = TranscribeResource(self)
        self.gov = GovResource(self)
        self.bb = BBResource(self)
        self.ibge = IBGEResource(self)

        # Product-specific resources
        self.saude = SaudeResource(self)
        self.cartorio = CartorioResource(self)

        # RNDS (Brazilian National Health Data Network)
        self.rnds = RNDSResource(self)

        # CRC Nacional (Central de Informações do Registro Civil)
        self.crc = CRCResource(self)

        # CENSEC (Central Notarial de Serviços Eletrônicos Compartilhados)
        self.censec = CENSECResource(self)

        # e-Notariado (Fluxo de Assinaturas Eletrônicas)
        self.enotariado = ENotariadoResource(self)

        # ONR/SREI (Registro de Imóveis)
        self.onr = ONRResource(self)

        # Billing
        self.billing = BillingResource(self)

    def _detect_source_system(self) -> str:
        """Detect source system from API key prefix."""
        if self.api_key.startswith("ntl_hipo"):
            return "hipocrates"
        elif self.api_key.startswith("ntl_merc"):
            return "mercurius"
        elif self.api_key.startswith("ntl_poli"):
            return "polis"
        return "external"

    def request(
        self,
        method: str,
        endpoint: str,
        json: dict = None,
        data: dict = None,
        files: dict = None,
        params: dict = None,
        headers: dict = None,
    ) -> dict:
        """
        Make an API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /v1/chat/completions)
            json: JSON body
            data: Form data
            files: Files to upload
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            AuthenticationError: Invalid API key
            RateLimitError: Rate limit exceeded
            InsufficientCreditsError: Not enough credits
            APIError: General API error
        """
        try:
            response = self._client.request(
                method=method,
                url=endpoint,
                json=json,
                data=data,
                files=files,
                params=params,
                headers=headers,
            )

            # Handle errors
            if response.status_code == 401:
                raise AuthenticationError(
                    "Invalid API key",
                    status_code=401,
                    response=response.json() if response.content else {},
                )

            if response.status_code == 402:
                raise InsufficientCreditsError(
                    "Insufficient credits. Please add more credits.",
                    status_code=402,
                    response=response.json() if response.content else {},
                )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 60)
                raise RateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after}s",
                    status_code=429,
                    retry_after=int(retry_after),
                    response=response.json() if response.content else {},
                )

            if response.status_code == 503:
                raise ServiceUnavailableError(
                    "Service temporarily unavailable",
                    status_code=503,
                )

            if response.status_code >= 400:
                error_data = response.json() if response.content else {}
                raise APIError(
                    error_data.get("detail", f"API error: {response.status_code}"),
                    status_code=response.status_code,
                    response=error_data,
                )

            return response.json() if response.content else {}

        except httpx.TimeoutException as e:
            raise APIError(f"Request timeout after {self.timeout}s") from e
        except httpx.RequestError as e:
            raise APIError(f"Request failed: {e}") from e

    def get(self, endpoint: str, **kwargs) -> dict:
        """Make a GET request."""
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint: str, **kwargs) -> dict:
        """Make a POST request."""
        return self.request("POST", endpoint, **kwargs)

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
