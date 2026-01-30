"""Email notification commands."""

import typer
import httpx
from rich.console import Console
from rich.table import Table

from mushu.config import get_auth_token, get_config

app = typer.Typer(help="Email notification commands")
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


# Domain commands


@app.command("add-domain")
def add_domain(
    domain: str = typer.Argument(..., help="Domain to add (e.g., acme.com)"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    from_name: str = typer.Option(None, "--from-name", help="Default sender name"),
):
    """Add a domain for email sending."""
    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers()

    body = {"domain": domain}
    if from_name:
        body["from_name"] = from_name

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.notify_url}/tenants/{tenant_id}/email/domains",
                headers=headers,
                json=body,
                timeout=30,
            )

        if response.status_code == 200:
            result = response.json()
            console.print(f"[green]✓ Domain added: {domain}[/green]")
            console.print(f"  Status: {result['status']}")
            console.print()
            console.print("[yellow]Add these DNS records to verify your domain:[/yellow]")

            table = Table()
            table.add_column("Type")
            table.add_column("Name")
            table.add_column("Value")
            table.add_column("Purpose")

            for record in result.get("dns_records", []):
                table.add_row(
                    record["type"],
                    record["name"],
                    record["value"],
                    record["purpose"],
                )

            console.print(table)
            console.print()
            console.print("After adding records, run: mushu email verify-domain " + domain)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            console.print(response.text)
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("verify-domain")
def verify_domain(
    domain: str = typer.Argument(..., help="Domain to verify"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
):
    """Check domain verification status."""
    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers()

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.notify_url}/tenants/{tenant_id}/email/domains/{domain}/verify",
                headers=headers,
                timeout=30,
            )

        if response.status_code == 200:
            result = response.json()
            status = result["status"]

            if status == "verified":
                console.print(f"[green]✓ Domain verified: {domain}[/green]")
                if result.get("verified_at"):
                    console.print(f"  Verified at: {result['verified_at']}")
            elif status == "pending":
                console.print(f"[yellow]⏳ Domain pending verification: {domain}[/yellow]")
                console.print("  DNS records may take up to 72 hours to propagate.")
            else:
                console.print(f"[red]✗ Domain verification failed: {domain}[/red]")

        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            console.print(response.text)
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("get-domain")
def get_domain(
    domain: str = typer.Argument(..., help="Domain to get details for"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
):
    """Get domain details including DNS records."""
    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers()

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.notify_url}/tenants/{tenant_id}/email/domains/{domain}",
                headers=headers,
                timeout=30,
            )

        if response.status_code == 200:
            result = response.json()
            console.print(f"Domain: {result['domain']}")
            console.print(f"Status: {result['status']}")
            if result.get("from_name"):
                console.print(f"From Name: {result['from_name']}")
            console.print(f"Created: {result['created_at']}")
            if result.get("verified_at"):
                console.print(f"Verified: {result['verified_at']}")

            console.print()
            console.print("DNS Records:")

            table = Table()
            table.add_column("Type")
            table.add_column("Name")
            table.add_column("Value")

            for record in result.get("dns_records", []):
                table.add_row(
                    record["type"],
                    record["name"],
                    record["value"],
                )

            console.print(table)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("delete-domain")
