"""Payment tenant management commands."""

import typer
import httpx
from rich.console import Console
from rich.table import Table

from mushu.config import get_auth_token, get_config

app = typer.Typer(help="Payment tenant management commands")
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
    name: str = typer.Option(..., "--name", "-n", help="Tenant name"),
    stripe_key: str = typer.Option(..., "--stripe-key", "-k", help="Stripe secret key"),
    webhook_secret: str = typer.Option(
        None, "--webhook-secret", "-w", help="Stripe webhook secret"
    ),
):
    """Create a new pay tenant for an organization."""
    config = get_config()

    org_id = org_id or config.default_org
    if not org_id:
        console.print("[red]No org specified. Use --org or set default with 'mushu org use'[/red]")
        raise typer.Exit(1)

    headers = get_headers()

    payload = {
        "org_id": org_id,
        "name": name,
        "mode": "direct",
        "stripe_secret_key": stripe_key,
    }
    if webhook_secret:
        payload["stripe_webhook_secret"] = webhook_secret

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.pay_url}/pay-tenants",
                headers=headers,
                json=payload,
                timeout=30,
            )

        if response.status_code == 200:
            tenant = response.json()
            console.print("[green]✓ Pay tenant created[/green]")
            console.print(f"  Tenant ID: {tenant['tenant_id']}")
            console.print(f"  Name: {tenant['name']}")
            console.print(
                f"  Stripe: {'Connected' if tenant['has_stripe_key'] else 'Not Connected'}"
            )

            config.default_pay_tenant = tenant["tenant_id"]
            config.save()
            console.print("[dim]Set as default pay tenant[/dim]")

        elif response.status_code == 400:
            console.print(f"[red]✗ Invalid: {response.json().get('detail')}[/red]")
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
    """List pay tenants for an organization."""
    config = get_config()

    org_id = org_id or config.default_org
    if not org_id:
        console.print("[red]No org specified. Use --org or set default with 'mushu org use'[/red]")
        raise typer.Exit(1)

    headers = get_headers()

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.pay_url}/pay-tenants?org_id={org_id}",
                headers=headers,
                timeout=10,
            )

        if response.status_code == 200:
            tenants = response.json().get("tenants", [])

            if not tenants:
                console.print("[yellow]No pay tenants found for this organization.[/yellow]")
                return

            table = Table(title=f"Pay Tenants (org: {org_id})")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Stripe")
            table.add_column("Mode")
            table.add_column("Default")

            for t in tenants:
                is_default = "★" if t["tenant_id"] == config.default_pay_tenant else ""
                table.add_row(
                    t["tenant_id"],
                    t["name"],
                    "✓" if t["has_stripe_key"] else "✗",
                    t["mode"],
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


@app.command("use")
def use_tenant(
    tenant_id: str = typer.Argument(..., help="Pay tenant ID to set as default"),
):
    """Set default pay tenant."""
    config = get_config()
    config.default_pay_tenant = tenant_id
    config.save()
    console.print(f"[green]✓ Default pay tenant set to: {tenant_id}[/green]")


@app.command("products")
def list_products(
    tenant_id: str = typer.Argument(None, help="Pay tenant ID (uses default if not specified)"),
):
    """List products for a pay tenant."""
    config = get_config()
    tenant_id = tenant_id or config.default_pay_tenant

    if not tenant_id:
        console.print(
            "[red]No pay tenant specified. Use argument or set default with 'mushu pay use'[/red]"
        )
        raise typer.Exit(1)

    headers = get_headers()

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.pay_url}/pay-tenants/{tenant_id}/products",
                headers=headers,
                timeout=10,
            )

        if response.status_code == 200:
            products = response.json().get("products", [])

            if not products:
                console.print("[yellow]No products found.[/yellow]")
                return

            table = Table(title=f"Products (tenant: {tenant_id})")
            table.add_column("ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Price")
            table.add_column("Credits")
            table.add_column("Type")
            table.add_column("Active")

            for p in products:
                price = f"${p['price_cents'] / 100:.2f}"
                credits = str(p.get("credits") or "-")
                table.add_row(
                    p["product_id"],
                    p["name"],
                    price,
                    credits,
                    p["billing_model"],
                    "✓" if p["active"] else "✗",
                )

            console.print(table)

        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("add-product")
