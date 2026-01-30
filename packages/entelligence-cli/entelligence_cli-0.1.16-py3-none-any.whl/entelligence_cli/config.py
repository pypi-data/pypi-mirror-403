import json
import os
from pathlib import Path


# Optional: Load .env file if it exists (for local development)
# Only needed for developers testing against local backend
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv not installed - that's fine for normal users
    pass

# ==============================================================================
# GLOBAL BASE URL - Production default with local .env override
# ==============================================================================
# Production (default): "https://entelligence.ddbrief.com"
# Local Dev: Create .env file with ENTELLIGENCE_BASE_URL=http://localhost:8000
# ==============================================================================


def get_base_url() -> str:
    """Get base URL - checks .env file first, then falls back to production."""
    return os.getenv("ENTELLIGENCE_BASE_URL", "https://entelligence.ddbrief.com")


def get_full_endpoint() -> str:
    """Get full API endpoint URL."""
    return f"{get_base_url()}/generateReviewForCLI/"


class ConfigManager:
    """Manage EntelligenceAI CLI configuration."""

    def __init__(self):
        self.config_dir = Path.home() / ".entelligence"
        self.config_file = self.config_dir / "config.json"
        self.config_dir.mkdir(exist_ok=True)

    def load_config(self) -> dict:
        """Load configuration from file."""
        if self.config_file.exists():
            with open(self.config_file) as f:
                return json.load(f)
        return {}

    def save_config(self, config: dict):
        """Save configuration to file."""
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
        # Set secure permissions (owner read/write only)
        os.chmod(self.config_file, 0o600)

    def get_token(self):
        """Get stored API key."""
        # Check environment variable first
        if token := os.getenv("ENTELLIGENCE_API_KEY"):
            token = token.strip()
            return token if token else None

        # Check config file
        config = self.load_config()
        token = config.get("api_key")
        if isinstance(token, str):
            token = token.strip()
        return token or None

    def set_token(self, token: str):
        """Store API key."""
        config = self.load_config()
        config["api_key"] = token
        self.save_config(config)

    def get_org_uuid(self):
        """Get stored organization UUID."""
        # Check environment variable first
        if org_uuid := os.getenv("ENTELLIGENCE_ORG_UUID"):
            org_uuid = org_uuid.strip()
            return org_uuid if org_uuid else None

        # Check config file
        config = self.load_config()
        org_uuid = config.get("org_uuid")
        if isinstance(org_uuid, str):
            org_uuid = org_uuid.strip()
        return org_uuid or None

    def set_org_uuid(self, org_uuid: str):
        """Store organization UUID."""
        config = self.load_config()
        config["org_uuid"] = org_uuid
        self.save_config(config)

    def get_endpoint(self) -> str:
        """Get API endpoint (uses global BASE_URL with env var override)."""
        return get_full_endpoint()

    # ----- Optional GitHub token support (no hard-coded defaults) -----
    def get_github_token(self):
        """
        Resolve a GitHub token for backend use.
        Order: ENTELLIGENCE_GITHUB_TOKEN -> GITHUB_TOKEN -> GH_TOKEN -> config['github_token'].
        """
        token = (
            os.getenv("ENTELLIGENCE_GITHUB_TOKEN")
            or os.getenv("GITHUB_TOKEN")
            or os.getenv("GH_TOKEN")
            or self.load_config().get("github_token")
        )
        if isinstance(token, str):
            token = token.strip()
        return token or None

    def set_github_token(self, token: str):
        """Persist a GitHub token to config."""
        config = self.load_config()
        config["github_token"] = token
        self.save_config(config)

    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.get_token() is not None

    def clear_auth(self):
        """Clear authentication data."""
        config = self.load_config()
        config.pop("api_key", None)
        self.save_config(config)
