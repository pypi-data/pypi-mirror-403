from __future__ import annotations
from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class OnDemandConfig:
    """
    Immutable configuration for OnDemandClient.

    Attributes:
        api_key: OnDemand API key (required)
        chat_base_url: Base URL for chat APIs
        media_base_url: Base URL for media APIs
        timeout: HTTP timeout in seconds
    """
    api_key: str
    chat_base_url: str = "https://api.on-demand.io/chat/v1"
    media_base_url: str = "https://api.on-demand.io/media/v1"
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "OnDemandConfig":
        """
        Create config from environment variables.

        Required:
            ONDEMAND_API_KEY
        """
        api_key = os.getenv("ONDEMAND_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ONDEMAND_API_KEY environment variable is not set"
            )

        return cls(api_key=api_key)
