"""Custom exception classes for Rail Engine SDK."""

from typing import Optional


class RailtownError(Exception):
    """Base exception for all Rail Engine errors."""

    def __init__(
        self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None
    ):
        """
        Initialize RailtownError.

        Args:
            message: Error message
            status_code: HTTP status code (if applicable)
            response_text: Response text from the API (if applicable)
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_text = response_text


class RailtownBadRequestError(RailtownError):
    """Exception raised for 400 Bad Request errors."""

    pass


class RailtownUnauthorizedError(RailtownError):
    """Exception raised for 401 Unauthorized errors."""

    pass


class RailtownNotFoundError(RailtownError):
    """Exception raised for 404 Not Found errors."""

    pass


class RailtownConflictError(RailtownError):
    """Exception raised for 409 Conflict errors."""

    pass


class RailtownServerError(RailtownError):
    """Exception raised for 5xx Server errors."""

    pass
