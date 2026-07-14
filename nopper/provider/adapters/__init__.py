"""Auto-import all provider adapters to trigger self-registration."""

from nopper.provider.adapters import (  # noqa: F401
    anthropic,
    gemini,
    groq,
    local,
    mistral,
    ollama,
    openai,
    openrouter,
    together,
)
