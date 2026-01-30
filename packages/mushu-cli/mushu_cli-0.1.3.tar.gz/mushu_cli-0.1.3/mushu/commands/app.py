"""App commands."""

import typer
import httpx
from rich.console import Console
from rich.table import Table

from mushu.config import Config, StoredTokens, get_config, get_global_config

app = typer.Typer(help="App management")
console = Console()


def require_auth() -> tuple[StoredTokens, Config]:
    """Require authentication for a command."""
    tokens = StoredTokens.load()
    config = get_global_config()

    if not tokens:
        console.print("[red]Not logged in. Run 'mushu auth login' first.[/red]")
        raise typer.Exit(1)

    return tokens, config


def get_org_id(org_id: str | None) -> str:
    """Get org_id from argument or config."""
    if org_id:
        return org_id

    effective = get_config()
    if effective.org_id:
        return effective.org_id

    console.print("[red]No org specified. Use --org or set default with 'mushu org use <id>'[/red]")
    raise typer.Exit(1)


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
def create_app(
    name: str = typer.Argument(..., help="App name"),
    bundle_id: str = typer.Option(
        ..., "--bundle-id", "-b", help="iOS bundle ID (e.g., com.company.app)"
    ),
    org_id: str = typer.Option(None, "--org", "-o", help="Organization ID"),
    android_package: str = typer.Option(None, "--android", help="Android package name"),
):
    """Create a new app."""
    tokens, config = require_auth()
    org_id = get_org_id(org_id)

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.core_url}/orgs/{org_id}/apps",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                json={
                    "name": name,
                    "bundle_id": bundle_id,
                    "android_package": android_package,
                },
                timeout=10,
            )

        if response.status_code == 200:
            app_data = response.json()
            console.print("[green]✓ App created[/green]")
            console.print(f"  ID: {app_data['app_id']}")
            console.print(f"  Name: {app_data['name']}")
            console.print(f"  Bundle ID: {app_data['bundle_id']}")
        elif response.status_code == 400:
            error = response.json()
            console.print(f"[red]✗ {error.get('detail', 'Bad request')}[/red]")
            raise typer.Exit(1)
        elif response.status_code == 403:
            console.print("[red]✗ Admin access required[/red]")
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
def list_apps(
    org_id: str = typer.Option(None, "--org", "-o", help="Organization ID"),
):
    """List apps in an organization."""
    tokens, config = require_auth()
    org_id = get_org_id(org_id)

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.core_url}/orgs/{org_id}/apps",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            data = response.json()
            apps = data.get("apps", [])

            if not apps:
                console.print("[dim]No apps found.[/dim]")
                return

            table = Table(title="Apps")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Bundle ID")
            table.add_column("Created", style="dim")

            for a in apps:
                table.add_row(
                    a["app_id"],
                    a["name"],
                    a["bundle_id"],
                    a["created_at"][:10],
                )

            console.print(table)

        elif response.status_code == 403:
            console.print("[red]✗ Not a member of this organization[/red]")
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
def show_app(
    app_id: str = typer.Argument(None, help="App ID"),
):
    """Show app details."""
    tokens, config = require_auth()
    app_id = get_app_id(app_id)

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.core_url}/apps/{app_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            app_data = response.json()

            table = Table(title=f"App: {app_data['name']}")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("ID", app_data["app_id"])
            table.add_row("Name", app_data["name"])
            table.add_row("Bundle ID", app_data["bundle_id"])
            table.add_row("Android Package", app_data.get("android_package") or "-")
            table.add_row("Org ID", app_data["org_id"])
            table.add_row("Created", app_data["created_at"][:10])
            table.add_row("Key ID", app_data["key_id"])

            console.print(table)

        elif response.status_code == 403:
            console.print("[red]✗ Not a member of this organization[/red]")
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


@app.command("use")
def use_app(
    app_id: str = typer.Argument(..., help="App ID to set as default"),
):
    """Set default app for commands."""
    tokens, config = require_auth()

    # Verify app exists and user has access
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.core_url}/apps/{app_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            app_data = response.json()
            config.default_app = app_data["app_id"]
            config.default_app_name = app_data["name"]
            config.save()
            console.print(
                f"[green]✓ Default app set to: {app_data['name']} ({app_data['app_id']})[/green]"
            )
        elif response.status_code == 403:
            console.print("[red]✗ Not a member of this organization[/red]")
            raise typer.Exit(1)
        elif response.status_code == 404:
            console.print("[red]✗ App not found[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("current")
def current_app():
    """Show current default app."""
    effective = get_config()

    if effective.app_id:
        console.print(
            f"Default app: [green]{effective.app_name or 'Unknown'}[/green] ({effective.app_id})"
        )
    else:
        console.print("[dim]No default app set. Use 'mushu app use <app_id>' to set one.[/dim]")


@app.command("delete")
def delete_app(
    app_id: str = typer.Argument(None, help="App ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete an app (admin only)."""
    tokens, config = require_auth()
    app_id = get_app_id(app_id)

    if not force:
        confirm = typer.confirm(f"Delete app {app_id}? This cannot be undone.")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{config.core_url}/apps/{app_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            console.print("[green]✓ App deleted[/green]")
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