def add_product(
    tenant_id: str = typer.Option(
        None, "--tenant", "-t", help="Pay tenant ID (uses default if not specified)"
    ),
    name: str = typer.Option(..., "--name", "-n", help="Product name"),
    price: int = typer.Option(..., "--price", "-p", help="Price in cents (1000 = $10)"),
    credits: int = typer.Option(..., "--credits", "-c", help="Credits to grant"),
):
    """Add a product (one-time credit pack)."""
    config = get_config()
    tenant_id = tenant_id or config.default_pay_tenant

    if not tenant_id:
        console.print(
            "[red]No pay tenant specified. Use --tenant or set default with 'mushu pay use'[/red]"
        )
        raise typer.Exit(1)

    headers = get_headers()

    payload = {
        "name": name,
        "billing_model": "one_time",
        "price_cents": price,
        "credits": credits,
    }

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.pay_url}/pay-tenants/{tenant_id}/products",
                headers=headers,
                json=payload,
                timeout=30,
            )

        if response.status_code == 200:
            product = response.json()
            console.print("[green]✓ Product created[/green]")
            console.print(f"  Product ID: {product['product_id']}")
            console.print(f"  Name: {product['name']}")
            console.print(f"  Price: ${product['price_cents'] / 100:.2f}")
            console.print(f"  Credits: {product['credits']}")

        else:
            err = response.json().get("detail", "Unknown error")
            console.print(f"[red]✗ Failed: {err}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("balance")
def check_balance(
    tenant_id: str = typer.Option(
        None, "--tenant", "-t", help="Pay tenant ID (uses default if not specified)"
    ),
    customer_id: str = typer.Option(
        None, "--customer", "-c", help="Customer ID (uses current org if not specified)"
    ),
):
    """Check credit balance for a customer."""
    config = get_config()
    tenant_id = tenant_id or config.default_pay_tenant
    customer_id = customer_id or config.default_org

    if not tenant_id:
        console.print(
            "[red]No pay tenant specified. Use --tenant or set default with 'mushu pay use'[/red]"
        )
        raise typer.Exit(1)

    if not customer_id:
        console.print(
            "[red]No customer ID specified. Use --customer or set default org with 'mushu org use'[/red]"
        )
        raise typer.Exit(1)

    headers = get_headers()

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.pay_url}/pay-tenants/{tenant_id}/customers/{customer_id}",
                headers=headers,
                timeout=10,
            )

        if response.status_code == 200:
            customer = response.json()
            balance = customer.get("credit_balance", 0)

            if balance < 20:
                console.print(f"[red]Credit Balance: {balance:,}[/red]")
                console.print(
                    "[yellow]⚠ Balance is low. Consider purchasing more credits.[/yellow]"
                )
            else:
                console.print(f"[green]Credit Balance: {balance:,}[/green]")

        elif response.status_code == 404:
            console.print("[yellow]Customer not found (no balance yet)[/yellow]")
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("transactions")
def list_transactions(
    tenant_id: str = typer.Option(
        None, "--tenant", "-t", help="Pay tenant ID (uses default if not specified)"
    ),
    customer_id: str = typer.Option(
        None, "--customer", "-c", help="Customer ID (uses current org if not specified)"
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of transactions to show"),
):
    """List transactions for a customer."""
    config = get_config()
    tenant_id = tenant_id or config.default_pay_tenant
    customer_id = customer_id or config.default_org

    if not tenant_id:
        console.print(
            "[red]No pay tenant specified. Use --tenant or set default with 'mushu pay use'[/red]"
        )
        raise typer.Exit(1)

    if not customer_id:
        console.print(
            "[red]No customer ID specified. Use --customer or set default org with 'mushu org use'[/red]"
        )
        raise typer.Exit(1)

    headers = get_headers()

    try:
        with httpx.Client() as client:
            response = client.get(
                f"{config.pay_url}/pay-tenants/{tenant_id}/customers/{customer_id}/transactions?limit={limit}",
                headers=headers,
                timeout=10,
            )

        if response.status_code == 200:
            transactions = response.json().get("transactions", [])

            if not transactions:
                console.print("[yellow]No transactions found.[/yellow]")
                return

            table = Table(title=f"Transactions (customer: {customer_id})")
            table.add_column("Date", style="dim")
            table.add_column("Type")
            table.add_column("Amount", justify="right")
            table.add_column("Balance", justify="right")
            table.add_column("Description")

            for t in transactions:
                amount = t["amount"]
                amount_str = f"+{amount}" if amount >= 0 else str(amount)
                amount_style = "green" if amount >= 0 else "red"
                date = t["created_at"][:10]
                table.add_row(
                    date,
                    t["type"],
                    f"[{amount_style}]{amount_str}[/{amount_style}]",
                    str(t["balance_after"]),
                    t["description"][:40],
                )

            console.print(table)

        elif response.status_code == 404:
            console.print("[yellow]Customer not found.[/yellow]")
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("auto-refill")
def configure_auto_refill(
    tenant_id: str = typer.Option(
        None, "--tenant", "-t", help="Pay tenant ID (uses default if not specified)"
    ),
    customer_id: str = typer.Option(
        None, "--customer", "-c", help="Customer ID (uses current org if not specified)"
    ),
    enable: bool = typer.Option(None, "--enable/--disable", help="Enable or disable auto-refill"),
    product_id: str = typer.Option(
        None, "--product", "-p", help="Product to purchase for auto-refill"
    ),
    threshold: int = typer.Option(
        None, "--threshold", help="Balance threshold to trigger auto-refill"
    ),
):
    """Configure auto-refill for a customer."""
    config = get_config()
    tenant_id = tenant_id or config.default_pay_tenant
    customer_id = customer_id or config.default_org

    if not tenant_id:
        console.print(
            "[red]No pay tenant specified. Use --tenant or set default with 'mushu pay use'[/red]"
        )
        raise typer.Exit(1)

    if not customer_id:
        console.print(
            "[red]No customer ID specified. Use --customer or set default org with 'mushu org use'[/red]"
        )
        raise typer.Exit(1)

    # If no enable/disable flag, show current status
    if enable is None:
        headers = get_headers()
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{config.pay_url}/pay-tenants/{tenant_id}/customers/{customer_id}",
                    headers=headers,
                    timeout=10,
                )

            if response.status_code == 200:
                customer = response.json()
                console.print("[bold]Auto-Refill Status[/bold]")
                console.print(
                    f"  Enabled: {'Yes' if customer.get('auto_refill_enabled') else 'No'}"
                )
                console.print(f"  Product: {customer.get('auto_refill_product_id') or 'Not set'}")
                console.print(f"  Threshold: {customer.get('auto_refill_threshold', 0)}")
                console.print(
                    f"  Payment Method: {'Saved' if customer.get('has_payment_method') else 'Not saved'}"
                )
            elif response.status_code == 404:
                console.print("[yellow]Customer not found.[/yellow]")
            else:
                console.print(f"[red]✗ Failed: {response.status_code}[/red]")
                raise typer.Exit(1)
        except httpx.RequestError as e:
            console.print(f"[red]Network error: {e}[/red]")
            raise typer.Exit(1)
        return

    # Configure auto-refill
    headers = get_headers()
    payload = {"enabled": enable}
    if enable:
        if not product_id:
            console.print("[red]--product is required when enabling auto-refill[/red]")
            raise typer.Exit(1)
        payload["product_id"] = product_id
        payload["threshold"] = threshold or 10

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.pay_url}/pay-tenants/{tenant_id}/customers/{customer_id}/auto-refill",
                headers=headers,
                json=payload,
                timeout=10,
            )

        if response.status_code == 200:
            if enable:
                console.print("[green]✓ Auto-refill enabled[/green]")
                console.print(f"  Product: {product_id}")
                console.print(f"  Threshold: {payload.get('threshold')}")
            else:
                console.print("[yellow]Auto-refill disabled[/yellow]")
        elif response.status_code == 400:
            err = response.json().get("detail", "Unknown error")
            console.print(f"[red]✗ {err}[/red]")
            if "payment method" in err.lower():
                console.print(
                    "[dim]Tip: Customer must save a payment method first via Stripe SetupIntent[/dim]"
                )
            raise typer.Exit(1)
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)


@app.command("api-key")
def create_api_key(
    tenant_id: str = typer.Argument(None, help="Pay tenant ID (uses default if not specified)"),
    name: str = typer.Option("default", "--name", "-n", help="Key name"),
):
    """Create an API key for a pay tenant."""
    config = get_config()
    tenant_id = tenant_id or config.default_pay_tenant

    if not tenant_id:
        console.print(
            "[red]No pay tenant specified. Use argument or set default with 'mushu pay use'[/red]"
        )
        raise typer.Exit(1)

    headers = get_headers()

    try:
        with httpx.Client() as client:
            response = client.post(
                f"{config.pay_url}/pay-tenants/{tenant_id}/api-keys",
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
            console.print(f"  {key['api_key']}")
        else:
            console.print(f"[red]✗ Failed: {response.status_code}[/red]")
            raise typer.Exit(1)

    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        raise typer.Exit(1)
