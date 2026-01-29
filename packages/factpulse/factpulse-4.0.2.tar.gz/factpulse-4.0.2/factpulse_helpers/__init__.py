"""
FactPulse Helpers - Simplified client with built-in JWT authentication and polling.

This module provides:
- FactPulseClient: HTTP client with JWT auth and automatic polling
- FactPulseError: Base exception class

Example:
    >>> from factpulse_helpers import FactPulseClient
    >>>
    >>> client = FactPulseClient(
    ...     email="user@example.com",
    ...     password="password",
    ...     client_uid="..."
    ... )
    >>>
    >>> result = client.post("processing/invoices/generate", {"invoice_data": {...}})
"""
from .client import FactPulseClient, FactPulseError
from .exceptions import (
    FactPulseAuthError,
    FactPulsePollingTimeout,
    FactPulseValidationError,
    ValidationErrorDetail,
)

__all__ = [
    "FactPulseClient",
    "FactPulseError",
    "FactPulseAuthError",
    "FactPulsePollingTimeout",
    "FactPulseValidationError",
    "ValidationErrorDetail",
]
