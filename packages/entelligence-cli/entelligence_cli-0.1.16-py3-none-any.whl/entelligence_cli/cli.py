"""EntelligenceAI CLI - AI-powered code review from your terminal."""

import warnings

# Suppress noisy urllib3/OpenSSL compatibility warnings on macOS LibreSSL setups.
# This must happen BEFORE any imports that trigger urllib3 (requests, etc.).
warnings.filterwarnings(
    "ignore",
    message=r"urllib3 v2 only supports OpenSSL 1\.1\.1\+",
)  # pragma: no cover - environment-specific warning

import click
from contextlib import suppress

from . import __version__
from .api_client import APIClient, APIConfig
from .commands import auth, diff, review, status
from .config import ConfigManager
from .update_checker import check_for_updates, get_update_message


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """EntelligenceAI Code Review CLI - AI-powered code review from your terminal."""
    # Initialize session storage
    ctx.ensure_object(dict)

    # Check for updates (non-blocking, cached for 24 hours)
    try:
        update_info = check_for_updates(__version__)
        if update_info:
            click.echo(get_update_message(update_info), err=True)
    except Exception:
        pass  # Silently ignore update check errors

    # Fetch user info once at session start if authenticated
    config = ConfigManager()
    if config.is_authenticated():
        token = config.get_token()
        endpoint = config.get_endpoint()

        api_config = APIConfig(endpoint=endpoint, api_token=token)
        api_client = APIClient(api_config)

        # Fetch user info from backend (required)
        user_info = None
        with suppress(Exception):
            user_info = api_client.get_user_info()

        # Store in context for all commands to use
        ctx.obj["user_info"] = user_info
        ctx.obj["config"] = config
        ctx.obj["api_client"] = api_client


# Add command groups and commands
cli.add_command(auth, "auth")
cli.add_command(review, "review")
cli.add_command(diff, "diff")
cli.add_command(status, "status")


if __name__ == "__main__":
    cli()
