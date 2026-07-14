"""Provider Factory — creates provider adapter instances using the Registry."""

from typing import Any

import nopper.provider.adapters  # noqa: F401
from nopper.provider.base import BaseProvider
from nopper.provider.registry import registry


class ProviderFactory:
    """Creates provider adapter instances using the ProviderRegistry.

    The Node calls this factory to obtain a ready-to-use provider
    adapter. The factory looks up the adapter class in the registry
    and injects configuration.
    """

    @staticmethod
    def create(
        provider_name: str,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> BaseProvider:
        """Create a provider adapter instance.

        Args:
            provider_name: Registered provider name (e.g. "openai").
            api_key: API key for authentication.
            model: Default model to use.
            base_url: Override base URL.
            timeout: Request timeout in seconds.
            **kwargs: Additional provider-specific parameters.

        Returns:
            A ready-to-use BaseProvider instance.

        Raises:
            KeyError: If the provider is not registered.
        """
        adapter_cls = registry.get(provider_name)
        return adapter_cls(
            api_key=api_key,
            model=model,
            base_url=base_url,
            timeout=timeout,
            **kwargs,
        )
