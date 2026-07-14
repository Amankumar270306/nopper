"""Provider Registry — singleton mapping provider names to adapter classes.

Replaces the if/elif chain in the old ProviderFactory.
Adding a new provider requires only:
  1. Create an adapter class extending BaseProvider
  2. Call registry.register("name", AdapterClass)
"""


from nopper.provider.base import BaseProvider


class ProviderRegistry:
    """Singleton registry mapping provider names to adapter classes."""

    _instance: "ProviderRegistry | None" = None
    _providers: dict[str, type[BaseProvider]]

    def __new__(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._providers = {}
        return cls._instance

    def register(self, name: str, adapter_cls: type[BaseProvider]) -> None:
        """Register a provider adapter. Idempotent."""
        self._providers[name.lower()] = adapter_cls

    def get(self, name: str) -> type[BaseProvider]:
        """Look up a registered provider adapter by name."""
        key = name.lower()
        if key not in self._providers:
            available = ", ".join(sorted(self._providers.keys()))
            raise KeyError(
                f"Provider '{name}' is not registered. Available: [{available}]"
            )
        return self._providers[key]

    def has(self, name: str) -> bool:
        """Check if a provider is registered."""
        return name.lower() in self._providers

    def list(self) -> list[str]:
        """Return sorted list of all registered provider names."""
        return sorted(self._providers.keys())


# Module-level singleton for convenience
registry = ProviderRegistry()
