"""
NTLabs - Neural Thinkers LAB SDK
Python SDK for Neural Thinkers LAB AI Platform APIs.

Sync Usage:
    from ntlabs import NTLClient

    client = NTLClient(api_key="ntl_hipo_xxx")
    response = client.chat.complete(messages=[...])
    client.close()

Async Usage:
    from ntlabs import AsyncNTLClient

    async with AsyncNTLClient(api_key="ntl_hipo_xxx") as client:
        response = await client.chat.complete(messages=[...])
        company = await client.gov.cnpj("12.345.678/0001-90")

Resources available:
    - agents: AI Agents (Dédalo, Chiron, Themis, Hermes, Athena)
    - chat: LLM completions (Maritaca, Claude, GPT)
    - email: Email sending via Resend
    - transcribe: Audio transcription (Deepgram, Groq Whisper)
    - gov: Government APIs (CNPJ, CPF, CEP)
    - ibge: IBGE geographic/demographic data
    - bb: Banco do Brasil OAuth + PIX
    - saude: Medical AI (Hipocrates)
    - cartorio: Notary AI (Mercurius)
    - crc: CRC Nacional - Central de Registro Civil (Mercurius)
    - censec: CENSEC - Testamentos, Procurações, Escrituras (Mercurius)
    - enotariado: e-Notariado - Fluxo de Assinaturas Eletrônicas (Mercurius)
    - onr: ONR/SREI - Registro de Imóveis (Mercurius)
    - rnds: Brazilian National Health Network
    - billing: Usage and subscription

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from .async_client import AsyncNTLClient
from .client import NTLClient
from .exceptions import (
    APIError,
    AuthenticationError,
    InsufficientCreditsError,
    NTLError,
    RateLimitError,
    ServiceUnavailableError,
)

__version__ = "1.0.0"
__all__ = [
    "NTLClient",
    "AsyncNTLClient",
    "NTLError",
    "AuthenticationError",
    "RateLimitError",
    "InsufficientCreditsError",
    "APIError",
    "ServiceUnavailableError",
]
