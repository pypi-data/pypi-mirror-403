"""API Key commands."""

import typer
import httpx
from rich.console import Console
from rich.table import Table

from mushu.config import Config, StoredTokens, get_config, get_global_config

app = typer.Typer(help="API key management")
console = Console()


def require_auth() -> tuple[StoredTokens, Config]:
    """Require authentication for a command."""
    tokens = StoredTokens.load()
    config = get_global_config()

    if not tokens:
        console.print("[red]Not logged in. Run 'mushu auth login' first.[/red]")
        raise typer.Exit(1)

    return tokens, config


def get_app_id(app_id: str | None) -> str:
    """Get app_id from argument or config."""
    if app_id:
        return app_id

    effective = get_config()
    if effective.app_id:
        return effective.app_id

    console.print("[red]No app specified. Use --app or set default with 'mushu app use <id>'[/red]")
    raise typer.Exit(1)


@app.command("create")
def create_api_key(
    name: str = typer.Argument(..., help="Key name (e.g., 'production-backend')"),
    app_id: str = typer.Option(None, "--app", "-a", help="App ID"),
    scope: str = typer.Option("write", "--scope", "-s", help="Scope: read, write, or admin"),
    expires_days: int = typer.Option(None, "--expires", help="Days until expiry (default: never)"),
):
    """Create a new API key for an app.

    The full key is only shown once - save it immediately.
    """
    tokens, config = require_auth()
    app_id = get_app_id(app_id)

    if scope not in ("read", "write", "admin"):
        console.print("[red]Scope must be 'read', 'write', or 'admin'[/red]")
        raise typer.Exit(1)

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.core_url}/apps/{app_id}/api-keys",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                json={
                    "name": name,
                    "scope": scope,
                    "expires_in_days": expires_days,
                },
                timeout=10,
            )

        if response.status_code == 200:
            key_data = response.json()
            console.print("[green]✓ API key created[/green]")
            console.print()
            console.print(f"  Key ID: {key_data['key_id']}")
            console.print(f"  Name: {key_data['name']}")
            console.print(f"  Scope: {key_data['scope']}")
            if key_data.get("expires_at"):
                console.print(f"  Expires: {key_data['expires_at'][:10]}")
            console.print()
            console.print("[yellow]Save this key now - it won't be shown again:[/yellow]")
            console.print()
            console.print(f"  [bold]{key_data['key']}[/bold]")
            console.print()
        elif response.status_code == 400:
            error = response.json()
            console.print(f"[red]✗ {error.get('detail', 'Bad request')}[/red]")
            raise typer.Exit(1)
        elif response.status_code == 403:
            console.print("[red]✗ Admin access required[/red]")
            raise typer.Exit(1)
        elif response.status_code == 404:
            console.print("[red]✗ App not found[/red]")
            raise typer.Exit(1)
        elif response.status_code == 401:
            console.print("[red]✗ Unauthorized. Try 'mushu auth refresh'.[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_api_keys(
    app_id: str = typer.Option(None, "--app", "-a", help="App ID"),
):
    """List API keys for an app."""
    tokens, config = require_auth()
    app_id = get_app_id(app_id)

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.core_url}/apps/{app_id}/api-keys",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            data = response.json()
            keys = data.get("keys", [])

            if not keys:
                console.print("[dim]No API keys found.[/dim]")
                return

            table = Table(title="API Keys")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Prefix")
            table.add_column("Scope")
            table.add_column("Created", style="dim")
            table.add_column("Expires", style="dim")

            for k in keys:
                scope_style = {
                    "read": "[dim]read[/dim]",
                    "write": "write",
                    "admin": "[yellow]admin[/yellow]",
                }.get(k["scope"], k["scope"])

                expires = k.get("expires_at", "-")
                if expires and expires != "-":
                    expires = expires[:10]

                # Show if revoked
                if k.get("revoked_at"):
                    scope_style = "[red]revoked[/red]"

                table.add_row(
                    k["key_id"],
                    k["name"],
                    k["prefix"] + "...",
                    scope_style,
                    k["created_at"][:10],
                    expires,
                )

            console.print(table)

        elif response.status_code == 403:
            console.print("[red]✗ Admin access required[/red]")
            raise typer.Exit(1)
        elif response.status_code == 404:
            console.print("[red]✗ App not found[/red]")
            raise typer.Exit(1)
        elif response.status_code == 401:
            console.print("[red]✗ Unauthorized. Try 'mushu auth refresh'.[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("show")
def show_api_key(
    key_id: str = typer.Argument(..., help="API key ID"),
    app_id: str = typer.Option(None, "--app", "-a", help="App ID"),
):
    """Show API key details."""
    tokens, config = require_auth()
    app_id = get_app_id(app_id)

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.core_url}/apps/{app_id}/api-keys/{key_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            k = response.json()

            table = Table(title=f"API Key: {k['name']}")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Key ID", k["key_id"])
            table.add_row("Name", k["name"])
            table.add_row("Prefix", k["prefix"] + "...")
            table.add_row("Scope", k["scope"])
            table.add_row("App ID", k["app_id"])
            table.add_row("Created", k["created_at"][:19])
            table.add_row("Created By", k["created_by"])
            table.add_row(
                "Last Used", k.get("last_used_at", "-")[:19] if k.get("last_used_at") else "-"
            )
            table.add_row(
                "Expires", k.get("expires_at", "-")[:10] if k.get("expires_at") else "Never"
            )

            if k.get("revoked_at"):
                table.add_row("Revoked", k["revoked_at"][:19])

            console.print(table)

        elif response.status_code == 403:
            console.print("[red]✗ Admin access required[/red]")
            raise typer.Exit(1)
        elif response.status_code == 404:
            console.print("[red]✗ API key not found[/red]")
            raise typer.Exit(1)
        elif response.status_code == 401:
            console.print("[red]✗ Unauthorized. Try 'mushu auth refresh'.[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete_api_key(
    key_id: str = typer.Argument(..., help="API key ID to revoke"),
    app_id: str = typer.Option(None, "--app", "-a", help="App ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Revoke an API key.

    The key will stop working immediately.
    """
    tokens, config = require_auth()
    app_id = get_app_id(app_id)

    if not force:
        confirm = typer.confirm(f"Revoke API key {key_id}? This cannot be undone.")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{config.core_url}/apps/{app_id}/api-keys/{key_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            console.print("[green]✓ API key revoked[/green]")
        elif response.status_code == 403:
            console.print("[red]✗ Admin access required[/red]")
            raise typer.Exit(1)
        elif response.status_code == 404:
            console.print("[red]✗ API key not found or already revoked[/red]")
            raise typer.Exit(1)
        elif response.status_code == 401:
            console.print("[red]✗ Unauthorized. Try 'mushu auth refresh'.[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)
