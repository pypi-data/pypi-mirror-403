"""Application settings using Pydantic BaseSettings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Anthropic API key for chat functionality
    anthropic_api_key: str | None = None

    # Default org ID (hardcoded for now, will be from auth token later)
    default_org_id: str = "noon"

    # GCP project for BigQuery queries (legacy - will be per-org)
    # Uses Application Default Credentials (ADC) - run `gcloud auth application-default login`
    gcp_project_id: str = "noon-datawarehouse"

    # MCP OAuth Configuration (for Claude.ai integration)
    # Create OAuth 2.0 credentials in Google Cloud Console:
    # 1. Go to APIs & Services > Credentials
    # 2. Create OAuth 2.0 Client ID (Web application)
    # 3. Add authorized redirect URI: <your-server-url>/mcp/auth/callback
    mcp_oauth_client_id: str | None = None
    mcp_oauth_client_secret: str | None = None
    mcp_server_base_url: str = "https://metricly.xyz/api"
    # JWT signing key for MCP tokens - MUST be persistent across server restarts
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    mcp_jwt_signing_key: str | None = None

    # Internal secret for Cloud Function -> Backend communication
    # Used by the scheduled reports executor to authenticate with the backend
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    internal_secret: str | None = None

    # Feature flags
    schedules_enabled: bool = False  # Scheduled reports (email delivery not implemented yet)


# Singleton instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
