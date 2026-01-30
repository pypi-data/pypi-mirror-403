"""Configuration management for Pulse Workflow MCP Server."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Configuration for the Pulse Workflow MCP Server.

    Environment variables:
        PULSE_API_URL - Base URL of the Pulse console API
        PULSE_API_KEY - Your access token (from Claude Connect modal)
        PULSE_APP_ID - Optional default workflow app ID (can be set per-tool call)

    Example:
        export PULSE_API_URL=https://your-pulse-instance.com
        export PULSE_API_KEY=your-access-token
        export PULSE_APP_ID=your-app-id  # Optional - can select at runtime
    """

    model_config = SettingsConfigDict(env_prefix="PULSE_")

    api_url: str = Field(default="http://localhost:5001", validation_alias="PULSE_API_URL")
    api_key: str = ""
    app_id: str = ""  # Optional - can be empty, selected at runtime
    workspace_id: str = ""
    timeout: float = 30.0

    def validate_config(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        if not self.api_key:
            errors.append("PULSE_API_KEY is required")
        # app_id is no longer required at startup
        return errors

    @property
    def console_api_base(self) -> str:
        """Get the console API base URL."""
        return f"{self.api_url}/console/api"

    def get_workflow_draft_url(self, app_id: str | None = None) -> str:
        """Get the workflow draft endpoint URL for a specific app."""
        target_app_id = app_id or self.app_id
        if not target_app_id:
            raise ValueError("No app_id provided and no default PULSE_APP_ID configured")
        return f"{self.console_api_base}/apps/{target_app_id}/workflows/draft"

    @property
    def workflow_draft_url(self) -> str:
        """Get the workflow draft endpoint URL using default app_id."""
        return self.get_workflow_draft_url()


# Global config instance - initialized when server starts
config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global config
    if config is None:
        config = Config()
    return config


def init_config() -> Config:
    """Initialize and validate configuration."""
    global config
    config = Config()
    errors = config.validate_config()
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    return config
