"""4Writers API - Python library for 4writers.net automation."""

__version__ = "0.6.0"

from .api.api import API
from .types.models import Order, File
from .exceptions import (
    FourWritersAPIError,
    AuthenticationError,
    SessionExpiredError,
    NetworkError,
    ParsingError,
    OrderNotFoundError,
    FileNotFoundError,
    RateLimitError,
)

__all__ = (
    "API",
    "Order",
    "File",
    "FourWritersAPIError",
    "AuthenticationError",
    "SessionExpiredError",
    "NetworkError",
    "ParsingError",
    "OrderNotFoundError",
    "FileNotFoundError",
    "RateLimitError",
    "__version__",
)
