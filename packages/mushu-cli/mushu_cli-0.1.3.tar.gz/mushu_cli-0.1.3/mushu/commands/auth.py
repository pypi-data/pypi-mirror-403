"""Authentication commands."""

import http.server
import socket
import socketserver
import threading
import urllib.parse
import webbrowser

import httpx
import jwt
import typer
from datetime import datetime, UTC
from rich.console import Console
from rich.table import Table

from mushu.config import StoredTokens, get_config

app = typer.Typer(help="Authentication commands")
console = Console()


class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handle OAuth callback from the auth server."""

    tokens: dict | None = None
    error: str | None = None

    def log_message(self, format, *args):
        """Suppress HTTP server logs."""
        pass

    def do_GET(self):
        """Handle GET request with OAuth tokens."""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "access_token" in params and "refresh_token" in params:
            OAuthCallbackHandler.tokens = {
                "access_token": params["access_token"][0],
                "refresh_token": params["refresh_token"][0],
            }
            self._send_success_page()
        elif "error" in params:
            OAuthCallbackHandler.error = params.get("error_description", params["error"])[0]
            self._send_error_page(OAuthCallbackHandler.error)
        else:
            OAuthCallbackHandler.error = "No tokens received"
            self._send_error_page("Authentication failed: no tokens received")

    def _send_success_page(self):
        """Send success HTML response."""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Mushu - Signed In</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .box {
            background: white;
            padding: 3rem;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            text-align: center;
        }
        h1 { color: #22c55e; margin-bottom: 0.5rem; }
        p { color: #666; margin-top: 0; }
        .close { color: #999; font-size: 0.9rem; margin-top: 1.5rem; }
    </style>
</head>
<body>
    <div class="box">
        <h1>✓ Signed In</h1>
        <p>You're now authenticated with Mushu.</p>
        <p class="close">You can close this window and return to the terminal.</p>
    </div>
</body>
</html>"""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def _send_error_page(self, message: str):
        """Send error HTML response."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Mushu - Error</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #f5f5f5;
        }}
        .box {{
            background: white;
            padding: 3rem;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            text-align: center;
        }}
        h1 {{ color: #ef4444; margin-bottom: 0.5rem; }}
        p {{ color: #666; }}
    </style>
</head>
<body>
    <div class="box">
        <h1>Authentication Error</h1>
        <p>{message}</p>
    </div>
</body>
</html>"""
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())


