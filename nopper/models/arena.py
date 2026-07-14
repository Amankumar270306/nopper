"""Arena response model for multi-provider comparison."""


from pydantic import BaseModel

from nopper.models.responses import AIString, ChatResponse


class ArenaResponse(BaseModel):
    """Response from multiple models side by side."""
    model_config = {"arbitrary_types_allowed": True}
    responses: dict[str, ChatResponse | AIString | str]

    def __str__(self) -> str:
        parts = []
        for provider, response in self.responses.items():
            parts.append(f"{provider.capitalize()}")
            if isinstance(response, ChatResponse):
                parts.append(response.message.content or "")
            elif isinstance(response, str):
                parts.append(response)
            else:
                parts.append(str(response))
            parts.append("")
        return "\n".join(parts)
