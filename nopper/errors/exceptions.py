"""Nopper exception hierarchy.

Hierarchy:
    NopperError
    ├── ProviderError          — Provider adapter failures
    ├── NodeError              — Node execution failures
    │   └── NodeNotFoundError  — Node config not found on disk
    ├── WrapperNotFoundError   — Wrapper config not found
    ├── ConfigurationError     — Invalid configuration
    └── RetryExhaustedError    — All retry attempts failed
"""


class NopperError(Exception):
    """Base exception for all Nopper errors."""


class ProviderError(NopperError):
    """Raised when an AI provider adapter fails."""


class NodeError(NopperError):
    """Raised when a node execution fails."""


class NodeNotFoundError(NodeError):
    """Raised when a node configuration cannot be found."""


class WrapperNotFoundError(NopperError):
    """Raised when a wrapper configuration cannot be found."""


class ConfigurationError(NopperError):
    """Raised when configuration is invalid or missing."""


class RetryExhaustedError(NopperError):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str, last_exception: Exception | None = None):
        super().__init__(message)
        self.last_exception = last_exception
