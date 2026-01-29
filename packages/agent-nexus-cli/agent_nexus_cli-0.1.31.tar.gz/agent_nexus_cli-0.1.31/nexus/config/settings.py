"""Settings Module.

Application settings with environment variable support.
"""

import os
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings Class.

    Provides application settings with environment variable support.

    Inherits:
        BaseSettings

    Attrs:
        model_config: SettingsConfigDict - Configuration for settings model.
        openai_api_key: str - OpenAI API key.
        openai_base_url: str | None - OpenAI base URL.
        model_name: str - LLM model name.
        temperature: float - LLM temperature.
        max_tokens: int - Maximum tokens for LLM.
        langsmith_api_key: str | None - LangSmith API key.
        langsmith_project: str - LangSmith project name.
        langsmith_tracing: bool - Enable LangSmith tracing.
        working_directory: Path - Working directory.
        nexus_dir: Path - Nexus configuration directory.
        plans_directory: Path - Plans directory for ARCHITECT mode.
        max_iterations: int - Maximum iterations.
        approval_required: bool - Require approval for tool execution.
        checkpoint_db: str - Checkpoint database path.
        log_level: str - Logging level.
        debug: bool - Debug mode.

    Methods:
        configure_langsmith(): Configure LangSmith tracing.
    """

    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(None, alias="OPENAI_BASE_URL")
    model_name: str = "gpt-4o"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = 4096

    langsmith_api_key: str | None = Field(None, alias="LANGSMITH_API_KEY")
    langsmith_project: str = "nexus"
    langsmith_tracing: bool = True

    working_directory: Path = Field(default_factory=Path.cwd)
    nexus_dir: Path = Field(default=Path(".nexus"))
    plans_directory: Path = Field(default=Path(".nexus/plans"))
    max_iterations: int = 50
    approval_required: bool = True

    checkpoint_db: str = "checkpoints.db"

    log_level: str = "INFO"
    debug: bool = False

    @property
    def mcp_config_path(self) -> Path:
        """Get MCP configuration file path.

        Returns:
            Path - Path to mcp_config.json
        """

        return self.nexus_dir / "mcp_config.json"

    def __init__(self, **data: Any) -> None:
        """Initialize Settings.

        Sets up absolute paths for checkpoint database.

        Args:
            **data: any - Configuration data.

        Returns:
            None

        Raises:
            None
        """

        super().__init__(**data)

        if not self.nexus_dir.is_absolute():
            self.nexus_dir = self.working_directory / self.nexus_dir

        db_dir = self.nexus_dir / "db"
        db_dir.mkdir(parents=True, exist_ok=True)

        rules_dir = self.nexus_dir / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        if not self.plans_directory.is_absolute():
            object.__setattr__(
                self,
                "plans_directory",
                self.working_directory / self.plans_directory,
            )
        self.plans_directory.mkdir(parents=True, exist_ok=True)

        if not self.checkpoint_db.startswith(("file:", "sqlite:", "/")):
            db_path = db_dir / self.checkpoint_db
            object.__setattr__(self, "checkpoint_db", str(db_path))

    def configure_langsmith(self) -> None:
        """Configure LangSmith Tracing.

        Sets environment variables for LangSmith tracing.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """

        if self.langsmith_api_key and self.langsmith_tracing:
            os.environ["LANGSMITH_API_KEY"] = self.langsmith_api_key
            os.environ["LANGSMITH_PROJECT"] = self.langsmith_project
            os.environ["LANGSMITH_TRACING"] = "true"


settings: Settings = Settings()
settings.configure_langsmith()


__all__: list[str] = ["Settings", "settings"]
