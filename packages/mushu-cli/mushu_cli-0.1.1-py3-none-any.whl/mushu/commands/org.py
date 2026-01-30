"""Organization commands."""

import typer
import httpx
from rich.console import Console
from rich.table import Table

from mushu.config import Config, StoredTokens, get_config

app = typer.Typer(help="Organization management")
console = Console()


def require_auth() -> tuple[StoredTokens, Config]:
    """Require authentication for a command."""
    tokens = StoredTokens.load()
    config = get_config()

    if not tokens:
        console.print("[red]Not logged in. Run 'mushu auth login' first.[/red]")
        raise typer.Exit(1)

    return tokens, config


@app.command("create")
def create_org(
    name: str = typer.Argument(..., help="Organization name"),
):
    """Create a new organization."""
    tokens, config = require_auth()

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.auth_url}/orgs",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                json={"name": name},
                timeout=10,
            )

        if response.status_code == 200:
            org = response.json()
            console.print("[green]✓ Organization created[/green]")
            console.print(f"  ID: {org['org_id']}")
            console.print(f"  Name: {org['name']}")
        elif response.status_code == 401:
            console.print("[red]✗ Unauthorized. Try 'mushu auth refresh'.[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            try:
                error = response.json()
                console.print(f"  {error.get('detail', 'Unknown error')}")
            except Exception:
                pass
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_orgs():
    """List organizations you belong to."""
    tokens, config = require_auth()

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.auth_url}/orgs",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            data = response.json()
            orgs = data.get("orgs", [])

            if not orgs:
                console.print("[dim]No organizations found.[/dim]")
                return

            table = Table(title="Organizations")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Created", style="dim")

            for org in orgs:
                table.add_row(
                    org["org_id"],
                    org["name"],
                    org["created_at"][:10],
                )

            console.print(table)

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
def show_org(
    org_id: str = typer.Argument(..., help="Organization ID"),
):
    """Show organization details."""
    tokens, config = require_auth()

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.auth_url}/orgs/{org_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            org = response.json()

            table = Table(title=f"Organization: {org['name']}")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("ID", org["org_id"])
            table.add_row("Name", org["name"])
            table.add_row("Created", org["created_at"][:10])
            table.add_row("Created By", org["created_by"])

            console.print(table)

        elif response.status_code == 403:
            console.print("[red]✗ Not a member of this organization[/red]")
            raise typer.Exit(1)
        elif response.status_code == 404:
            console.print("[red]✗ Organization not found[/red]")
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
def use_org(
    org_id: str = typer.Argument(..., help="Organization ID to set as default"),
):
    """Set default organization for commands."""
    tokens, config = require_auth()

    # Verify org exists and user is a member
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.auth_url}/orgs/{org_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            org = response.json()
            config.default_org = org["org_id"]
            config.default_org_name = org["name"]
            config.save()
            console.print(f"[green]✓ Default org set to: {org['name']} ({org['org_id']})[/green]")
        elif response.status_code == 403:
            console.print("[red]✗ Not a member of this organization[/red]")
            raise typer.Exit(1)
        elif response.status_code == 404:
            console.print("[red]✗ Organization not found[/red]")
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("current")
def current_org():
    """Show current default organization."""
    config = get_config()

    if config.default_org:
        console.print(
            f"Default org: [green]{config.default_org_name or 'Unknown'}[/green] ({config.default_org})"
        )
    else:
        console.print("[dim]No default org set. Use 'mushu org use <org_id>' to set one.[/dim]")


@app.command("delete")
def delete_org(
    org_id: str = typer.Argument(..., help="Organization ID"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete an organization (owner only)."""
    tokens, config = require_auth()

    if not force:
        confirm = typer.confirm(f"Delete organization {org_id}? This cannot be undone.")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{config.auth_url}/orgs/{org_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            console.print("[green]✓ Organization deleted[/green]")
        elif response.status_code == 403:
            console.print("[red]✗ Owner access required[/red]")
            raise typer.Exit(1)
        elif response.status_code == 404:
            console.print("[red]✗ Organization not found[/red]")
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


# Member management subcommand group
members_app = typer.Typer(help="Organization member management")
app.add_typer(members_app, name="members")


@members_app.command("list")
def list_members(
    org_id: str = typer.Argument(..., help="Organization ID"),
):
    """List organization members."""
    tokens, config = require_auth()

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.auth_url}/orgs/{org_id}/members",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            data = response.json()
            members = data.get("members", [])

            if not members:
                console.print("[dim]No members found.[/dim]")
                return

            table = Table(title="Members")
            table.add_column("User ID", style="cyan")
            table.add_column("Role", style="green")
            table.add_column("Joined", style="dim")

            for member in members:
                role = member["role"]
                role_style = {
                    "owner": "[bold magenta]owner[/bold magenta]",
                    "admin": "[yellow]admin[/yellow]",
                    "member": "member",
                }.get(role, role)

                table.add_row(
                    member["user_id"],
                    role_style,
                    member["joined_at"][:10],
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


@members_app.command("add")
def add_member(
    org_id: str = typer.Argument(..., help="Organization ID"),
    user_id: str = typer.Argument(..., help="User ID to add"),
    role: str = typer.Option("member", "--role", "-r", help="Role: member, admin"),
):
    """Add a member to the organization (admin only)."""
    tokens, config = require_auth()

    if role not in ("member", "admin"):
        console.print("[red]Role must be 'member' or 'admin'[/red]")
        raise typer.Exit(1)

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.auth_url}/orgs/{org_id}/members",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                json={"user_id": user_id, "role": role},
                timeout=10,
            )

        if response.status_code == 200:
            member = response.json()
            console.print("[green]✓ Member added[/green]")
            console.print(f"  User: {member['user_id']}")
            console.print(f"  Role: {member['role']}")
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


@members_app.command("update")
def update_member(
    org_id: str = typer.Argument(..., help="Organization ID"),
    user_id: str = typer.Argument(..., help="User ID to update"),
    role: str = typer.Argument(..., help="New role: member, admin"),
):
    """Update a member's role (admin only)."""
    tokens, config = require_auth()

    if role not in ("member", "admin"):
        console.print("[red]Role must be 'member' or 'admin'[/red]")
        raise typer.Exit(1)

    try:
        with httpx.Client() as client:
            response = client.patch(
                f"{config.auth_url}/orgs/{org_id}/members/{user_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                json={"role": role},
                timeout=10,
            )

        if response.status_code == 200:
            member = response.json()
            console.print("[green]✓ Member updated[/green]")
            console.print(f"  User: {member['user_id']}")
            console.print(f"  Role: {member['role']}")
        elif response.status_code == 400:
            error = response.json()
            console.print(f"[red]✗ {error.get('detail', 'Bad request')}[/red]")
            raise typer.Exit(1)
        elif response.status_code == 403:
            console.print("[red]✗ Admin access required[/red]")
            raise typer.Exit(1)
        elif response.status_code == 404:
            console.print("[red]✗ Member not found[/red]")
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


@members_app.command("remove")
def remove_member(
    org_id: str = typer.Argument(..., help="Organization ID"),
    user_id: str = typer.Argument(..., help="User ID to remove"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Remove a member from the organization (admin only)."""
    tokens, config = require_auth()

    if not force:
        confirm = typer.confirm(f"Remove user {user_id} from organization?")
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            return

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{config.auth_url}/orgs/{org_id}/members/{user_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            console.print("[green]✓ Member removed[/green]")
        elif response.status_code == 400:
            error = response.json()
            console.print(f"[red]✗ {error.get('detail', 'Bad request')}[/red]")
            raise typer.Exit(1)
        elif response.status_code == 403:
            console.print("[red]✗ Admin access required[/red]")
            raise typer.Exit(1)
        elif response.status_code == 404:
            console.print("[red]✗ Member not found[/red]")
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


@members_app.command("me")
def my_membership(
    org_id: str = typer.Argument(..., help="Organization ID"),
):
    """Show your membership in an organization."""
    tokens, config = require_auth()

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.auth_url}/orgs/{org_id}/members/me",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            member = response.json()

            table = Table(title="Your Membership")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("User ID", member["user_id"])
            table.add_row("Organization", member["org_id"])
            table.add_row("Role", member["role"])
            table.add_row("Joined", member["joined_at"][:10])

            console.print(table)

        elif response.status_code == 404:
            console.print("[yellow]You are not a member of this organization[/yellow]")
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


# Invite management subcommand group
invites_app = typer.Typer(help="Organization invite management")
app.add_typer(invites_app, name="invites")


@invites_app.command("create")
def create_invite(
    org_id: str = typer.Argument(..., help="Organization ID"),
    email: str = typer.Option(None, "--email", "-e", help="Email address to invite"),
    link: bool = typer.Option(False, "--link", "-l", help="Create shareable link instead"),
    role: str = typer.Option("member", "--role", "-r", help="Role: member, admin"),
    expires: int = typer.Option(7, "--expires", help="Days until invite expires (0 for never)"),
):
    """Create an invite to an organization."""
    tokens, config = require_auth()

    if not email and not link:
        console.print("[red]Specify --email or --link[/red]")
        raise typer.Exit(1)

    if email and link:
        console.print("[red]Cannot use both --email and --link[/red]")
        raise typer.Exit(1)

    if role not in ("member", "admin"):
        console.print("[red]Role must be 'member' or 'admin'[/red]")
        raise typer.Exit(1)

    try:
        with httpx.Client() as client:
            if email:
                response = client.post(
                    f"{config.auth_url}/orgs/{org_id}/invites/email",
                    headers={"Authorization": f"Bearer {tokens.access_token}"},
                    json={"email": email, "role": role},
                    timeout=10,
                )
            else:
                response = client.post(
                    f"{config.auth_url}/orgs/{org_id}/invites/link",
                    headers={"Authorization": f"Bearer {tokens.access_token}"},
                    json={
                        "role": role,
                        "expires_in_days": expires if expires > 0 else None,
                    },
                    timeout=10,
                )

        if response.status_code == 200:
            invite = response.json()
            console.print("[green]✓ Invite created[/green]")

            if email:
                console.print(f"  Email: {invite['email']}")
                console.print(f"  Role: {invite['role']}")
            else:
                # Show the invite link
                invite_url = f"https://admin.mushucorp.com/join/{invite['invite_token']}"
                console.print(f"  Role: {invite['role']}")
                console.print()
                console.print("[yellow]Share this link:[/yellow]")
                console.print(f"  {invite_url}")

            if invite.get("expires_at"):
                console.print(f"  Expires: {invite['expires_at'][:10]}")

        elif response.status_code == 403:
            console.print("[red]✗ Admin access required[/red]")
            raise typer.Exit(1)
        elif response.status_code == 400:
            error = response.json()
            console.print(f"[red]✗ {error.get('detail', 'Bad request')}[/red]")
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


@invites_app.command("list")
def list_invites(
    org_id: str = typer.Argument(..., help="Organization ID"),
    pending: bool = typer.Option(True, "--pending/--all", help="Show only pending invites"),
):
    """List invites for an organization."""
    tokens, config = require_auth()

    try:
        url = f"{config.auth_url}/orgs/{org_id}/invites"
        if pending:
            url += "?status=pending"

        with httpx.Client() as client:
            response = client.get(
                url,
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            data = response.json()
            invites = data.get("invites", [])

            if not invites:
                console.print("[dim]No invites found.[/dim]")
                return

            table = Table(title="Invites")
            table.add_column("ID", style="cyan")
            table.add_column("Type")
            table.add_column("Email/Link")
            table.add_column("Role")
            table.add_column("Status")
            table.add_column("Expires")

            for inv in invites:
                status_style = {
                    "pending": "[yellow]pending[/yellow]",
                    "accepted": "[green]accepted[/green]",
                    "cancelled": "[dim]cancelled[/dim]",
                    "expired": "[red]expired[/red]",
                }.get(inv["status"], inv["status"])

                table.add_row(
                    inv["invite_id"],
                    inv["invite_type"],
                    inv.get("email") or "[link]",
                    inv["role"],
                    status_style,
                    inv.get("expires_at", "-")[:10] if inv.get("expires_at") else "-",
                )

            console.print(table)

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


@invites_app.command("cancel")
def cancel_invite(
    org_id: str = typer.Argument(..., help="Organization ID"),
    invite_id: str = typer.Argument(..., help="Invite ID to cancel"),
):
    """Cancel a pending invite."""
    tokens, config = require_auth()

    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{config.auth_url}/orgs/{org_id}/invites/{invite_id}",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            console.print("[green]✓ Invite cancelled[/green]")
        elif response.status_code == 404:
            console.print("[red]✗ Invite not found or already used[/red]")
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


@invites_app.command("accept")
def accept_invite(
    token: str = typer.Argument(..., help="Invite token from invite link"),
):
    """Accept an invite to join an organization."""
    tokens, config = require_auth()

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.auth_url}/invites/{token}/accept",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            member = response.json()
            console.print("[green]✓ You've joined the organization![/green]")
            console.print(f"  Organization: {member['org_id']}")
            console.print(f"  Role: {member['role']}")
        elif response.status_code == 400:
            error = response.json()
            console.print(f"[red]✗ {error.get('detail', 'Could not accept invite')}[/red]")
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
