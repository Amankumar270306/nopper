"""Prompt pipeline — prepares standardized Message lists."""


from nopper.models.messages import Message, Role


class PromptBuilder:
    """Prepares Message lists from raw prompt inputs."""

    @staticmethod
    def prepare(
        prompt: str | list[str] | list[Message],
        system_prompt: str = "",
    ) -> list[Message]:
        """Convert a raw prompt input into a standardized list of Message objects."""
        messages: list[Message] = []

        if system_prompt:
            messages.append(Message(role=Role.SYSTEM, content=system_prompt))

        if isinstance(prompt, str):
            messages.append(Message(role=Role.USER, content=prompt))
        elif isinstance(prompt, list):
            if not prompt:
                raise ValueError("Prompt list cannot be empty.")

            if all(isinstance(m, str) for m in prompt):
                for m in prompt:
                    messages.append(Message(role=Role.USER, content=str(m)))
            elif all(isinstance(m, Message) for m in prompt):
                for m in prompt:
                    if isinstance(m, Message):
                        if m.role == Role.SYSTEM and system_prompt:
                            continue  # Ignore system prompt if already in list
                        messages.append(m)
            else:
                raise ValueError("Prompt list must contain strings or Message objects.")
        else:
            raise ValueError(
                "Prompt must be a string, a list of strings, or a list of Message objects."
            )

        return messages
