"""EntelligenceAI CLI - AI-powered code review from your terminal."""

import warnings

# Suppress noisy urllib3/OpenSSL compatibility warnings on macOS LibreSSL setups.
# This must happen BEFORE any imports that trigger urllib3 (requests, etc.).
warnings.filterwarnings(
    "ignore",
    message=r"urllib3 v2 only supports OpenSSL 1\.1\.1\+",
)  # pragma: no cover - environment-specific warning

from importlib.metadata import version


__version__ = version("entelligence-cli")

from .api_client import APIClient, APIConfig
from .cli import cli
from .config import ConfigManager
from .exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    EntelligenceError,
    GitError,
    ReviewError,
    ValidationError,
)
from .git_operations import GitOperations
from .ui import AnimatedLoader, InteractiveUI, TerminalUI


__all__ = [
    "cli",
    "GitOperations",
    "APIClient",
    "APIConfig",
    "ConfigManager",
    "TerminalUI",
    "InteractiveUI",
    "AnimatedLoader",
    "EntelligenceError",
    "AuthenticationError",
    "APIError",
    "GitError",
    "ValidationError",
    "ConfigurationError",
    "ReviewError",
    "__version__",
]
