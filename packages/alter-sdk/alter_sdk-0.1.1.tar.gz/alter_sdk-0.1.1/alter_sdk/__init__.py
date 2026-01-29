"""
Alter Vault Python SDK

OAuth token management with policy enforcement and automatic token injection.

Zero Token Exposure Architecture:
- Tokens are NEVER exposed to developers
- SDK handles all token operations internally
- Developers only see API results, never credentials
"""

from alter_sdk.client import AlterVault
from alter_sdk.exceptions import (
    AlterSDKError,
    ConnectionNotFoundError,
    NetworkError,
    PolicyViolationError,
    ProviderAPIError,
    TokenExpiredError,
    TokenRetrievalError,
)
from alter_sdk.models import TokenResponse
from alter_sdk.providers.enums import Provider

__version__ = "0.1.0"

__all__ = [
    "AlterVault",
    "Provider",
    "TokenResponse",
    "AlterSDKError",
    "TokenRetrievalError",
    "PolicyViolationError",
    "ConnectionNotFoundError",
    "TokenExpiredError",
    "ProviderAPIError",
    "NetworkError",
]
