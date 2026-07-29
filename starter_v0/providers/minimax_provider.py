from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


class MiniMaxProvider(OpenAIProvider):
    """MiniMax uses an OpenAI-compatible Chat Completions surface."""

    def __init__(self) -> None:
        super().__init__(
            api_key_env="MINIMAX_API_KEY",
            base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1"),
            default_model="MiniMax-Text-01",
        )
