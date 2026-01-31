"""
Neural LAB - AI Solutions Platform
SDK Resources.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from .auth import AuthResource
from .bb import BBResource
from .billing import (
    BillingResource,
    Credits,
    PixCharge,
    PixStatus,
    ProductPlan,
    ProductSubscription,
    ProductUsage,
    Subscription,
    Usage,
)
from .cartorio import CartorioResource
from .chat import ChatResource
from .email import EmailResource
from .gov import GovResource
from .ibge import IBGEResource
from .registros import (
    AsyncCENSECResource,
    AsyncCRCResource,
    AsyncENotariadoResource,
    AsyncONRResource,
    CENSECResource,
    CRCResource,
    ENotariadoResource,
    ONRResource,
)
from .rnds import RNDSResource
from .saude import SaudeResource
from .transcribe import TranscribeResource

__all__ = [
    # Core Resources
    "AuthResource",
    "ChatResource",
    "EmailResource",
    "TranscribeResource",
    "GovResource",
    "BBResource",
    "SaudeResource",
    "CartorioResource",
    "BillingResource",
    "RNDSResource",
    "IBGEResource",
    # Billing Types
    "Credits",
    "PixCharge",
    "PixStatus",
    "ProductPlan",
    "ProductSubscription",
    "ProductUsage",
    "Subscription",
    "Usage",
    # Registros (Sync)
    "CRCResource",
    "CENSECResource",
    "ENotariadoResource",
    "ONRResource",
    # Registros (Async)
    "AsyncCRCResource",
    "AsyncCENSECResource",
    "AsyncENotariadoResource",
    "AsyncONRResource",
]
