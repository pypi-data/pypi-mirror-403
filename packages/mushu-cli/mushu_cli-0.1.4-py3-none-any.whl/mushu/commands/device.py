"""Device management commands."""

import typer
import httpx
from rich.console import Console
from rich.table import Table

from mushu.config import get_auth_token, get_config

app = typer.Typer(help="Device management commands")
console = Console()


def get_headers(api_key: str | None = None) -> dict:
    """Get auth headers."""
    if api_key:
        return {"X-API-Key": api_key}
    token = get_auth_token()
    if not token:
        console.print("[red]Not authenticated. Run 'mushu auth login' or use --api-key.[/red]")
        raise typer.Exit(1)
    return {"Authorization": f"Bearer {token}"}


def resolve_tenant(tenant_id: str | None) -> str:
    """Resolve tenant ID."""
    if tenant_id:
        return tenant_id
    config = get_config()
    if config.default_tenant:
        return config.default_tenant
    console.print("[red]No tenant specified. Use --tenant or 'mushu tenant use'.[/red]")
    raise typer.Exit(1)


@app.command("register")
def register(
    user_id: str = typer.Option(..., "--user", "-u", help="User ID"),
    token: str = typer.Option(..., "--token", help="APNs device token"),
    platform: str = typer.Option("ios", "--platform", "-p", help="Platform (ios/watchos)"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    app_version: str = typer.Option(None, "--version", "-v", help="App version"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="Tenant API key"),
):
    """Register a device token."""
    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers(api_key)

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.notify_url}/tenants/{tenant_id}/devices",
                headers=headers,
                json={
                    "user_id": user_id,
                    "token": token,
                    "platform": platform,
                    "app_version": app_version,
                },
                timeout=10,
            )

        if response.status_code == 200:
            device = response.json()
            console.print("[green]✓ Device registered[/green]")
            console.print(f"  User: {device['user_id']}")
            console.print(f"  Platform: {device['platform']}")
            console.print(f"  Token: {device['token'][:16]}...")
        elif response.status_code == 400:
            console.print("[red]✗ Invalid token format[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_devices(
    user_id: str = typer.Option(..., "--user", "-u", help="User ID"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="Tenant API key"),
):
    """List devices for a user."""
    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers(api_key)

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.notify_url}/tenants/{tenant_id}/devices",
                headers=headers,
                params={"user_id": user_id},
                timeout=10,
            )

        if response.status_code == 200:
            devices = response.json().get("devices", [])

            if not devices:
                console.print(f"[yellow]No devices for user {user_id}[/yellow]")
                return

            table = Table(title=f"Devices for {user_id}")
            table.add_column("Token", style="cyan")
            table.add_column("Platform")
            table.add_column("Version")
            table.add_column("Updated")

            for d in devices:
                table.add_row(
                    f"{d['token'][:16]}...",
                    d["platform"],
                    d.get("app_version") or "-",
                    d["updated_at"][:10],
                )

            console.print(table)

        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("unregister")
def unregister(
    user_id: str = typer.Option(..., "--user", "-u", help="User ID"),
    token: str = typer.Option(..., "--token", help="Device token"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="Tenant API key"),
):
    """Unregister a device token."""
    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers(api_key)

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{config.notify_url}/tenants/{tenant_id}/devices/{token}",
                headers=headers,
                params={"user_id": user_id},
                timeout=10,
            )

        if response.status_code == 200:
            console.print("[green]✓ Device unregistered[/green]")
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)
