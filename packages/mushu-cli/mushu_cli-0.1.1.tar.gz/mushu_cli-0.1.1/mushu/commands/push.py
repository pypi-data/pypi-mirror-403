"""Push notification commands."""

import json
import typer
import httpx
from rich.console import Console

from mushu.config import get_auth_token, get_config

app = typer.Typer(help="Push notification commands")
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


@app.command("send")
def send(
    user_id: str = typer.Option(..., "--user", "-u", help="Target user ID"),
    title: str = typer.Option(None, "--title", help="Notification title"),
    body: str = typer.Option(None, "--body", "-b", help="Notification body"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    badge: int = typer.Option(None, "--badge", help="Badge count"),
    sound: str = typer.Option(None, "--sound", help="Sound name"),
    payload: str = typer.Option(None, "--payload", "-p", help="Custom JSON payload"),
    silent: bool = typer.Option(False, "--silent", "-s", help="Silent/background push"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="Tenant API key"),
):
    """Send a push notification to a user."""
    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers(api_key)

    # Build request
    request_body: dict = {"user_id": user_id}

    if not silent and (title or body):
        alert = {}
        if title:
            alert["title"] = title
        if body:
            alert["body"] = body
        request_body["alert"] = alert

    if badge is not None:
        request_body["badge"] = badge
    if sound:
        request_body["sound"] = sound
    if silent:
        request_body["content_available"] = True

    if payload:
        try:
            request_body["data"] = json.loads(payload)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON payload[/red]")
            raise typer.Exit(1)

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.notify_url}/tenants/{tenant_id}/notify",
                headers=headers,
                json=request_body,
                timeout=30,
            )

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                console.print("[green]✓ Push sent[/green]")
                if result.get("message_id"):
                    console.print(f"  Message ID: {result['message_id']}")
            else:
                console.print(f"[red]✗ Push failed: {result.get('error')}[/red]")
                raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("bulk")
def bulk(
    users: str = typer.Option(..., "--users", help="Comma-separated user IDs"),
    title: str = typer.Option(None, "--title", help="Notification title"),
    body: str = typer.Option(None, "--body", "-b", help="Notification body"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    badge: int = typer.Option(None, "--badge", help="Badge count"),
    silent: bool = typer.Option(False, "--silent", "-s", help="Silent/background push"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="Tenant API key"),
):
    """Send push to multiple users."""
    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers(api_key)

    user_ids = [u.strip() for u in users.split(",") if u.strip()]
    if not user_ids:
        console.print("[red]No user IDs provided[/red]")
        raise typer.Exit(1)

    request_body: dict = {"user_ids": user_ids}

    if not silent and (title or body):
        alert = {}
        if title:
            alert["title"] = title
        if body:
            alert["body"] = body
        request_body["alert"] = alert

    if badge is not None:
        request_body["badge"] = badge
    if silent:
        request_body["content_available"] = True

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.notify_url}/tenants/{tenant_id}/notify/bulk",
                headers=headers,
                json=request_body,
                timeout=60,
            )

        if response.status_code == 200:
            result = response.json()
            console.print("[green]✓ Bulk push completed[/green]")
            console.print(f"  Total: {result['total']}")
            console.print(f"  Success: {result['success']}")
            console.print(f"  Failed: {result['failed']}")
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)