def _find_free_port() -> int:
    """Find an available port for the OAuth callback server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


@app.command("login")
def login(
    no_browser: bool = typer.Option(
        False, "--no-browser", help="Print URL instead of opening browser"
    ),
):
    """
    Sign in with Apple (opens browser).

    Opens your default browser for Apple Sign In. After authentication,
    the browser will redirect back to the CLI to complete login.
    """
    config = get_config()
    console.print(f"[dim]Auth API: {config.auth_url}[/dim]")
    console.print()

    # Reset handler state
    OAuthCallbackHandler.tokens = None
    OAuthCallbackHandler.error = None

    # Find a free port for the callback server
    port = _find_free_port()
    redirect_uri = f"http://localhost:{port}/callback"

    # Build OAuth authorize URL
    authorize_url = (
        f"{config.auth_url}/auth/apple/authorize?redirect_uri={urllib.parse.quote(redirect_uri)}"
    )

    # Start local server in background
    class ReusableServer(socketserver.TCPServer):
        allow_reuse_address = True

    server = ReusableServer(("localhost", port), OAuthCallbackHandler)

    def run_server():
        server.handle_request()  # Handle single request then stop

    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()

    # Open browser or print URL
    if no_browser:
        console.print("[bold]Open this URL in your browser:[/bold]")
    else:
        console.print("[bold]Opening browser for Apple Sign In...[/bold]")
        webbrowser.open(authorize_url)

    console.print()
    console.print(f"[dim]{authorize_url}[/dim]")
    console.print()
    console.print(f"[dim]Waiting for authentication on port {port}...[/dim]")
    console.print("[dim]Press Ctrl+C to cancel[/dim]")

    try:
        # Wait for the server to handle the callback
        server_thread.join(timeout=300)  # 5 minute timeout

        if OAuthCallbackHandler.tokens:
            tokens_data = OAuthCallbackHandler.tokens

            # Validate token and get user info
            try:
                with httpx.Client() as client:
                    response = client.get(
                        f"{config.auth_url}/auth/validate",
                        headers={"Authorization": f"Bearer {tokens_data['access_token']}"},
                        timeout=10,
                    )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("valid"):
                        tokens = StoredTokens(
                            access_token=tokens_data["access_token"],
                            refresh_token=tokens_data["refresh_token"],
                            user_id=data.get("user_id"),
                            email=data.get("email"),
                        )
                        tokens.save()

                        console.print()
                        console.print("[green]✓ Logged in successfully[/green]")
                        if data.get("user_id"):
                            console.print(f"  User ID: {data.get('user_id')}")
                        if data.get("email"):
                            console.print(f"  Email: {data.get('email')}")
                    else:
                        console.print("[red]✗ Token validation failed[/red]")
                        raise typer.Exit(1)
                else:
                    console.print(f"[red]✗ Validation failed: {response.status_code}[/red]")
                    raise typer.Exit(1)

            except httpx.RequestError as e:
                console.print(f"[red]Network error: {e}[/red]")
                raise typer.Exit(1)

        elif OAuthCallbackHandler.error:
            console.print()
            console.print(f"[red]✗ Authentication failed: {OAuthCallbackHandler.error}[/red]")
            raise typer.Exit(1)
        else:
            console.print()
            console.print("[yellow]Authentication timed out or was cancelled.[/yellow]")
            raise typer.Exit(1)

    except KeyboardInterrupt:
        console.print()
        console.print("[yellow]Login cancelled.[/yellow]")
        raise typer.Exit(1)
    finally:
        server.server_close()


@app.command("login-manual")
def login_manual():
    """Manually enter tokens for testing."""
    config = get_config()
    console.print("[yellow]Manual token entry for testing[/yellow]")
    console.print()

    access_token = typer.prompt("Access token")
    refresh_token = typer.prompt("Refresh token")

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.auth_url}/auth/validate",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            data = response.json()
            if data.get("valid"):
                tokens = StoredTokens(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    user_id=data.get("user_id"),
                    email=data.get("email"),
                )
                tokens.save()

                console.print("[green]✓ Logged in successfully[/green]")
                console.print(f"  User ID: {data.get('user_id')}")
                if data.get("email"):
                    console.print(f"  Email: {data.get('email')}")
            else:
                console.print("[red]✗ Token validation failed[/red]")
                raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Validation failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("logout")
def logout():
    """Sign out and clear stored tokens."""
    tokens = StoredTokens.load()
    config = get_config()

    if not tokens:
        console.print("[yellow]Not logged in.[/yellow]")
        return

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.auth_url}/auth/logout",
                json={
                    "access_token": tokens.access_token,
                    "refresh_token": tokens.refresh_token,
                },
                timeout=10,
            )

        if response.status_code == 200:
            console.print("[green]✓ Logged out from server[/green]")
        else:
            console.print("[yellow]Could not logout from server[/yellow]")

    except httpx.RequestError:
        console.print("[yellow]Could not reach server[/yellow]")

    StoredTokens.clear()
    console.print("[green]✓ Local tokens cleared[/green]")


@app.command("status")
def status():
    """Show current authentication status."""
    tokens = StoredTokens.load()
    config = get_config()

    console.print(f"[dim]Auth API: {config.auth_url}[/dim]")

    if not tokens:
        console.print("[yellow]Not logged in[/yellow]")
        return

    console.print("[green]Logged in[/green]")
    if tokens.user_id:
        console.print(f"  User ID: {tokens.user_id}")
    if tokens.email:
        console.print(f"  Email: {tokens.email}")


@app.command("token")
def show_token():
    """Display current session token info."""
    tokens = StoredTokens.load()

    if not tokens:
        console.print("[yellow]Not logged in. Run 'mushu auth login' first.[/yellow]")
        raise typer.Exit(1)

    try:
        claims = jwt.decode(tokens.access_token, options={"verify_signature": False})

        table = Table(title="Session Token")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("User ID", claims.get("sub", "N/A"))
        table.add_row("Session ID", claims.get("sid", "N/A"))
        table.add_row("Issuer", claims.get("iss", "N/A"))

        exp = claims.get("exp")
        if exp:
            exp_dt = datetime.fromtimestamp(exp, UTC)
            now = datetime.now(UTC)
            if exp_dt > now:
                delta = exp_dt - now
                hours = int(delta.total_seconds() // 3600)
                mins = int((delta.total_seconds() % 3600) // 60)
                table.add_row("Expires", f"{hours}h {mins}m remaining")
            else:
                table.add_row("Expires", "[red]EXPIRED[/red]")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error decoding token: {e}[/red]")
        raise typer.Exit(1)


@app.command("refresh")
def refresh():
    """Refresh session tokens."""
    tokens = StoredTokens.load()
    config = get_config()

    if not tokens:
        console.print("[yellow]Not logged in.[/yellow]")
        raise typer.Exit(1)

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.auth_url}/auth/refresh",
                json={
                    "access_token": tokens.access_token,
                    "refresh_token": tokens.refresh_token,
                },
                timeout=10,
            )

        if response.status_code == 200:
            data = response.json()
            new_tokens = StoredTokens(
                access_token=data["tokens"]["access_token"],
                refresh_token=data["tokens"]["refresh_token"],
                user_id=data["user"]["user_id"],
                email=data["user"].get("email"),
            )
            new_tokens.save()
            console.print("[green]✓ Token refreshed[/green]")
        else:
            console.print(f"[red]✗ Refresh failed: {response.status_code}[/red]")
            if response.status_code == 401:
                console.print("[yellow]Session expired. Please login again.[/yellow]")
                StoredTokens.clear()
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("user")
def user_info():
    """Show current user profile."""
    tokens = StoredTokens.load()
    config = get_config()

    if not tokens:
        console.print("[yellow]Not logged in.[/yellow]")
        raise typer.Exit(1)

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.auth_url}/users/me",
                headers={"Authorization": f"Bearer {tokens.access_token}"},
                timeout=10,
            )

        if response.status_code == 200:
            user = response.json()

            table = Table(title="User Profile")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("User ID", user.get("user_id", "N/A"))
            table.add_row("Type", user.get("user_type", "N/A"))
            table.add_row("Email", user.get("email") or "[dim]N/A[/dim]")
            table.add_row("Verified", "Yes" if user.get("email_verified") else "No")
            table.add_row("Name", user.get("name") or "[dim]N/A[/dim]")
            table.add_row("Created", user.get("created_at", "N/A")[:10])

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
