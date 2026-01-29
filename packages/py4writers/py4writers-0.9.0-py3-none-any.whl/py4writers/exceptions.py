"""Custom exceptions for 4Writers API."""


class FourWritersAPIError(Exception):
    """Base exception for all 4Writers API errors."""
    pass


class AuthenticationError(FourWritersAPIError):
    """Raised when authentication fails."""
    pass


class SessionExpiredError(FourWritersAPIError):
    """Raised when session has expired and needs re-authentication."""
    pass


class NetworkError(FourWritersAPIError):
    """Raised when network request fails."""
    pass


class ParsingError(FourWritersAPIError):
    """Raised when HTML parsing fails."""
    pass


class OrderNotFoundError(FourWritersAPIError):
    """Raised when order is not found."""
    pass


class FileNotFoundError(FourWritersAPIError):
    """Raised when file is not found."""
    pass


class RateLimitError(FourWritersAPIError):
    """Raised when rate limit is exceeded."""
    pass
