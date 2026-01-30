"""Authentication commands for EntelligenceAI CLI."""

import click

from ..api_client import APIClient, APIConfig
from ..config import ConfigManager


@click.group()
def auth():
    """Authentication commands."""
    pass


@auth.command()
@click.option("--token", default=None, help="Your EntelligenceAI API key")
def login(token):
    """Authenticate with EntelligenceAI."""
    # Show helpful message about where to get API key
    if not token:
        click.echo("\nGet your API key from: https://app.entelligence.ai/signup?cli=true")
        token = click.prompt("Enter your API key", hide_input=True, confirmation_prompt=False)
        if not token:
            click.echo("✗ No API key entered", err=True)
            return

    config = ConfigManager()
    endpoint = config.get_endpoint()

    # Validate API key with backend before saving
    click.echo("Validating API key...")
    api_config = APIConfig(endpoint=endpoint, api_token=token)
    api_client = APIClient(api_config)

    # Try to fetch user info to validate the API key
    user_info = api_client.get_user_info()

    if user_info and not user_info.get("Error"):
        # Valid API key - save it
        config.set_token(token)
        click.echo("✓ Authentication successful!")
        click.echo(f"✓ API key stored in {config.config_file}")
        click.echo("\nYou can now run: entelligence review")
    else:
        # Invalid API key or error - show user-friendly message
        if user_info and user_info.get("Error"):
            error_msg = user_info["Error"]
            if "401" in error_msg or "Unauthorized" in error_msg or "Invalid API key" in error_msg:
                click.echo("✗ Invalid API key", err=True)
            elif "403" in error_msg or "Forbidden" in error_msg:
                click.echo("✗ API key does not have required permissions", err=True)
            elif "Network error" in error_msg:
                click.echo("✗ Network error - could not reach server", err=True)
            else:
                click.echo(f"✗ Authentication failed: {error_msg}", err=True)
        else:
            # This should rarely happen now, but keep as fallback
            click.echo("✗ Authentication failed - please check your API key", err=True)
        click.echo("\nPlease check your API key and try again.", err=True)


@auth.command()
def logout():
    """Remove stored authentication."""
    config = ConfigManager()
    config.clear_auth()
    click.echo("✓ Logged out successfully")


@auth.command()
@click.pass_context
def status(ctx):
    """Check authentication status."""
    config = ConfigManager()

    if config.is_authenticated():
        token = config.get_token()

        # Use cached user info from session
        user_info = ctx.obj.get("user_info") if ctx.obj else None

        click.echo("✓ Authenticated")

        # Show user details if available
        if user_info:
            if user_info.get("Name"):
                click.echo(f"  Name: {user_info['Name']}")
            if user_info.get("Email"):
                click.echo(f"  Email: {user_info['Email']}")
            if user_info.get("OrgName"):
                click.echo(f"  Organization: {user_info['OrgName']}")
                if user_info.get("OrgUUID"):
                    click.echo(f"  Org UUID: {user_info['OrgUUID']}")

        # Always show API key
        click.echo(f"  API Key: {'*' * 8}{token[-4:]}")
    else:
        click.echo("✗ Not authenticated")
        click.echo("\nRun: entelligence auth login")
