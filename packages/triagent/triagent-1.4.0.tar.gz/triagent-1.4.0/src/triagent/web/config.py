"""Web configuration for Triagent."""

import os
from dataclasses import dataclass


@dataclass
class WebConfig:
    """Web UI configuration from environment variables."""

    # Azure AD OAuth
    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    allowed_ad_group_id: str | None = None

    # API Authentication
    triagent_api_key: str = ""

    # CORS
    cors_origins: str = "*"

    # Session Pool (Azure Container Apps Dynamic Sessions)
    session_pool_endpoint: str = ""
    local_mode: bool = False
    local_sessions_url: str = "http://localhost:8082"

    def __init__(self) -> None:
        """Load configuration from environment variables."""
        self.azure_tenant_id = os.getenv("AZURE_TENANT_ID", "")
        # Support both naming conventions: AZURE_CLIENT_ID and OAUTH_AZURE_AD_CLIENT_ID
        self.azure_client_id = os.getenv("AZURE_CLIENT_ID") or os.getenv(
            "OAUTH_AZURE_AD_CLIENT_ID", ""
        )
        self.azure_client_secret = os.getenv("AZURE_CLIENT_SECRET") or os.getenv(
            "OAUTH_AZURE_AD_CLIENT_SECRET", ""
        )
        self.allowed_ad_group_id = os.getenv("ALLOWED_AD_GROUP_ID")

        # API Authentication
        self.triagent_api_key = os.getenv("TRIAGENT_API_KEY", "")

        # CORS configuration
        self.cors_origins = os.getenv("CORS_ORIGINS", "*")

        # Local mode vs Azure mode
        self.local_mode = os.getenv("TRIAGENT_LOCAL_MODE", "false").lower() == "true"
        self.local_sessions_url = os.getenv(
            "TRIAGENT_LOCAL_SESSIONS_URL", "http://localhost:8082"
        )

        # Session Pool endpoint (Azure Container Apps Dynamic Sessions)
        self.session_pool_endpoint = os.getenv("TRIAGENT_SESSION_POOL_ENDPOINT", "")
