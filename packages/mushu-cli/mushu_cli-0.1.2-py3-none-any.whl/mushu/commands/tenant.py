"""Tenant management commands."""

import typer
import httpx
from pathlib import Path
from rich.console import Console
from rich.table import Table

from mushu.config import get_auth_token, get_config

app = typer.Typer(help="Tenant management commands")
console = Console()


def get_headers() -> dict:
    """Get auth headers."""
    token = get_auth_token()
    if not token:
        console.print("[red]Not authenticated. Run 'mushu auth login' first.[/red]")
        raise typer.Exit(1)
    return {"Authorization": f"Bearer {token}"}


@app.command("create")
def create(
    org_id: str = typer.Option(
        None, "--org", "-o", help="Organization ID (uses default if not specified)"
    ),
    bundle_id: str = typer.Option(..., "--bundle-id", "-b", help="iOS app bundle ID"),
    team_id: str = typer.Option(..., "--team-id", "-t", help="Apple Developer Team ID"),
    key_id: str = typer.Option(..., "--key-id", "-k", help="APNs Key ID"),
    key_file: Path = typer.Option(..., "--key-file", "-f", help="Path to APNs .p8 key file"),
    sandbox: bool = typer.Option(True, "--sandbox/--production", help="Use sandbox APNs"),
):
    """Create a new notification tenant for an organization."""
    config = get_config()

    # Use default org if not specified
    org_id = org_id or config.default_org
    if not org_id:
        console.print("[red]No org specified. Use --org or set default with 'mushu org use'[/red]")
        raise typer.Exit(1)

    if not key_file.exists():
        console.print(f"[red]Key file not found: {key_file}[/red]")
        raise typer.Exit(1)

    private_key = key_file.read_text()
    headers = get_headers()

    payload = {
        "org_id": org_id,
        "bundle_id": bundle_id,
        "team_id": team_id,
        "key_id": key_id,
        "private_key": private_key,
        "use_sandbox": sandbox,
    }

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.notify_url}/tenants",
                headers=headers,
                json=payload,
                timeout=30,
            )

        if response.status_code == 200:
            tenant = response.json()
            console.print("[green]✓ Tenant created[/green]")
            console.print(f"  Tenant ID: {tenant['tenant_id']}")
            console.print(f"  Organization: {tenant['org_id']}")
            console.print(f"  Bundle ID: {tenant['bundle_id']}")
            console.print(f"  Environment: {'Sandbox' if tenant['use_sandbox'] else 'Production'}")

            # Set as default
            config.default_tenant = tenant["tenant_id"]
            config.save()
            console.print("[dim]Set as default tenant[/dim]")

        elif response.status_code == 400:
            console.print(f"[red]✗ Invalid credentials: {response.json().get('detail')}[/red]")
            raise typer.Exit(1)
        elif response.status_code == 403:
            console.print(f"[red]✗ Access denied: {response.json().get('detail')}[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_tenants(
    org_id: str = typer.Option(
        None, "--org", "-o", help="Organization ID (uses default if not specified)"
    ),
):
    """List tenants for an organization."""
    config = get_config()

    # Use default org if not specified
    org_id = org_id or config.default_org
    if not org_id:
        console.print("[red]No org specified. Use --org or set default with 'mushu org use'[/red]")
        raise typer.Exit(1)

    headers = get_headers()

    url = f"{config.notify_url}/tenants?org_id={org_id}"

    try:
        with httpx.Client() as client:
            response = client.get(
                url,
                headers=headers,
                timeout=10,
            )

        if response.status_code == 200:
            tenants = response.json().get("tenants", [])

            if not tenants:
                console.print("[yellow]No tenants found for this organization.[/yellow]")
                return

            table = Table(title=f"Tenants (org: {org_id})")
            table.add_column("ID", style="cyan")
            table.add_column("Bundle ID", style="green")
            table.add_column("Team ID")
            table.add_column("Env")
            table.add_column("Default")

            for t in tenants:
                is_default = "★" if t["tenant_id"] == config.default_tenant else ""
                table.add_row(
                    t["tenant_id"],
                    t["bundle_id"],
                    t["team_id"],
                    "sandbox" if t["use_sandbox"] else "prod",
                    is_default,
                )

            console.print(table)

        elif response.status_code == 403:
            console.print(f"[red]✗ Access denied: {response.json().get('detail')}[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete")
def delete(
    tenant_id: str = typer.Argument(..., help="Tenant ID to delete"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Delete a tenant."""
    if not yes:
        if not typer.confirm(f"Delete tenant {tenant_id}?"):
            console.print("Cancelled.")
            return

    config = get_config()
    headers = get_headers()

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{config.notify_url}/tenants/{tenant_id}",
                headers=headers,
                timeout=10,
            )

        if response.status_code == 200:
            console.print(f"[green]✓ Tenant {tenant_id} deleted[/green]")
            if config.default_tenant == tenant_id:
                config.default_tenant = None
                config.save()
        elif response.status_code == 404:
            console.print("[red]✗ Tenant not found[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("use")
def use_tenant(
    tenant_id: str = typer.Argument(..., help="Tenant ID to set as default"),
):
    """Set default tenant."""
    config = get_config()
    config.default_tenant = tenant_id
    config.save()
    console.print(f"[green]✓ Default tenant set to: {tenant_id}[/green]")


@app.command("api-key")
def create_api_key(
    tenant_id: str = typer.Argument(None, help="Tenant ID (uses default if not specified)"),
    name: str = typer.Option("default", "--name", "-n", help="Key name"),
):
    """Create an API key for a tenant."""
    config = get_config()
    tenant_id = tenant_id or config.default_tenant

    if not tenant_id:
        console.print(
            "[red]No tenant specified. Use --tenant or set default with 'mushu tenant use'[/red]"
        )
        raise typer.Exit(1)

    headers = get_headers()

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.notify_url}/tenants/{tenant_id}/api-keys",
                headers=headers,
                json={"name": name},
                timeout=10,
            )

        if response.status_code == 200:
            key = response.json()
            console.print("[green]✓ API key created[/green]")
            console.print(f"  Key ID: {key['key_id']}")
            console.print()
            console.print("[yellow]Save this key - it won't be shown again:[/yellow]")
            console.print(f"  {key['key']}")
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)
