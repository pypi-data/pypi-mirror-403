class XenfraError(Exception):
    """Base exception for all SDK errors."""

    pass


class AuthenticationError(XenfraError):
    """Raised for issues related to authentication."""

    pass


class XenfraAPIError(XenfraError):
    """Raised when the API returns a non-2xx status code."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")
