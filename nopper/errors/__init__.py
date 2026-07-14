"""Nopper exception hierarchy."""

from nopper.errors.exceptions import (
    ConfigurationError,
    NodeError,
    NodeNotFoundError,
    NopperError,
    ProviderError,
    RetryExhaustedError,
    WrapperNotFoundError,
)

# Backwards compatibility alias
MyAIError = NopperError

__all__ = [
    "ConfigurationError",
    "MyAIError",
    "NodeError",
    "NodeNotFoundError",
    "NopperError",
    "ProviderError",
    "RetryExhaustedError",
    "WrapperNotFoundError",
]
