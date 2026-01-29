"""Configuration management for Colibri CLI."""

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for Colibri CLI."""

    api_url: str
    api_key: str
    project_id: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Returns:
            Config instance

        Raises:
            ValueError: If required environment variables are missing
        """
        required_env = {
            "COLIBRI_API_URL": os.getenv("COLIBRI_API_URL"),
            "COLIBRI_API_KEY": os.getenv("COLIBRI_API_KEY"),
            "COLIBRI_PROJECT_ID": os.getenv("COLIBRI_PROJECT_ID"),
        }

        missing = [name for name, value in required_env.items() if not value]

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        api_url = required_env["COLIBRI_API_URL"]
        api_key = required_env["COLIBRI_API_KEY"]
        project_id = required_env["COLIBRI_PROJECT_ID"]

        return cls(
            api_url=api_url,
            api_key=api_key,
            project_id=project_id,
        )




