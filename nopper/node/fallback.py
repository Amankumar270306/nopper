"""FallbackNode — executes requests across a fallback chain of providers/models."""

import logging
from collections.abc import AsyncIterator, Iterator
from typing import Any

from nopper.errors.exceptions import NodeError
from nopper.models.requests import ExecutionRequest
from nopper.models.responses import ChatResponse, StreamChunk
from nopper.node.base import Node
from nopper.provider.factory import ProviderFactory

logger = logging.getLogger(__name__)


class FallbackNode(Node):
    """FallbackNode attempts execution on primary provider, falling back on failure."""

    def _get_api_key(self, provider_name: str) -> str | None:
        """Resolve API key for a specific provider in fallback chain."""
        if provider_name == self.config.provider:
            return self.config.api_key
        from nopper.config.loader import load_config
        settings = load_config()
        return settings.api_keys.get(provider_name)

    def _get_providers(self) -> list[tuple[str, str]]:
        """Return list of (provider, model) pairs starting with primary."""
        pairs = [(self.config.provider, self.config.model)]
        for fallback_str in self.config.fallbacks:
            if ":" in fallback_str:
                p, m = fallback_str.split(":", 1)
                pairs.append((p, m))
            else:
                pairs.append((fallback_str, self.config.model))
        return pairs

    def execute(self, request: ExecutionRequest) -> ChatResponse:
        providers = self._get_providers()
        last_error: Exception | None = None
        effective_timeout = request.timeout if request.timeout is not None else self.config.timeout

        for i, (provider_name, model_name) in enumerate(providers):
            try:
                provider = ProviderFactory.create(
                    provider_name=provider_name,
                    api_key=self._get_api_key(provider_name),
                    model=model_name,
                    base_url=self.config.base_url,
                    timeout=effective_timeout,
                    **self.config.parameters,
                )
                response = provider.chat(
                    messages=request.messages,
                    model=model_name,
                    tools=request.tools,
                    tool_choice=request.tool_choice,
                    response_model=request.response_model,
                    timeout=effective_timeout,
                    **request.kwargs,
                )
                response.timeout = effective_timeout
                return response
            except Exception as e:
                last_error = e
                if i < len(providers) - 1:
                    logger.warning(
                        f"Node '{self.name}' fallback {i+1}/{len(providers)-1}: "
                        f"{provider_name}:{model_name} failed with {e}. Trying next."
                    )
                else:
                    raise NodeError(
                        f"Node '{self.name}' all fallbacks exhausted. Last error: {e}"
                    ) from e

        raise NodeError(f"Node '{self.name}' failed with no providers available.")

    def execute_stream(self, request: ExecutionRequest) -> Iterator[StreamChunk]:
        providers = self._get_providers()
        last_error: Exception | None = None
        effective_timeout = request.timeout if request.timeout is not None else self.config.timeout

        for i, (provider_name, model_name) in enumerate(providers):
            try:
                provider = ProviderFactory.create(
                    provider_name=provider_name,
                    api_key=self._get_api_key(provider_name),
                    model=model_name,
                    base_url=self.config.base_url,
                    timeout=effective_timeout,
                    **self.config.parameters,
                )
                yield from provider.stream(
                    messages=request.messages,
                    model=model_name,
                    tools=request.tools,
                    tool_choice=request.tool_choice,
                    response_model=request.response_model,
                    timeout=effective_timeout,
                    **request.kwargs,
                )
                return
            except Exception as e:
                last_error = e
                if i < len(providers) - 1:
                    logger.warning(
                        f"Node '{self.name}' stream fallback {i+1}/{len(providers)-1}: "
                        f"{provider_name}:{model_name} failed with {e}. Trying next."
                    )
                else:
                    raise NodeError(
                        f"Node '{self.name}' streaming all fallbacks exhausted: {e}"
                    ) from e

        raise NodeError(f"Node '{self.name}' failed with no providers available.")

    async def aexecute(self, request: ExecutionRequest) -> ChatResponse:
        providers = self._get_providers()
        last_error: Exception | None = None
        effective_timeout = request.timeout if request.timeout is not None else self.config.timeout

        for i, (provider_name, model_name) in enumerate(providers):
            try:
                provider = ProviderFactory.create(
                    provider_name=provider_name,
                    api_key=self._get_api_key(provider_name),
                    model=model_name,
                    base_url=self.config.base_url,
                    timeout=effective_timeout,
                    **self.config.parameters,
                )
                response = await provider.achat(
                    messages=request.messages,
                    model=model_name,
                    tools=request.tools,
                    tool_choice=request.tool_choice,
                    response_model=request.response_model,
                    timeout=effective_timeout,
                    **request.kwargs,
                )
                response.timeout = effective_timeout
                return response
            except Exception as e:
                last_error = e
                if i < len(providers) - 1:
                    logger.warning(
                        f"Node '{self.name}' async fallback {i+1}/{len(providers)-1}: "
                        f"{provider_name}:{model_name} failed with {e}. Trying next."
                    )
                else:
                    raise NodeError(
                        f"Node '{self.name}' all async fallbacks exhausted: {e}"
                    ) from e

        raise NodeError(f"Node '{self.name}' failed with no providers available.")

    async def aexecute_stream(self, request: ExecutionRequest) -> AsyncIterator[StreamChunk]:
        providers = self._get_providers()
        last_error: Exception | None = None
        effective_timeout = request.timeout if request.timeout is not None else self.config.timeout

        for i, (provider_name, model_name) in enumerate(providers):
            try:
                provider = ProviderFactory.create(
                    provider_name=provider_name,
                    api_key=self._get_api_key(provider_name),
                    model=model_name,
                    base_url=self.config.base_url,
                    timeout=effective_timeout,
                    **self.config.parameters,
                )
                async for chunk in provider.astream(
                    messages=request.messages,
                    model=model_name,
                    tools=request.tools,
                    tool_choice=request.tool_choice,
                    response_model=request.response_model,
                    timeout=effective_timeout,
                    **request.kwargs,
                ):
                    yield chunk
                return
            except Exception as e:
                last_error = e
                if i < len(providers) - 1:
                    logger.warning(
                        f"Node '{self.name}' async stream fallback {i+1}/{len(providers)-1}: "
                        f"{provider_name}:{model_name} failed with {e}. Trying next."
                    )
                else:
                    raise NodeError(
                        f"Node '{self.name}' async streaming fallbacks exhausted: {e}"
                    ) from e

        raise NodeError(f"Node '{self.name}' failed with no providers available.")

    def execute_embed(self, text: str, model: str | None = None, **kwargs: Any) -> list[float]:
        providers = self._get_providers()
        for provider_name, model_name in providers:
            try:
                provider = ProviderFactory.create(
                    provider_name=provider_name,
                    api_key=self._get_api_key(provider_name),
                    model=model_name,
                    base_url=self.config.base_url,
                    timeout=self.config.timeout,
                    **self.config.parameters,
                )
                return provider.embed(text, model=model or model_name, **kwargs)
            except Exception:
                continue
        raise NodeError(f"Node '{self.name}' embed failed across all fallbacks.")

    def list_models(self) -> list[str]:
        provider = ProviderFactory.create(
            provider_name=self.config.provider,
            api_key=self.config.api_key,
            model=self.config.model,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            **self.config.parameters,
        )
        return provider.models()
