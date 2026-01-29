"""
gq-sdk - Python SDK for GoQuant Trading Platform

For documentation and usage examples, visit: https://docs.goquant.io
"""

VERSION = "0.1.3"
__version__ = VERSION

# Main client
from .unified_trading import Client

# Exceptions
from .exceptions import (
    GQPYError,
    AuthenticationError,
    FailedRequestError,
    InvalidConfigurationError,
    InvalidRequestError,
    NotAuthenticatedError,
    ExchangeLoginError,
)

# Endpoint enums (for advanced usage)
from .auth import Auth
from .credentials import Credentials
from .trade import Trade
from .exchange import Exchange

__all__ = [
    # Version
    "VERSION",
    "__version__",
    # Main client
    "Client",
    # Exceptions
    "GQPYError",
    "AuthenticationError",
    "FailedRequestError",
    "InvalidConfigurationError",
    "InvalidRequestError",
    "NotAuthenticatedError",
    "ExchangeLoginError",
    # Endpoint enums
    "Auth",
    "Credentials",
    "Trade",
    "Exchange",
]
