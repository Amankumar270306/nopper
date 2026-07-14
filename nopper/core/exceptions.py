class NopperError(Exception):
    """Base exception for Nopper."""

# Alias for backwards compatibility
MyAIError = NopperError

class WrapperNotFoundError(NopperError):
    """Raised when a wrapper configuration cannot be found."""

class ProviderError(NopperError):
    """Raised when an AI provider fails."""
