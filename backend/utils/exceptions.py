"""
Custom exception hierarchy for the Brain application.
Provides structured error responses across all API endpoints.
"""


class BrainException(Exception):
    """Base exception for all Brain application errors."""

    def __init__(self, message: str, status_code: int = 500, detail: dict = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


class NotFoundError(BrainException):
    """Resource not found."""

    def __init__(self, resource: str, id: int):
        super().__init__(f"{resource} #{id} not found", 404)


class AuthenticationError(BrainException):
    """Authentication required or failed."""

    def __init__(self, message="Authentication required"):
        super().__init__(message, 401)


class AuthorizationError(BrainException):
    """User is not authorized to perform this action."""

    def __init__(self, message="You are not authorized to perform this action"):
        super().__init__(message, 403)


class ValidationError(BrainException):
    """Request validation failed."""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message, 422, {"errors": errors or []})


class RateLimitError(BrainException):
    """Rate limit exceeded."""

    def __init__(self):
        super().__init__("Rate limit exceeded. Please try again later.", 429)


class ConflictError(BrainException):
    """Resource conflict (e.g., duplicate)."""

    def __init__(self, message: str):
        super().__init__(message, 409)
