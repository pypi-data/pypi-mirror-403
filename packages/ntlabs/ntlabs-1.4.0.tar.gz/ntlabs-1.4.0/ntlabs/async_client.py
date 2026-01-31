"""
NTLabs - Neural Thinkers LAB SDK
Async SDK Client.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
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


class AsyncNTLClient:
    """
    Async NTLabs API Client.

    Usage:
        async with AsyncNTLClient(api_key="ntl_hipo_xxx") as client:
            # Chat (LLM)
            response = await client.chat.complete(messages=[...])

            # Email
            await client.email.send(to=["user@example.com"], subject="Olá", html="<h1>Hi</h1>")

            # Transcription
            result = await client.transcribe.audio("audio.mp3")

            # Government APIs
            company = await client.gov.cnpj("12.345.678/0001-90")
            address = await client.gov.cep("01310-100")

            # Saúde (Hipocrates)
            soap = await client.saude.generate_soap(transcription)

            # Cartório (Mercurius)
            minuta = await client.cartorio.generate_escritura(dados)

            # Billing
            usage = await client.billing.get_usage()
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        source_system: str | None = None,
    ):
        """
        Initialize the async NTLabs client.

        Args:
            api_key: API key (ntl_hipo_xxx or ntl_merc_xxx).
                    Falls back to NTL_API_KEY env var.
            base_url: Base URL for the API.
                     Falls back to NTL_API_URL env var.
            timeout: Request timeout in seconds.
            source_system: Source system identifier (hipocrates, mercurius, polis).
        """
        self.api_key = api_key or os.getenv("NTL_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Set NTL_API_KEY or pass api_key parameter."
            )

        self.base_url = (base_url or _get_base_url()).rstrip("/")
        self.timeout = timeout
        self.source_system = source_system or self._detect_source_system()

        # Lazy-initialized async HTTP client
        self._client: httpx.AsyncClient | None = None

        # Lazy-initialized resources
        self._agents = None
        self._auth = None
        self._chat = None
        self._email = None
        self._transcribe = None
        self._gov = None
        self._bb = None
        self._ibge = None
        self._saude = None
        self._cartorio = None
        self._rnds = None
        self._crc = None
        self._censec = None
        self._enotariado = None
        self._onr = None
        self._billing = None

    def _detect_source_system(self) -> str:
        """Detect source system from API key prefix."""
        if self.api_key.startswith("ntl_hipo"):
            return "hipocrates"
        elif self.api_key.startswith("ntl_merc"):
            return "mercurius"
        elif self.api_key.startswith("ntl_poli"):
            return "polis"
        return "external"

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-API-Key": self.api_key,
                    "X-Source-System": self.source_system,
                    "User-Agent": f"ntlabs-python/1.0.0 ({self.source_system})",
                },
                timeout=self.timeout,
            )
        return self._client

    # =========================================================================
    # Lazy Resource Properties
    # =========================================================================

    @property
    def agents(self):
        """AI Agents resource (unified access to all product agents)."""
        if self._agents is None:
            from .resources.async_agents import AsyncAgentsResource

            self._agents = AsyncAgentsResource(self)
        return self._agents

    @property
    def auth(self):
        """Authentication resource."""
        if self._auth is None:
            from .resources.async_auth import AsyncAuthResource

            self._auth = AsyncAuthResource(self)
        return self._auth

    @property
    def chat(self):
        """Chat/LLM resource."""
        if self._chat is None:
            from .resources.async_chat import AsyncChatResource

            self._chat = AsyncChatResource(self)
        return self._chat

    @property
    def email(self):
        """Email resource."""
        if self._email is None:
            from .resources.async_email import AsyncEmailResource

            self._email = AsyncEmailResource(self)
        return self._email

    @property
    def transcribe(self):
        """Transcription resource."""
        if self._transcribe is None:
            from .resources.async_transcribe import AsyncTranscribeResource

            self._transcribe = AsyncTranscribeResource(self)
        return self._transcribe

    @property
    def gov(self):
        """Government APIs resource."""
        if self._gov is None:
            from .resources.async_gov import AsyncGovResource

            self._gov = AsyncGovResource(self)
        return self._gov

    @property
    def bb(self):
        """Banco do Brasil resource."""
        if self._bb is None:
            from .resources.async_bb import AsyncBBResource

            self._bb = AsyncBBResource(self)
        return self._bb

    @property
    def ibge(self):
        """IBGE resource."""
        if self._ibge is None:
            from .resources.async_ibge import AsyncIBGEResource

            self._ibge = AsyncIBGEResource(self)
        return self._ibge

    @property
    def saude(self):
        """Saúde (Hipocrates) resource."""
        if self._saude is None:
            from .resources.async_saude import AsyncSaudeResource

            self._saude = AsyncSaudeResource(self)
        return self._saude

    @property
    def cartorio(self):
        """Cartório (Mercurius) resource."""
        if self._cartorio is None:
            from .resources.async_cartorio import AsyncCartorioResource

            self._cartorio = AsyncCartorioResource(self)
        return self._cartorio

    @property
    def rnds(self):
        """RNDS resource."""
        if self._rnds is None:
            from .resources.async_rnds import AsyncRNDSResource

            self._rnds = AsyncRNDSResource(self)
        return self._rnds

    @property
    def crc(self):
        """CRC Nacional resource."""
        if self._crc is None:
            from .resources.registros import AsyncCRCResource

            self._crc = AsyncCRCResource(self)
        return self._crc

    @property
    def censec(self):
        """CENSEC resource."""
        if self._censec is None:
            from .resources.registros import AsyncCENSECResource

            self._censec = AsyncCENSECResource(self)
        return self._censec

    @property
    def enotariado(self):
        """e-Notariado resource."""
        if self._enotariado is None:
            from .resources.registros import AsyncENotariadoResource

            self._enotariado = AsyncENotariadoResource(self)
        return self._enotariado

    @property
    def onr(self):
        """ONR/SREI resource."""
        if self._onr is None:
            from .resources.registros import AsyncONRResource

            self._onr = AsyncONRResource(self)
        return self._onr

    @property
    def billing(self):
        """Billing resource."""
        if self._billing is None:
            from .resources.async_billing import AsyncBillingResource

            self._billing = AsyncBillingResource(self)
        return self._billing

    # =========================================================================
    # HTTP Methods
    # =========================================================================

    async def request(
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
        Make an async API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., /v1/chat/completions)
            json: JSON body
            data: Form data
            files: Files to upload
            params: Query parameters
            headers: Additional headers

        Returns:
            Response JSON

        Raises:
            AuthenticationError: Invalid API key
            RateLimitError: Rate limit exceeded
            InsufficientCreditsError: Not enough credits
            APIError: General API error
        """
        client = self._get_client()

        try:
            response = await client.request(
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

    async def get(self, endpoint: str, **kwargs) -> dict:
        """Make an async GET request."""
        return await self.request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> dict:
        """Make an async POST request."""
        return await self.request("POST", endpoint, **kwargs)

    async def close(self):
        """Close the async HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
