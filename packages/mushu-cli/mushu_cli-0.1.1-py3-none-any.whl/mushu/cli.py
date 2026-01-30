"""Main CLI entry point for Mushu."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from mushu.commands import (
    api_key,
    app as app_cmd,
    auth,
    device,
    email,
    media,
    org,
    pay,
    push,
    tenant,
)
from mushu.config import (
    LocalConfig,
    StoredTokens,
    get_config,
    get_global_config,
    LOCAL_CONFIG_FILE,
)

app = typer.Typer(
    name="mushu",
    help="Mushu CLI - Authentication and push notifications",
    no_args_is_help=True,
)
console = Console()

# Add command groups
app.add_typer(auth.app, name="auth", help="Authentication")
app.add_typer(org.app, name="org", help="Organization management")
app.add_typer(app_cmd.app, name="app", help="App management")  # app_cmd to avoid name collision
app.add_typer(api_key.app, name="api-key", help="API key management")
app.add_typer(tenant.app, name="tenant", help="Notification tenant management")
app.add_typer(pay.app, name="pay", help="Payment tenant management")
app.add_typer(media.app, name="media", help="Media management")
app.add_typer(device.app, name="device", help="Device management")
app.add_typer(push.app, name="push", help="Push notifications")
app.add_typer(email.app, name="email", help="Email notifications")


@app.command("init")
def init_cmd(
    org_id: str = typer.Option(None, "--org", "-o", help="Organization ID"),
    org_name: str = typer.Option(None, "--org-name", help="Organization name (for display)"),
    app_id: str = typer.Option(None, "--app", "-a", help="App ID"),
    app_name: str = typer.Option(None, "--app-name", help="App name (for display)"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Notification tenant ID"),
    pay_tenant_id: str = typer.Option(None, "--pay-tenant", help="Pay tenant ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
):
    """Initialize a .mushu.json config file in the current directory.

    This creates a project-specific configuration that the CLI will automatically
    use when running commands from this directory (or any subdirectory).

    Examples:
        mushu init --org org_abc123
        mushu init --org org_abc123 --tenant tenant_xyz
        mushu init --org org_abc123 --app app_def456
    """
    config_path = Path.cwd() / LOCAL_CONFIG_FILE

    # Check if config already exists
    if config_path.exists() and not force:
        console.print(f"[yellow]Config file already exists: {config_path}[/yellow]")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)

    # If no options provided, try to use current global defaults
    if not any([org_id, app_id, tenant_id, pay_tenant_id]):
        global_config = get_global_config()
        if global_config.default_org:
            org_id = global_config.default_org
            org_name = global_config.default_org_name
            console.print(f"[dim]Using default org from global config: {org_id}[/dim]")
        if global_config.default_tenant:
            tenant_id = global_config.default_tenant
            console.print(f"[dim]Using default tenant from global config: {tenant_id}[/dim]")
        if global_config.default_pay_tenant:
            pay_tenant_id = global_config.default_pay_tenant

    if not org_id:
        console.print(
            "[yellow]No org specified. Use --org to set one, or run 'mushu org use <id>' first.[/yellow]"
        )
        raise typer.Exit(1)

    # Create and save local config
    local_config = LocalConfig(
        org_id=org_id,
        org_name=org_name,
        app_id=app_id,
        app_name=app_name,
        tenant_id=tenant_id,
        pay_tenant_id=pay_tenant_id,
    )
    saved_path = local_config.save(config_path)

    console.print(f"[green]Created {saved_path}[/green]")
    console.print()

    # Show what was saved
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="dim")
    table.add_column("Value")

    if org_id:
        display = f"{org_id}" + (f" ({org_name})" if org_name else "")
        table.add_row("org_id", display)
    if app_id:
        display = f"{app_id}" + (f" ({app_name})" if app_name else "")
        table.add_row("app_id", display)
    if tenant_id:
        table.add_row("tenant_id", tenant_id)
    if pay_tenant_id:
        table.add_row("pay_tenant_id", pay_tenant_id)

    console.print(table)
    console.print()
    console.print("[dim]Commands in this directory will now use these defaults.[/dim]")


@app.command("config")
def config_cmd(
    auth_url: str = typer.Option(None, "--auth-url", help="Set auth API URL"),
    notify_url: str = typer.Option(None, "--notify-url", help="Set notify API URL"),
    pay_url: str = typer.Option(None, "--pay-url", help="Set pay API URL"),
    media_url: str = typer.Option(None, "--media-url", help="Set media API URL"),
    show: bool = typer.Option(False, "--show", "-s", help="Show current config"),
):
    """Configure global CLI settings.

    For per-project settings, use 'mushu init' to create a .mushu.json file.
    """
    config = get_global_config()

    if auth_url:
        config.auth_url = auth_url.rstrip("/")
        console.print(f"[green]Auth URL: {auth_url}[/green]")

    if notify_url:
        config.notify_url = notify_url.rstrip("/")
        console.print(f"[green]Notify URL: {notify_url}[/green]")

    if pay_url:
        config.pay_url = pay_url.rstrip("/")
        console.print(f"[green]Pay URL: {pay_url}[/green]")

    if media_url:
        config.media_url = media_url.rstrip("/")
        console.print(f"[green]Media URL: {media_url}[/green]")

    if auth_url or notify_url or pay_url or media_url:
        config.save()

    if show or (not auth_url and not notify_url and not pay_url and not media_url):
        # Show effective config (merged)
        effective = get_config()

        console.print("[bold]Global Config[/bold] (~/.mushu/config.json)")
        console.print(f"  Auth URL: {config.auth_url}")
        console.print(f"  Notify URL: {config.notify_url}")
        console.print(f"  Pay URL: {config.pay_url}")
        console.print(f"  Media URL: {config.media_url}")
        console.print(f"  Default org: {config.default_org or '[not set]'}")
        console.print(f"  Default tenant: {config.default_tenant or '[not set]'}")
        console.print()

        if effective.local_config_path:
            console.print(f"[bold]Local Config[/bold] ({effective.local_config_path})")
            local = LocalConfig.load()
            if local:
                if local.org_id:
                    console.print(f"  org_id: {local.org_id}")
                if local.app_id:
                    console.print(f"  app_id: {local.app_id}")
                if local.tenant_id:
                    console.print(f"  tenant_id: {local.tenant_id}")
                if local.pay_tenant_id:
                    console.print(f"  pay_tenant_id: {local.pay_tenant_id}")
            console.print()

        console.print("[bold]Effective Config[/bold] (merged)")
        console.print(f"  org_id: {effective.org_id or '[not set]'}")
        console.print(f"  app_id: {effective.app_id or '[not set]'}")
        console.print(f"  tenant_id: {effective.tenant_id or '[not set]'}")


@app.command("status")
def status():
    """Show current status and effective configuration."""
    config = get_config()
    tokens = StoredTokens.load()

    console.print("[bold]Mushu Status[/bold]")
    console.print()

    # Auth status
    if tokens:
        console.print("[green]Authenticated[/green]")
        if tokens.email:
            console.print(f"  Email: {tokens.email}")
        if tokens.user_id:
            console.print(f"  User: {tokens.user_id}")
    else:
        console.print("[yellow]Not authenticated[/yellow]")
        console.print("  Run: mushu auth login")

    console.print()

    # Project context
    console.print("[bold]Project Context[/bold]")
    if config.local_config_path:
        console.print(f"  [dim]from {config.local_config_path}[/dim]")
    else:
        console.print("  [dim]no .mushu.json found (using global defaults)[/dim]")

    if config.org_id:
        display = config.org_id + (f" ({config.org_name})" if config.org_name else "")
        console.print(f"  [green]Org: {display}[/green]")
    else:
        console.print("  [yellow]Org: not set[/yellow]")

    if config.app_id:
        display = config.app_id + (f" ({config.app_name})" if config.app_name else "")
        console.print(f"  [green]App: {display}[/green]")

    if config.tenant_id:
        console.print(f"  [green]Tenant: {config.tenant_id}[/green]")

    console.print()
    console.print(f"[dim]Auth: {config.auth_url}[/dim]")
    console.print(f"[dim]Notify: {config.notify_url}[/dim]")


@app.callback()
def main():
    """
    Mushu CLI - Authentication, push notifications, and media for your apps.

    Get started:
      mushu auth login          # Sign in
      mushu org create ...      # Create an organization
      mushu init --org <id>     # Set up project config
      mushu push send ...       # Send a notification
    """
    pass


if __name__ == "__main__":
    app()
