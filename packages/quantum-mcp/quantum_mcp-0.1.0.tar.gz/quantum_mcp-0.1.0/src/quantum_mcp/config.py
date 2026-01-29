# Description: Configuration management for Quantum MCP Server.
# Description: Handles environment variables and settings via pydantic-settings.
"""Configuration management for Quantum MCP Server."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure Quantum settings
    azure_quantum_workspace_id: str = Field(
        default="",
        description="Azure Quantum workspace ID",
    )
    azure_quantum_resource_group: str = Field(
        default="",
        description="Azure resource group name",
    )
    azure_quantum_subscription_id: str = Field(
        default="",
        description="Azure subscription ID",
    )
    azure_quantum_location: str = Field(
        default="eastus",
        description="Azure region",
    )

    # Azure Service Principal (for authentication)
    azure_client_id: str = Field(
        default="",
        description="Azure Service Principal client ID",
    )
    azure_tenant_id: str = Field(
        default="",
        description="Azure tenant ID",
    )
    azure_client_secret: str = Field(
        default="",
        description="Azure Service Principal client secret",
    )

    # Quantum execution settings
    default_backend: str = Field(
        default="ionq.simulator",
        description="Default quantum backend",
    )
    max_shots: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum shots per job",
    )

    # Budget settings
    budget_limit_usd: float = Field(
        default=10.0,
        ge=0.0,
        description="Maximum spend per session in USD",
    )

    # Server settings
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    cache_results: bool = Field(
        default=True,
        description="Cache quantum results",
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache TTL in seconds",
    )

    # PostgreSQL settings (HttpIngest metrics database)
    postgres_host: str = Field(
        default="",
        description="PostgreSQL host",
    )
    postgres_port: int = Field(
        default=5432,
        description="PostgreSQL port",
    )
    postgres_database: str = Field(
        default="",
        description="PostgreSQL database name",
    )
    postgres_user: str = Field(
        default="",
        description="PostgreSQL username",
    )
    postgres_password: str = Field(
        default="",
        description="PostgreSQL password (or leave empty for AAD auth)",
    )
    postgres_ssl_mode: str = Field(
        default="require",
        description="PostgreSQL SSL mode",
    )
    postgres_auth_method: str = Field(
        default="password",
        description="PostgreSQL auth method: 'password' or 'aad'",
    )

    # D-Wave settings
    dwave_api_token: str = Field(
        default="",
        description="D-Wave API token (or set DWAVE_API_TOKEN env var)",
    )
    dwave_solver: str = Field(
        default="Advantage_system6.4",
        description="D-Wave solver name",
    )

    @property
    def has_azure_credentials(self) -> bool:
        """Check if Azure credentials are configured."""
        return bool(
            self.azure_quantum_workspace_id
            and self.azure_quantum_resource_group
            and self.azure_quantum_subscription_id
        )

    @property
    def has_service_principal(self) -> bool:
        """Check if Service Principal credentials are configured."""
        return bool(
            self.azure_client_id
            and self.azure_tenant_id
            and self.azure_client_secret
        )

    @property
    def has_dwave_credentials(self) -> bool:
        """Check if D-Wave credentials are configured."""
        import os

        return bool(self.dwave_api_token or os.environ.get("DWAVE_API_TOKEN"))

    @property
    def has_postgres_credentials(self) -> bool:
        """Check if PostgreSQL credentials are configured."""
        has_connection_info = bool(
            self.postgres_host
            and self.postgres_database
            and self.postgres_user
        )
        # Password required for password auth, optional for AAD
        if self.postgres_auth_method == "aad":
            return has_connection_info
        return has_connection_info and bool(self.postgres_password)

    @property
    def postgres_dsn(self) -> str:
        """Build PostgreSQL connection string."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
            f"?sslmode={self.postgres_ssl_mode}"
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings singleton."""
    return Settings()
