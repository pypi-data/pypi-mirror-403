"""Custom exceptions for the Telescopius API client."""


class TelescopiusError(Exception):
    """Base exception for all Telescopius API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class TelescopiusAuthError(TelescopiusError):
    """Raised when authentication fails (401 Unauthorized)."""

    def __init__(self, message: str = "Invalid API key"):
        super().__init__(f"Unauthorized: {message}", status_code=401)


class TelescopiusBadRequestError(TelescopiusError):
    """Raised when the request is invalid (400 Bad Request)."""

    def __init__(self, message: str = "Invalid parameters"):
        super().__init__(f"Bad Request: {message}", status_code=400)


class TelescopiusRateLimitError(TelescopiusError):
    """Raised when rate limit is exceeded (429 Too Many Requests)."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(f"Too Many Requests: {message}", status_code=429)


class TelescopiusNotFoundError(TelescopiusError):
    """Raised when resource is not found (404 Not Found)."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(f"Not Found: {message}", status_code=404)


class TelescopiusServerError(TelescopiusError):
    """Raised when a server error occurs (5xx errors)."""

    def __init__(self, message: str = "Internal server error", status_code: int = 500):
        super().__init__(f"Server Error: {message}", status_code=status_code)


class TelescopiusNetworkError(TelescopiusError):
    """Raised when a network error occurs (no response from server)."""

    def __init__(self, message: str = "No response from API server"):
        super().__init__(message, status_code=None)
