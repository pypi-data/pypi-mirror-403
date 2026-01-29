"""
Custom exceptions for the Cisco Security Cloud Control SDK
"""


class SCCError(Exception):
    """Base exception for all SCC API errors."""
    pass


class AuthenticationError(SCCError):
    """Raised when authentication fails (401)."""
    pass


class ForbiddenError(SCCError):
    """Raised when access is forbidden (403)."""
    pass


class NotFoundError(SCCError):
    """Raised when a resource is not found (404)."""
    pass


class ValidationError(SCCError):
    """Raised when request validation fails (400)."""
    pass


class ServerError(SCCError):
    """Raised when server error occurs (500)."""
    pass
