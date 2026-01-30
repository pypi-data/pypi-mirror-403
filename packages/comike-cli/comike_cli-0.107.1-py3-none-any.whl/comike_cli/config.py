"""Configuration management."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration."""

    circle_ms_client_id: str
    circle_ms_client_secret: str
    openai_api_key: str
    token_file: Path = Path.home() / ".comike_cli" / "token.json"

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment variables."""
        env_file = Path.home() / ".comike_cli" / ".env"
        load_dotenv(env_file)

        client_id = os.getenv("CIRCLE_MS_CLIENT_ID", "")
        client_secret = os.getenv("CIRCLE_MS_CLIENT_SECRET", "")
        openai_key = os.getenv("OPENAI_API_KEY", "")

        if not client_id or not client_secret:
            raise ValueError("CIRCLE_MS_CLIENT_ID and CIRCLE_MS_CLIENT_SECRET must be set")

        if not openai_key:
            raise ValueError("OPENAI_API_KEY must be set")

        return cls(
            circle_ms_client_id=client_id,
            circle_ms_client_secret=client_secret,
            openai_api_key=openai_key,
        )
