"""Middleware pipeline for request/response transformations."""

from abc import ABC

from nopper.models.requests import ExecutionRequest
from nopper.models.responses import ChatResponse


class Middleware(ABC):
    """Abstract base class for custom middleware."""

    def before_request(self, request: ExecutionRequest) -> ExecutionRequest:
        """Modify or inspect execution request before sending to Node."""
        return request

    def after_response(self, response: ChatResponse) -> ChatResponse:
        """Modify or inspect chat response after receiving from Node."""
        return response


class MiddlewarePipeline:
    """Chain of middleware executed sequentially."""

    def __init__(self) -> None:
        self._middlewares: list[Middleware] = []

    def use(self, middleware: Middleware) -> None:
        """Add a middleware to the end of the pipeline."""
        self._middlewares.append(middleware)

    def run_before(self, request: ExecutionRequest) -> ExecutionRequest:
        """Pass request through all before_request hooks."""
        current = request
        for mw in self._middlewares:
            current = mw.before_request(current)
        return current

    def run_after(self, response: ChatResponse) -> ChatResponse:
        """Pass response through all after_response hooks."""
        current = response
        for mw in self._middlewares:
            current = mw.after_response(current)
        return current