def delete_domain(
    domain: str = typer.Argument(..., help="Domain to delete"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove a domain from the tenant."""
    if not force:
        confirm = typer.confirm(f"Delete domain {domain}?")
        if not confirm:
            raise typer.Exit(0)

    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers()

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{config.notify_url}/tenants/{tenant_id}/email/domains/{domain}",
                headers=headers,
                timeout=30,
            )

        if response.status_code == 200:
            console.print(f"[green]✓ Domain deleted: {domain}[/green]")
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


# Contact commands


@app.command("add-contact")
def add_contact(
    user_id: str = typer.Option(..., "--user", "-u", help="User ID"),
    email_address: str = typer.Option(..., "--email", "-e", help="Email address"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="Tenant API key"),
):
    """Register an email contact for a user."""
    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers(api_key)

    body = {
        "user_id": user_id,
        "email": email_address,
    }

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.notify_url}/tenants/{tenant_id}/contacts",
                headers=headers,
                json=body,
                timeout=30,
            )

        if response.status_code == 200:
            result = response.json()
            console.print("[green]✓ Contact registered[/green]")
            console.print(f"  User: {result['user_id']}")
            console.print(f"  Email: {result['email']}")
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            console.print(response.text)
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list-contacts")
def list_contacts(
    user_id: str = typer.Option(None, "--user", "-u", help="Filter by user ID"),
    email_address: str = typer.Option(None, "--email", "-e", help="Filter by email"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="Tenant API key"),
):
    """List email contacts."""
    if not user_id and not email_address:
        console.print("[red]Either --user or --email is required[/red]")
        raise typer.Exit(1)

    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers(api_key)

    params = {}
    if user_id:
        params["user_id"] = user_id
    if email_address:
        params["email"] = email_address

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.notify_url}/tenants/{tenant_id}/contacts",
                headers=headers,
                params=params,
                timeout=30,
            )

        if response.status_code == 200:
            result = response.json()
            contacts = result.get("contacts", [])

            if not contacts:
                console.print("No contacts found.")
                return

            table = Table()
            table.add_column("Email")
            table.add_column("User ID")
            table.add_column("Subscribed")
            table.add_column("Created")

            for contact in contacts:
                table.add_row(
                    contact["email"],
                    contact["user_id"],
                    "Yes" if contact["subscribed"] else "No",
                    contact["created_at"][:10],
                )

            console.print(table)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("unsubscribe")
def unsubscribe(
    email_address: str = typer.Argument(..., help="Email to unsubscribe"),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="Tenant API key"),
):
    """Unsubscribe an email contact."""
    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers(api_key)

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{config.notify_url}/tenants/{tenant_id}/contacts/{email_address}",
                headers=headers,
                timeout=30,
            )

        if response.status_code == 200:
            console.print(f"[green]✓ Contact unsubscribed: {email_address}[/green]")
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


# Send email command


@app.command("send")
def send(
    user_id: str = typer.Option(..., "--user", "-u", help="Target user ID"),
    subject: str = typer.Option(..., "--subject", "-s", help="Email subject"),
    body_html: str = typer.Option(None, "--html", help="HTML body (or use --file)"),
    body_file: str = typer.Option(None, "--file", "-f", help="HTML file to send"),
    body_text: str = typer.Option(None, "--text", help="Plain text body"),
    from_address: str = typer.Option(
        None, "--from", help="Sender email (must be @verified-domain)"
    ),
    tenant_id: str = typer.Option(None, "--tenant", "-t", help="Tenant ID"),
    api_key: str = typer.Option(None, "--api-key", "-k", help="Tenant API key"),
):
    """Send an email notification to a user."""
    if not body_html and not body_file:
        console.print("[red]Either --html or --file is required[/red]")
        raise typer.Exit(1)

    if body_file:
        try:
            with open(body_file, "r") as f:
                body_html = f.read()
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            raise typer.Exit(1)

    tenant_id = resolve_tenant(tenant_id)
    config = get_config()
    headers = get_headers(api_key)

    body = {
        "user_id": user_id,
        "channel": "email",
        "email_subject": subject,
        "email_body_html": body_html,
    }

    if body_text:
        body["email_body_text"] = body_text
    if from_address:
        body["email_from"] = from_address

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.notify_url}/tenants/{tenant_id}/notify/unified",
                headers=headers,
                json=body,
                timeout=30,
            )

        if response.status_code == 200:
            result = response.json()
            email_result = result.get("email", {})

            if email_result.get("success"):
                console.print("[green]✓ Email sent[/green]")
                if email_result.get("message_id"):
                    console.print(f"  Message ID: {email_result['message_id']}")
            else:
                console.print(f"[red]✗ Email failed: {email_result.get('error')}[/red]")
                raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            console.print(response.text)
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)
