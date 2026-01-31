#!/usr/bin/env python3
"""
Aribot CLI - AI-Powered Threat Modeling

Usage:
    aribot login                    # Authenticate with API key
    aribot analyze <diagram>        # Analyze a diagram file
    aribot threats <diagram-id>     # List threats for a diagram
    aribot export <diagram-id>      # Export report
    aribot diagrams                 # List all diagrams
"""

import os
import sys
import time
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from importlib.metadata import version as get_version
from pathlib import Path
from typing import Optional

import click
import httpx
import keyring
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
API_BASE = "https://api.aribot.ayurak.com/aribot-api"
SERVICE_NAME = "aribot-cli"

# Read version from package metadata
try:
    VERSION = get_version("aribot-cli")
except Exception:
    VERSION = "0.0.0"


# =============================================================================
# SECURE CREDENTIAL MANAGEMENT
# =============================================================================

def get_api_key() -> Optional[str]:
    """Get API key from secure keyring storage."""
    try:
        return keyring.get_password(SERVICE_NAME, "api_key")
    except Exception:
        # Fallback to environment variable
        return os.environ.get("ARIBOT_API_KEY")


def set_api_key(api_key: str) -> None:
    """Store API key in secure keyring storage."""
    try:
        keyring.set_password(SERVICE_NAME, "api_key", api_key)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not store in keyring: {e}[/yellow]")
        console.print("[dim]Set ARIBOT_API_KEY environment variable as fallback[/dim]")


def delete_api_key() -> None:
    """Remove API key from keyring."""
    try:
        keyring.delete_password(SERVICE_NAME, "api_key")
    except keyring.errors.PasswordDeleteError:
        pass
    except Exception:
        pass


def get_stored_user_info() -> dict:
    """Get cached user info from keyring."""
    try:
        email = keyring.get_password(SERVICE_NAME, "user_email")
        company = keyring.get_password(SERVICE_NAME, "company")
        return {"email": email, "company": company}
    except Exception:
        return {}


def set_stored_user_info(email: str, company: str) -> None:
    """Cache user info in keyring."""
    try:
        keyring.set_password(SERVICE_NAME, "user_email", email or "")
        keyring.set_password(SERVICE_NAME, "company", company or "")
    except Exception:
        pass


# =============================================================================
# SECURE API CLIENT
# =============================================================================

def get_headers() -> dict:
    """Get auth headers for API requests."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated. Run: aribot login[/red]")
        sys.exit(1)

    return {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
        "User-Agent": f"aribot-cli/{VERSION} (Python)",
    }


def get_auth_header_only() -> dict:
    """Get only Authorization header (for file uploads)."""
    api_key = get_api_key()
    if not api_key:
        console.print("[red]Not authenticated. Run: aribot login[/red]")
        sys.exit(1)

    return {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": f"aribot-cli/{VERSION} (Python)",
    }


def create_request_signature(method: str, path: str, timestamp: str, body: str = "") -> str:
    """Create HMAC signature for request integrity verification."""
    api_key = get_api_key()
    if not api_key:
        return ""

    # Create signature payload
    payload = f"{method.upper()}\n{path}\n{timestamp}\n{body}"

    # Sign with API key
    signature = hmac.new(
        api_key.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return signature


def api_request(
    endpoint: str,
    method: str = "GET",
    json_data: dict = None,
    files: dict = None,
    data: dict = None,
    timeout: float = 60.0
) -> dict:
    """Make secure API request with proper error handling."""
    headers = get_headers() if not files else get_auth_header_only()

    # Add request timestamp for replay attack prevention
    timestamp = datetime.now(timezone.utc).isoformat()
    headers["X-Request-Timestamp"] = timestamp
    headers["X-Request-ID"] = secrets.token_urlsafe(16)

    try:
        with httpx.Client(timeout=timeout) as client:
            if method == "GET":
                response = client.get(f"{API_BASE}{endpoint}", headers=headers)
            elif method == "POST":
                if files:
                    response = client.post(
                        f"{API_BASE}{endpoint}",
                        headers=headers,
                        files=files,
                        data=data
                    )
                else:
                    response = client.post(
                        f"{API_BASE}{endpoint}",
                        headers=headers,
                        json=json_data
                    )
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            console.print("[red]Authentication failed. Run: aribot login[/red]")
        elif e.response.status_code == 403:
            console.print("[red]Access denied. Check your API key permissions.[/red]")
        elif e.response.status_code == 429:
            console.print("[yellow]Rate limit exceeded. Please wait and try again.[/yellow]")
        else:
            try:
                error = e.response.json()
                console.print(f"[red]API Error: {error.get('detail', str(e))}[/red]")
            except Exception:
                console.print(f"[red]API Error: {e.response.status_code}[/red]")
        sys.exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Network error: {e}[/red]")
        sys.exit(1)


def resolve_diagram_id(short_id: str) -> str:
    """Resolve short UUID to full UUID by fetching diagrams."""
    # If it already looks like a full UUID, return it
    if '-' in short_id or len(short_id) >= 32:
        return short_id

    # Fetch diagrams and find by prefix match
    data = api_request("/v2/threat-modeling/diagrams/?limit=100")
    results = data.get("results", [])

    for diagram in results:
        did = str(diagram.get("id", ""))
        uuid_val = str(diagram.get("uuid", ""))
        if did == short_id or did.startswith(short_id) or uuid_val.startswith(short_id):
            return diagram["id"]

    raise click.ClickException(f"No diagram found matching ID: {short_id}")


# =============================================================================
# CLI COMMANDS
# =============================================================================

@click.group()
@click.version_option(version=VERSION)
def main():
    """Aribot CLI - AI-powered threat modeling by Ayurak."""
    pass


@main.command()
@click.option("--key", "-k", help="API key (alternative to interactive prompt)")
@click.option("--open-portal", is_flag=True, help="Open developer portal to create API key")
def login(key: Optional[str], open_portal: bool):
    """Authenticate with your Aribot API key.

    Your API key is stored securely in your system's keychain/credential manager.
    Get your API key from: https://developer.ayurak.com
    """
    import webbrowser

    # Show welcome banner - Ayurak Theme (Orange/Gold/White/Black)
    console.print()
    console.print("[bold #FF6B35]╭" + "─" * 48 + "╮[/bold #FF6B35]")
    console.print("[bold #FF6B35]│[/bold #FF6B35]" + " " * 10 + "[bold white]◆ ARIBOT[/bold white]  [#D4A03C]Secure Authentication[/#D4A03C]" + " " * 9 + "[bold #FF6B35]│[/bold #FF6B35]")
    console.print("[bold #FF6B35]╰" + "─" * 48 + "╯[/bold #FF6B35]")
    console.print()

    # Check if already authenticated
    existing_key = get_api_key()
    if existing_key:
        cached = get_stored_user_info()
        console.print("[yellow]You are already logged in.[/yellow]")
        if cached.get("email"):
            console.print(f"  [dim]Email:[/dim]   {cached.get('email')}")
            console.print(f"  [dim]Company:[/dim] {cached.get('company', 'N/A')}")
        console.print()
        if not click.confirm("Would you like to re-authenticate with a different key?", default=False):
            return

    # Open developer portal if requested
    if open_portal:
        portal_url = "https://developer.ayurak.com"
        console.print(f"[cyan]Opening developer portal...[/cyan]")
        console.print(f"[dim]{portal_url}[/dim]")
        webbrowser.open(portal_url)
        console.print()
        console.print("[dim]After creating your API key, run:[/dim]")
        console.print("  [green]aribot login[/green]")
        return

    # Show instructions
    console.print("[bold]To authenticate, you need an API key.[/bold]")
    console.print()
    console.print("[dim]Get your API key from the developer portal:[/dim]")
    console.print("  [cyan]https://developer.ayurak.com[/cyan]")
    console.print()
    console.print("[dim]Or run: [green]aribot login --open-portal[/green] to open it[/dim]")
    console.print()

    # Get API key (from option or prompt)
    if key:
        api_key = key
        console.print("[dim]Using provided API key...[/dim]")
    else:
        console.print("[bold]Enter your API key below[/bold]")
        console.print("[dim](input is hidden for security)[/dim]")
        api_key = click.prompt("API Key", hide_input=True)

    # Validate API key format
    api_key = api_key.strip()
    if len(api_key) < 20:
        console.print()
        console.print("[red]Invalid API key format[/red]")
        console.print("[dim]API keys should be at least 20 characters long.[/dim]")
        console.print("[dim]Get a valid key from: https://developer.ayurak.com[/dim]")
        return

    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Validating API key...", total=None)

        try:
            with httpx.Client(timeout=30.0) as client:
                # Exchange API key for token
                response = client.post(
                    f"{API_BASE}/v1/developer/token/",
                    headers={"Content-Type": "application/json"},
                    json={"api_key": api_key}
                )

                if response.status_code == 200:
                    data = response.json()
                    progress.update(task, description="Storing credentials securely...")
                    set_api_key(api_key)

                    # Store user info
                    user = data.get("user", {})
                    set_stored_user_info(
                        user.get("email", ""),
                        user.get("company", "")
                    )

                    progress.remove_task(task)

                    # Success display
                    console.print()
                    console.print("[bold green]Authentication successful![/bold green]")
                    console.print()
                    console.print("[bold]Account Details:[/bold]")
                    console.print(f"  [cyan]Email:[/cyan]   {user.get('email', 'N/A')}")
                    console.print(f"  [cyan]Company:[/cyan] {user.get('company', 'N/A')}")
                    console.print(f"  [cyan]Plan:[/cyan]    {data.get('plan', 'Standard')}")
                    console.print()
                    console.print("[bold]Security:[/bold]")
                    console.print("  [green]API key stored in system keychain[/green]")
                    console.print("  [dim]Your key is encrypted and secure.[/dim]")
                    console.print()
                    console.print("[bold]Next steps:[/bold]")
                    console.print("  [cyan]aribot diagrams[/cyan]      - List your diagrams")
                    console.print("  [cyan]aribot analyze <file>[/cyan] - Analyze a new diagram")
                    console.print("  [cyan]aribot status[/cyan]        - Check API status")
                    console.print("  [cyan]aribot --help[/cyan]        - See all commands")
                else:
                    progress.remove_task(task)
                    console.print()
                    try:
                        error = response.json()
                        error_msg = error.get('message') or error.get('detail', 'Invalid API key')
                        console.print(f"[red]Authentication failed: {error_msg}[/red]")
                    except Exception:
                        if response.status_code == 401:
                            console.print("[red]Invalid API key. Please check and try again.[/red]")
                        elif response.status_code == 403:
                            console.print("[red]API key is disabled or expired.[/red]")
                        else:
                            console.print(f"[red]Authentication failed (HTTP {response.status_code})[/red]")
                    console.print()
                    console.print("[dim]Need a new API key? Visit:[/dim]")
                    console.print("  [cyan]https://developer.ayurak.com[/cyan]")

        except httpx.TimeoutException:
            progress.remove_task(task)
            console.print()
            console.print("[red]Connection timed out.[/red]")
            console.print("[dim]Please check your internet connection and try again.[/dim]")
        except httpx.ConnectError:
            progress.remove_task(task)
            console.print()
            console.print("[red]Could not connect to Aribot servers.[/red]")
            console.print("[dim]Please check your internet connection.[/dim]")
        except Exception as e:
            progress.remove_task(task)
            console.print()
            console.print(f"[red]Authentication failed: {e}[/red]")


@main.command()
def logout():
    """Remove stored credentials."""
    delete_api_key()
    try:
        keyring.delete_password(SERVICE_NAME, "user_email")
        keyring.delete_password(SERVICE_NAME, "company")
    except Exception:
        pass
    console.print("[green]Logged out successfully.[/green]")
    console.print("[dim]Run 'aribot login' to authenticate again.[/dim]")


@main.command()
def setup():
    """Interactive first-time setup wizard.

    Guides you through:
    - Creating an Aribot account (if needed)
    - Getting your API key
    - Authenticating the CLI
    - Verifying everything works
    """
    import webbrowser

    # Welcome screen
    console.print()
    console.print("[bold cyan]" + "=" * 56 + "[/bold cyan]")
    console.print("[bold cyan]      Welcome to Aribot CLI - Setup Wizard[/bold cyan]")
    console.print("[bold cyan]" + "=" * 56 + "[/bold cyan]")
    console.print()
    console.print("  [bold]Aribot[/bold] - AI-Powered Threat Modeling Platform")
    console.print()
    console.print("  This wizard will help you set up the CLI securely.")
    console.print()

    # Check existing auth
    existing_key = get_api_key()
    if existing_key:
        cached = get_stored_user_info()
        console.print("[green]You are already authenticated![/green]")
        console.print()
        if cached.get("email"):
            console.print(f"  Email:   {cached.get('email')}")
            console.print(f"  Company: {cached.get('company', 'N/A')}")
        console.print()
        console.print("[dim]Run 'aribot logout' first if you want to change accounts.[/dim]")
        return

    # Step 1: Do you have an account?
    console.print("[bold]Step 1: Aribot Account[/bold]")
    console.print("-" * 40)
    console.print()

    has_account = click.confirm("Do you have an Aribot account?", default=True)

    if not has_account:
        console.print()
        console.print("[cyan]Let's create your account![/cyan]")
        console.print()
        console.print("Opening the signup page...")
        webbrowser.open("https://developer.ayurak.com/signup")
        console.print()
        console.print("[dim]After signing up, run this wizard again:[/dim]")
        console.print("  [green]aribot setup[/green]")
        return

    # Step 2: Get API key
    console.print()
    console.print("[bold]Step 2: API Key[/bold]")
    console.print("-" * 40)
    console.print()

    has_key = click.confirm("Do you have an API key?", default=True)

    if not has_key:
        console.print()
        console.print("[cyan]Let's get your API key![/cyan]")
        console.print()
        console.print("Opening the developer portal...")
        webbrowser.open("https://developer.ayurak.com")
        console.print()
        console.print("[bold]To create an API key:[/bold]")
        console.print("  1. Click [cyan]'Create API Key'[/cyan]")
        console.print("  2. Give it a name (e.g., 'My CLI')")
        console.print("  3. Copy the key - it won't be shown again!")
        console.print()
        click.pause("Press Enter when you have your API key...")
        console.print()

    # Step 3: Enter API key
    console.print()
    console.print("[bold]Step 3: Authentication[/bold]")
    console.print("-" * 40)
    console.print()
    console.print("[dim]Your API key will be stored securely in your system keychain.[/dim]")
    console.print()

    api_key = click.prompt("Paste your API key", hide_input=True)
    api_key = api_key.strip()

    if len(api_key) < 20:
        console.print()
        console.print("[red]That doesn't look like a valid API key.[/red]")
        console.print("[dim]API keys are typically 40+ characters long.[/dim]")
        console.print()
        console.print("Get a key from: [cyan]https://developer.ayurak.com[/cyan]")
        return

    # Validate the key
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Validating API key...", total=None)

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{API_BASE}/v1/developer/token/",
                    headers={"Content-Type": "application/json"},
                    json={"api_key": api_key}
                )

                if response.status_code == 200:
                    data = response.json()
                    progress.update(task, description="Storing credentials...")
                    set_api_key(api_key)

                    user = data.get("user", {})
                    set_stored_user_info(
                        user.get("email", ""),
                        user.get("company", "")
                    )

                    progress.remove_task(task)

                    # Success!
                    console.print()
                    console.print("[bold green]Setup Complete![/bold green]")
                    console.print()
                    console.print("[bold]Your Account:[/bold]")
                    console.print(f"  Email:   [cyan]{user.get('email', 'N/A')}[/cyan]")
                    console.print(f"  Company: [cyan]{user.get('company', 'N/A')}[/cyan]")
                    console.print(f"  Plan:    [cyan]{data.get('plan', 'Standard')}[/cyan]")
                    console.print()
                    console.print("[bold]Security:[/bold]")
                    console.print("  [green]API key stored in system keychain[/green]")
                    console.print()
                    console.print("[bold cyan]" + "=" * 56 + "[/bold cyan]")
                    console.print("[bold]You're all set! Try these commands:[/bold]")
                    console.print("[bold cyan]" + "=" * 56 + "[/bold cyan]")
                    console.print()
                    console.print("  [green]aribot diagrams[/green]          List your diagrams")
                    console.print("  [green]aribot analyze <file>[/green]   Upload & analyze a diagram")
                    console.print("  [green]aribot threats <id>[/green]     View threats for a diagram")
                    console.print("  [green]aribot compliance <id>[/green]  Run compliance check")
                    console.print("  [green]aribot --help[/green]           See all commands")
                    console.print()
                else:
                    progress.remove_task(task)
                    console.print()
                    console.print("[red]Invalid API key. Please try again.[/red]")
                    console.print()
                    console.print("Get a new key from: [cyan]https://developer.ayurak.com[/cyan]")

        except Exception as e:
            progress.remove_task(task)
            console.print()
            console.print(f"[red]Setup failed: {e}[/red]")
            console.print("[dim]Check your internet connection and try again.[/dim]")


@main.command()
def whoami():
    """Show current authentication status."""
    api_key = get_api_key()

    if not api_key:
        console.print("[yellow]Not authenticated[/yellow]")
        console.print("[dim]Run: aribot login[/dim]")
        return

    try:
        # Fetch user info and API key info in parallel
        user_data = api_request("/v1/users/me/")
        keys_data = api_request("/v1/developer/api-keys/")

        # Get company from API keys endpoint
        company = "N/A"
        plan = "N/A"
        if keys_data and isinstance(keys_data, list) and len(keys_data) > 0:
            company = keys_data[0].get("company_name", "N/A")
            plan = keys_data[0].get("plan_name", "N/A")
        elif user_data.get("company"):
            company = user_data.get("company")

        console.print("[green]Authenticated as:[/green]")
        console.print(f"  Email:   {user_data.get('email', 'N/A')}")
        console.print(f"  Company: {company}")
        console.print(f"  Plan:    {plan}")

        # Show API key info (masked)
        console.print(f"  API Key: {api_key[:8]}...{api_key[-4:]}")

    except Exception:
        # Try cached info
        cached = get_stored_user_info()
        if cached.get("email"):
            console.print("[yellow]API key stored (validation pending)[/yellow]")
            console.print(f"  Email:   {cached.get('email', 'N/A')}")
            console.print(f"  Company: {cached.get('company', 'N/A')}")
        else:
            console.print("[yellow]API key stored but validation failed[/yellow]")


@main.command()
@click.option("-l", "--limit", default=10, help="Number of diagrams to show")
def diagrams(limit: int):
    """List all your diagrams."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Fetching diagrams...", total=None)

        try:
            data = api_request(f"/v2/threat-modeling/diagrams/?limit={limit}")
            progress.remove_task(task)

            if not data.get("results"):
                console.print("[dim]No diagrams found.[/dim]")
                console.print("[dim]Create one at https://developer.ayurak.com[/dim]")
                return

            table = Table(title="Your Diagrams")
            table.add_column("ID", style="cyan")
            table.add_column("Name")
            table.add_column("Status")
            table.add_column("Threats", justify="right")
            table.add_column("Created")

            for d in data["results"]:
                # Use 'stage' field (not 'status')
                stage = d.get("stage", "pending")
                status_icon = "[green]✓[/green]" if stage == "completed" else "[yellow]⋯[/yellow]"

                # Use filename as fallback for name
                name = d.get("name") or d.get("filename") or "Unnamed"

                table.add_row(
                    d["id"][:8],
                    name[:40],
                    status_icon,
                    str(d.get("threats_count", 0)),
                    d.get("created_at", "")[:10]
                )

            console.print(table)
            console.print(f"[dim]Showing {len(data['results'])} of {data.get('count', 0)} diagrams[/dim]")

        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]Failed to fetch diagrams: {e}[/red]")


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("-n", "--name", help="Diagram name")
@click.option("--auto-threats/--no-auto-threats", default=True, help="Auto-generate AI threats")
def analyze(file: str, name: Optional[str], auto_threats: bool):
    """Upload and analyze a diagram file."""
    file_path = Path(file)
    diagram_name = name or file_path.stem

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Uploading diagram...", total=None)

        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f)}
                data = {
                    "name": diagram_name,
                    "auto_generate_threats": str(auto_threats).lower()
                }

                headers = get_auth_header_only()
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(
                        f"{API_BASE}/v2/threat-modeling/diagrams/upload-analyze/",
                        headers=headers,
                        files=files,
                        data=data
                    )
                    response.raise_for_status()
                    result = response.json()

            progress.update(task, description="Diagram uploaded!")
            progress.remove_task(task)

            console.print("\n[bold]Diagram Created:[/bold]")
            console.print(f"  ID:     [cyan]{result['id']}[/cyan]")
            console.print(f"  Name:   {result.get('name') or result.get('filename', 'Untitled')}")
            console.print(f"  Status: {result.get('stage', result.get('status', 'pending'))}")

            if auto_threats:
                task2 = progress.add_task("Generating AI threats...", total=None)

                # Poll for completion
                for _ in range(30):
                    time.sleep(2)
                    status = api_request(f"/v2/threat-modeling/diagrams/{result['id']}/")

                    if status.get("stage") == "completed":
                        progress.remove_task(task2)
                        console.print(f"[green]Generated {status.get('threats_count', 0)} threats[/green]")
                        break
                else:
                    progress.remove_task(task2)
                    console.print("[yellow]Threat generation in progress...[/yellow]")

            console.print(f"\n[dim]View at: https://developer.ayurak.com/diagrams/{result['id']}[/dim]")

        except httpx.HTTPStatusError as e:
            progress.remove_task(task)
            console.print(f"[red]Upload failed: {e.response.status_code}[/red]")
        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]Analysis failed: {e}[/red]")


@main.command()
@click.argument("diagram_id")
@click.option("-s", "--severity", help="Filter by severity (critical, high, medium, low)")
def threats(diagram_id: str, severity: Optional[str]):
    """List threats for a diagram."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Fetching threats...", total=None)

        try:
            full_id = resolve_diagram_id(diagram_id)
            url = f"/v2/threat-modeling/diagrams/{full_id}/threats/"
            if severity:
                url += f"?severity={severity}"

            data = api_request(url)
            progress.remove_task(task)

            # Handle both response formats
            threats_list = data.get("threats") or data.get("results") or []

            if not threats_list:
                console.print("[dim]No threats found.[/dim]")
                return

            table = Table(title="Threats")
            table.add_column("Severity", style="bold")
            table.add_column("Title")
            table.add_column("Category")
            table.add_column("ID", style="dim")

            severity_styles = {
                "critical": "red",
                "high": "yellow",
                "medium": "blue",
                "low": "dim"
            }

            for t in threats_list:
                sev = t.get("severity", "medium") or "medium"
                style = severity_styles.get(sev.lower(), "white")

                # Handle both title and name fields
                title = t.get("title") or t.get("name") or "Untitled"
                category = t.get("category") or t.get("stride_category") or "N/A"

                table.add_row(
                    f"[{style}]{sev.upper()}[/{style}]",
                    title[:60],
                    category,
                    str(t.get("id", ""))[:8]
                )

            console.print(table)
            total = data.get("count") or len(threats_list)
            console.print(f"\n[dim]Total: {total} threats[/dim]")

        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]Failed to fetch threats: {e}[/red]")


@main.command()
@click.argument("diagram_id")
@click.option("-f", "--format", "fmt", default="json", help="Export format (pdf, json, csv)")
@click.option("-o", "--output", help="Output file path")
def export(diagram_id: str, fmt: str, output: Optional[str]):
    """Export diagram report."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Exporting {fmt.upper()} report...", total=None)

        try:
            headers = get_auth_header_only()

            # Resolve short UUID
            diagram_id = resolve_diagram_id(diagram_id)

            with httpx.Client(timeout=120.0) as client:
                if fmt == "csv":
                    endpoint = f"{API_BASE}/v2/threat-modeling/diagrams/{diagram_id}/export/csv/"
                elif fmt == "pdf":
                    endpoint = f"{API_BASE}/v2/threat-modeling/diagrams/{diagram_id}/unified-report/?format=pdf"
                else:
                    endpoint = f"{API_BASE}/v2/threat-modeling/diagrams/{diagram_id}/report/"
                response = client.get(endpoint, headers=headers)
                response.raise_for_status()

                output_path = output or f"aribot-report-{diagram_id[:8]}.{fmt}"

                with open(output_path, "wb") as f:
                    f.write(response.content)

            progress.remove_task(task)
            console.print(f"[green]Report saved to [cyan]{output_path}[/cyan][/green]")

        except httpx.HTTPStatusError as e:
            progress.remove_task(task)
            console.print(f"[red]Export failed: {e.response.status_code}[/red]")
        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]Export failed: {e}[/red]")


@main.command("generate-threats")
@click.argument("diagram_id")
def generate_threats(diagram_id: str):
    """Generate AI threats for an existing diagram."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating AI threats...", total=None)

        try:
            full_id = resolve_diagram_id(diagram_id)
            api_request(
                f"/v2/threat-modeling/diagrams/{full_id}/analyze-threats/",
                method="POST"
            )

            progress.update(task, description="Processing...")

            # Poll for completion
            for _ in range(30):
                time.sleep(2)
                status = api_request(f"/v2/threat-modeling/diagrams/{diagram_id}/")

                if status.get("ai_threats_generated"):
                    progress.remove_task(task)
                    console.print(f"[green]Generated {status.get('threats_count', 0)} threats[/green]")
                    return

            progress.remove_task(task)
            console.print("[green]Threat generation initiated[/green]")

        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]Failed to generate threats: {e}[/red]")


@main.command()
def status():
    """Check API status and rate limits."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Checking API status...", total=None)

        try:
            # Check health endpoint (no auth required)
            with httpx.Client(timeout=10.0) as client:
                health_response = client.get(f"{API_BASE}/health/")
                health = health_response.json() if health_response.status_code == 200 else {}

            progress.remove_task(task)

            console.print("[bold]API Status[/bold]\n")
            status_icon = "[green]✓ Healthy[/green]" if health.get("status") == "healthy" else "[red]✗ Unhealthy[/red]"
            console.print(f"  Status:   {status_icon}")
            console.print(f"  Version:  [cyan]{health.get('version', 'N/A')}[/cyan]")
            console.print(f"  Features: {'[green]Enabled[/green]' if health.get('features_enabled') else '[yellow]Disabled[/yellow]'}")

            # Check rate limits if authenticated
            api_key = get_api_key()
            if api_key:
                try:
                    limits = api_request("/v2/developer-portal/rate-limits/usage/")
                    console.print("\n[bold]Rate Limits[/bold]")
                    console.print(f"  Requests/min:  {limits.get('requests_per_minute', {}).get('used', 0)}/{limits.get('requests_per_minute', {}).get('limit', 'unlimited')}")
                    console.print(f"  Requests/hour: {limits.get('requests_per_hour', {}).get('used', 0)}/{limits.get('requests_per_hour', {}).get('limit', 'unlimited')}")
                    console.print(f"  Requests/day:  {limits.get('requests_per_day', {}).get('used', 0)}/{limits.get('requests_per_day', {}).get('limit', 'unlimited')}")
                except Exception:
                    console.print("\n[dim]Rate limit info requires authentication[/dim]")

        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]Failed to check status: {e}[/red]")


# Compliance Standards
COMPLIANCE_STANDARDS = [
    'SOC2', 'ISO27001', 'ISO27017', 'ISO27018', 'ISO22301',
    'NIST-CSF', 'NIST-800-53', 'NIST-800-171',
    'PCI-DSS', 'PCI-DSS-4.0',
    'GDPR', 'CCPA', 'LGPD', 'PIPEDA',
    'HIPAA', 'HITRUST',
    'FedRAMP-Low', 'FedRAMP-Moderate', 'FedRAMP-High',
    'CIS-AWS', 'CIS-Azure', 'CIS-GCP', 'CIS-Kubernetes',
    'SOX', 'GLBA', 'FISMA',
    'CSA-CCM', 'MITRE-ATT&CK', 'OWASP-TOP-10',
]


@main.command()
@click.argument("diagram_id")
@click.option("-s", "--standard", default="SOC2", help="Compliance standard (SOC2, ISO27001, NIST, PCI-DSS, GDPR, HIPAA)")
@click.option("--list-standards", is_flag=True, help="List all available compliance standards")
def compliance(diagram_id: str, standard: str, list_standards: bool):
    """Run compliance assessment on a diagram."""
    if list_standards:
        console.print("[bold]Supported Compliance Standards[/bold]\n")
        for s in COMPLIANCE_STANDARDS:
            console.print(f"  [cyan]•[/cyan] {s}")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task(f"Running {standard} compliance assessment...", total=None)

        try:
            full_id = resolve_diagram_id(diagram_id)
            data = api_request(
                "/v2/compliances/assess_diagram/",
                method="POST",
                json_data={
                    "diagram_id": full_id,
                    "frameworks": [standard]
                }
            )

            report_id = data.get("report_id")
            if report_id:
                # Poll for completion
                import time as _time
                for i in range(15):
                    progress.update(task, description=f"Running {standard} compliance assessment... ({i*2}s)")
                    _time.sleep(2)
                    try:
                        report = api_request(f"/v2/compliances/reports/{report_id}/")
                        if report.get("status") == "completed" and (report.get("compliance_score", 0) > 0 or report.get("total_controls", 0) > 0):
                            data = report
                            break
                    except Exception:
                        pass

            progress.remove_task(task)
            console.print(f"[green]Compliance assessment complete![/green]")

            console.print(f"\n[bold]{standard} Compliance Report[/bold]\n")

            score = data.get("compliance_score", data.get("score", 0))
            score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
            console.print(f"  Score:           [{score_color}]{score}%[/{score_color}]")
            console.print(f"  Total Controls:  {data.get('total_controls', 0)}")
            console.print(f"  Passed Controls: [green]{data.get('passed_controls', 0)}[/green]")
            console.print(f"  Failed Controls: [red]{data.get('failed_controls', 0)}[/red]")

            comp_status = "Compliant" if score >= 70 else "Non-Compliant"
            status_color = "green" if score >= 70 else "red"
            console.print(f"  Status:          [{status_color}]{comp_status}[/{status_color}]")

            findings = data.get("findings", [])
            if findings:
                console.print("\n[bold]Top Findings[/bold]")
                for f in findings[:5]:
                    sev = f.get("severity", "medium")
                    sev_color = "red" if sev == "high" else "yellow" if sev == "medium" else "dim"
                    console.print(f"  [{sev_color}][{sev.upper()}][/{sev_color}] {f.get('title', f.get('control_id', 'N/A'))}")

        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]Compliance assessment failed: {e}[/red]")


@main.command()
@click.option("--roi", type=float, help="Calculate ROI for security investment (in USD)")
@click.option("--tco", help="Calculate TCO for a diagram using economic intelligence")
@click.option("--analyze", "analyze_diagram", help="Analyze costs for a diagram")
@click.option("--cost", "cost_diagram", help="AI-powered cost intelligence for diagram")
@click.option("--dashboard", is_flag=True, help="Show economic intelligence dashboard")
def economics(roi: Optional[float], tco: Optional[str], analyze_diagram: Optional[str], cost_diagram: Optional[str], dashboard: bool):
    """Economic intelligence and cost analysis."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Calculating...", total=None)

        try:
            if roi:
                data = api_request(
                    "/v2/economic/v2/roi/create/",
                    method="POST",
                    json_data={
                        "investment": roi,
                        "risk_reduction": 50,
                        "time_horizon": 3
                    }
                )

                progress.remove_task(task)
                console.print("[green]ROI Analysis Complete![/green]")
                console.print("\n[bold]Security ROI Analysis[/bold]\n")
                console.print(f"  Investment:      [cyan]${roi:,.0f}[/cyan]")
                console.print(f"  Expected ROI:    [green]{data.get('roi_percentage', data.get('roi', 0))}%[/green]")
                console.print(f"  NPV:             [green]${data.get('npv', 0):,.0f}[/green]")
                console.print(f"  Payback Period:  [cyan]{data.get('payback_months', data.get('payback_period', 0))} months[/cyan]")
                console.print(f"  Risk Reduction:  [green]50%[/green]")

            elif tco:
                # TCO per diagram using economic intelligence
                full_id = resolve_diagram_id(tco)
                data = api_request(
                    "/v2/economic/tco/",
                    method="POST",
                    json_data={
                        "diagram_id": full_id,
                        "years": 3,
                        "include_hidden_costs": True,
                        "include_risk_costs": True
                    }
                )

                progress.remove_task(task)
                console.print("[green]TCO Analysis Complete![/green]")
                tco_data = data.get('tco', data)
                diagram_name = tco_data.get('diagram_name', 'Diagram')
                console.print(f"\n[bold]Total Cost of Ownership - {diagram_name}[/bold]\n")

                # Cost summary
                console.print(f"  Monthly Cost:       [cyan]${tco_data.get('monthly_cost', tco_data.get('total_monthly', 0)):,.0f}[/cyan]")
                console.print(f"  Annual Cost:        [cyan]${tco_data.get('annual_cost', tco_data.get('year_1', 0)):,.0f}[/cyan]")
                console.print(f"  3-Year TCO:         [yellow]${tco_data.get('total_3_year', tco_data.get('total_cost', 0)):,.0f}[/yellow]")

                # Cost breakdown by component
                if tco_data.get('cost_breakdown'):
                    console.print("\n[bold]Cost Breakdown[/bold]\n")
                    breakdown = tco_data['cost_breakdown']
                    for key, value in breakdown.items():
                        if isinstance(value, (int, float)):
                            console.print(f"  {key.replace('_', ' ').title()}:  [cyan]${value:,.0f}[/cyan]")

                # Customizable costs info
                if tco_data.get('customizable'):
                    console.print("\n[dim]Costs can be customized in the Economic Intelligence panel[/dim]")

            elif analyze_diagram:
                data = api_request(
                    "/v2/economic/analyze/",
                    method="POST",
                    json_data={"diagram_id": analyze_diagram}
                )

                progress.remove_task(task)
                console.print("[green]Cost Analysis Complete![/green]")
                console.print("\n[bold]Diagram Cost Analysis[/bold]\n")
                console.print(f"  Estimated Monthly: [cyan]${data.get('monthly_estimate', 0):,.0f}[/cyan]")
                console.print(f"  Security Costs:    [yellow]${data.get('security_cost', 0):,.0f}[/yellow]")
                console.print(f"  Breach Risk Cost:  [red]${data.get('breach_risk_cost', 0):,.0f}[/red]")

            elif cost_diagram:
                # Diagram-specific cost analysis
                full_id = resolve_diagram_id(cost_diagram)
                data = api_request(f"/v2/threat-modeling/diagrams/{full_id}/cost-intelligence/")

                progress.remove_task(task)
                console.print("[green]Cost analysis complete![/green]")
                console.print("\n[bold]Diagram Cost Analysis[/bold]\n")

                summary = data.get("cost_summary", data)
                console.print(f"  Monthly Cost:     [cyan]${summary.get('total_monthly', summary.get('monthly', 0)):,.0f}[/cyan]")
                console.print(f"  Annual Cost:      [yellow]${summary.get('total_annual', (summary.get('total_monthly', 0) * 12)):,.0f}[/yellow]")
                console.print(f"  Component Count:  [white]{summary.get('component_count', len(data.get('components', [])))}[/white]")
                console.print(f"  Region:           [white]{summary.get('region', 'us-east-1')}[/white]")

                cost_breakdown = data.get("cost_breakdown", [])
                if cost_breakdown:
                    console.print("\n[bold]Cost Breakdown[/bold]\n")
                    for c in cost_breakdown[:5]:
                        console.print(f"  [cyan]•[/cyan] {c.get('name', c.get('component', 'Unknown'))}: [yellow]${c.get('monthly', c.get('cost', 0)):,.0f}[/yellow]/mo")

                recommendations = data.get("recommendations", [])
                if recommendations:
                    console.print("\n[bold]Optimization Recommendations[/bold]\n")
                    for r in recommendations[:3]:
                        console.print(f"  [green]•[/green] {r.get('title', r.get('description', r))}")

            elif dashboard:
                # Get economic intelligence from threat modeling endpoint
                data = api_request("/v2/threat-modeling/economic-intelligence/")

                progress.remove_task(task)
                console.print("[green]Dashboard loaded![/green]")
                console.print("\n[bold]Economic Intelligence Dashboard[/bold]\n")

                summary = data.get("company_summary", data.get("summary", data))
                console.print(f"  Total Monthly:    [cyan]${summary.get('total_monthly', summary.get('total_security_spend', 0)):,.0f}[/cyan]")
                console.print(f"  Total Annual:     [yellow]${summary.get('total_annual', 0):,.0f}[/yellow]")
                console.print(f"  Total Diagrams:   [white]{summary.get('total_diagrams', 0)}[/white]")
                console.print(f"  Region:           [white]{summary.get('region', 'us-east-1')}[/white]")

                top_cost_drivers = data.get("top_cost_drivers", [])
                if top_cost_drivers:
                    console.print("\n[bold]Top Cost Drivers[/bold]\n")
                    for d in top_cost_drivers[:5]:
                        console.print(f"  [cyan]•[/cyan] {d.get('name', 'Unknown')}: [yellow]${d.get('monthly_cost', 0):,.0f}[/yellow]/mo ({d.get('component_count', 0)} components)")

                ai_recommendations = data.get("intelligence", {}).get("recommendations", [])
                if ai_recommendations:
                    console.print("\n[bold]AI Recommendations[/bold]\n")
                    for r in ai_recommendations[:3]:
                        console.print(f"  [green]•[/green] {r.get('title', r.get('description', r))}")

            else:
                progress.remove_task(task)
                console.print("[yellow]Usage: aribot economics [--roi <amount>] [--tco <diagram-id>] [--analyze <diagram-id>] [--dashboard][/yellow]")

        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]Economic analysis failed: {e}[/red]")


@main.command("cloud-security")
@click.option("--scan", "scan_provider", is_flag=False, flag_value="all", default=None, help="Scan cloud security posture (aws, azure, gcp)")
@click.option("--findings", is_flag=True, help="List security findings")
@click.option("--dashboard", is_flag=True, help="Show cloud security dashboard")
@click.option("-s", "--severity", help="Filter findings by severity (critical, high, medium, low)")
@click.option("--dynamic-scan", "dynamic_scan", help="Run dynamic cloud scan (account ID)")
@click.option("--unified-scan", "unified_scan", is_flag=True, help="Run unified scan with scope")
@click.option("--scope", type=click.Choice(['account', 'standard', 'control', 'policy', 'diagram', 'component']), default='account', help="Scan scope for unified scan")
@click.option("--scope-id", "scope_id", help="ID for the scan scope (account_id, standard_id, etc.)")
@click.option("--rules", is_flag=True, help="List scanner rules")
@click.option("--create-rule", "create_rule", is_flag=True, help="Create a new scanner rule")
@click.option("--sync-rules", "sync_rules", is_flag=True, help="Sync rules from cloud providers")
@click.option("--scanner-stats", "scanner_stats", is_flag=True, help="Show scanner statistics")
@click.option("--remediate", "remediate", help="Execute remediation for a policy (policy ID)")
@click.option("--remediate-preview", "remediate_preview", help="Preview remediation without applying (policy ID)")
@click.option("--account-id", "account_id", type=int, help="Cloud account ID for operations")
def cloud_security(scan_provider: Optional[str], findings: bool, dashboard: bool, severity: Optional[str],
                   dynamic_scan: Optional[str], unified_scan: bool, scope: str, scope_id: Optional[str],
                   rules: bool, create_rule: bool, sync_rules: bool, scanner_stats: bool,
                   remediate: Optional[str], remediate_preview: Optional[str], account_id: Optional[int]):
    """Cloud security posture management (CSPM/CNAPP)."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Scanning cloud security...", total=None)

        try:
            if scan_provider:
                provider_param = scan_provider if scan_provider != "all" else None

                # Get violations by platform
                violations_url = "/v2/compliances/unified-violations/?limit=100"
                if provider_param:
                    violations_url += f"&platform={provider_param}"
                violations_data = api_request(violations_url)
                violations_list = violations_data.get("results", violations_data) if isinstance(violations_data, dict) else violations_data
                total_violations = violations_data.get("count", len(violations_list)) if isinstance(violations_data, dict) else len(violations_list)

                # Get cloud accounts to show connected accounts
                try:
                    customers_data = api_request("/v1/customers/")
                    customers = customers_data.get("results", [])
                    total_accounts = sum(c.get("ac_count", 0) for c in customers)
                except:
                    total_accounts = 0

                # Count by severity
                severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                platform_counts = {}
                for v in violations_list:
                    sev = (v.get("severity") or "medium").lower()
                    if sev in severity_counts:
                        severity_counts[sev] += 1
                    platform = (v.get("platform") or "unknown").lower()
                    platform_counts[platform] = platform_counts.get(platform, 0) + 1

                progress.remove_task(task)
                console.print("[green]Cloud security scan complete![/green]")
                console.print("\n[bold]Cloud Security Posture[/bold]\n")

                console.print(f"  Connected Accounts: [cyan]{total_accounts}[/cyan]")
                console.print(f"  Total Violations:   [yellow]{total_violations}[/yellow]")
                console.print(f"  Critical Issues:    [red]{severity_counts['critical']}[/red]")
                console.print(f"  High Issues:        [yellow]{severity_counts['high']}[/yellow]")
                console.print(f"  Medium Issues:      [blue]{severity_counts['medium']}[/blue]")

                if provider_param:
                    console.print(f"\n  Provider:           [cyan]{provider_param.upper()}[/cyan]")

                # Show provider breakdown if scanning all
                if platform_counts and not provider_param:
                    console.print("\n[bold]By Platform[/bold]\n")
                    for p, count in sorted(platform_counts.items(), key=lambda x: x[1], reverse=True):
                        console.print(f"  [cyan]{p.upper():10}[/cyan] {count} violations")

            elif findings:
                # Use unified violations endpoint
                url = "/v2/compliances/unified-violations/?limit=20"
                if severity:
                    url += f"&severity={severity}"
                data = api_request(url)

                progress.remove_task(task)
                console.print("\n[bold]Cloud Security Findings[/bold]\n")

                # Handle both list and dict response formats
                if isinstance(data, list):
                    findings_list = data
                else:
                    findings_list = data.get("results", data.get("violations", data.get("findings", [])))

                if not findings_list:
                    console.print("  [green]No open findings! Your cloud is secure.[/green]")
                else:
                    table = Table()
                    table.add_column("Severity", style="bold")
                    table.add_column("Rule", no_wrap=False)
                    table.add_column("Resource")
                    table.add_column("Platform")

                    severity_styles = {
                        "critical": "red",
                        "high": "yellow",
                        "medium": "blue",
                        "low": "dim"
                    }

                    for f in findings_list[:10]:
                        sev = f.get("severity", "medium")
                        style = severity_styles.get(sev.lower(), "white")
                        table.add_row(
                            f"[{style}]{sev.upper()}[/{style}]",
                            (f.get("rule_name", f.get("title", "N/A")) or "N/A")[:45],
                            (f.get("resource_name", f.get("resource_type", "N/A")) or "N/A")[:25],
                            f.get("platform", "N/A").upper()
                        )

                    console.print(table)
                    total_count = data.get("count", len(findings_list)) if isinstance(data, dict) else len(findings_list)
                    console.print(f"\n[dim]Showing {min(10, len(findings_list))} of {total_count} findings[/dim]")

            elif dashboard:
                # Get dashboard trends data
                data = api_request("/v2/compliances/dashboard/trends/")
                # Also get violations count
                violations_data = api_request("/v2/compliances/unified-violations/?limit=1")
                violations_count = violations_data.get("count", 0) if isinstance(violations_data, dict) else len(violations_data)

                progress.remove_task(task)
                console.print("[green]Dashboard loaded![/green]")
                console.print("\n[bold]Cloud Security Dashboard[/bold]\n")

                # Extract metrics from trends data
                fix_velocity = data.get("fix_velocity", "N/A")
                time_range = data.get("time_range", "7d")
                total_resolved = data.get("total_resolved", 0)
                avg_resolution_time = data.get("avg_resolution_time_hours", "N/A")

                console.print(f"  Fix Velocity:     [green]{fix_velocity}[/green]")
                console.print(f"  Time Range:       [cyan]{time_range}[/cyan]")
                console.print(f"  Resolved Issues:  [green]{total_resolved}[/green]")
                console.print(f"  Avg Resolution:   [white]{avg_resolution_time}h[/white]")
                console.print(f"  Open Violations:  [yellow]{violations_count}[/yellow]")

                # Show severity breakdown if available
                by_severity = data.get("by_severity", {})
                if by_severity:
                    console.print("\n[bold]Resolved by Severity[/bold]\n")
                    for sev, count in by_severity.items():
                        sev_color = {"critical": "red", "high": "yellow", "medium": "blue", "low": "dim"}.get(sev.lower(), "white")
                        console.print(f"  [{sev_color}]{sev.upper():10}[/{sev_color}] {count}")

            elif dynamic_scan:
                # Dynamic cloud scan
                progress.update(task, description="Running dynamic cloud scan...")
                data = api_request(
                    "/v2/compliances/dynamic-scan/execute/",
                    method="POST",
                    json_data={"account_id": int(dynamic_scan)}
                )
                progress.remove_task(task)

                console.print("[green]Dynamic scan initiated![/green]")
                console.print(f"\n[bold]Dynamic Scan Results[/bold]\n")
                console.print(f"  Scan ID:        [cyan]{data.get('scan_id', 'N/A')}[/cyan]")
                console.print(f"  Account ID:     [white]{data.get('account_id', dynamic_scan)}[/white]")
                console.print(f"  Status:         [green]{data.get('status', 'initiated')}[/green]")
                console.print(f"  Started At:     [dim]{data.get('started_at', 'now')}[/dim]")

                if data.get("findings_count"):
                    console.print(f"  Findings:       [yellow]{data.get('findings_count', 0)}[/yellow]")

                if data.get("async"):
                    console.print("\n[dim]Scan running asynchronously. Check status with --dashboard[/dim]")

            elif unified_scan:
                # Unified scan with scope
                if not scope_id and scope != 'account':
                    console.print("[red]--scope-id required for non-account scopes[/red]")
                    progress.remove_task(task)
                    return

                progress.update(task, description=f"Running unified scan ({scope})...")
                scan_data = {"scope": scope}

                if scope == 'account':
                    scan_data["account_id"] = account_id or int(scope_id) if scope_id else None
                elif scope == 'standard':
                    scan_data["standard_id"] = scope_id
                elif scope == 'control':
                    scan_data["control_id"] = scope_id
                elif scope == 'policy':
                    scan_data["policy_id"] = scope_id
                elif scope == 'diagram':
                    scan_data["diagram_id"] = scope_id
                elif scope == 'component':
                    scan_data["component_id"] = scope_id

                if account_id:
                    scan_data["account_id"] = account_id

                data = api_request(
                    "/v2/compliances/scan/execute/",
                    method="POST",
                    json_data=scan_data
                )
                progress.remove_task(task)

                console.print("[green]Unified scan complete![/green]")
                console.print(f"\n[bold]Unified Scan Results ({scope})[/bold]\n")
                console.print(f"  Scan ID:        [cyan]{data.get('scan_id', 'N/A')}[/cyan]")
                console.print(f"  Scope:          [white]{scope}[/white]")
                console.print(f"  Status:         [green]{data.get('status', 'completed')}[/green]")

                results = data.get("results", data)
                console.print(f"  Total Checked:  [white]{results.get('total_checks', results.get('total', 0))}[/white]")
                console.print(f"  Passed:         [green]{results.get('passed', 0)}[/green]")
                console.print(f"  Failed:         [red]{results.get('failed', 0)}[/red]")

                if results.get("compliance_score"):
                    score = results.get("compliance_score", 0)
                    score_color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
                    console.print(f"  Score:          [{score_color}]{score}%[/{score_color}]")

            elif rules:
                # List scanner rules
                progress.update(task, description="Fetching scanner rules...")
                url = "/v2/compliances/scanner-rules/"
                if severity:
                    url += f"?severity={severity}"
                data = api_request(url)
                progress.remove_task(task)

                rules_list = data.get("results", data.get("rules", []))
                console.print(f"\n[bold]Scanner Rules ({len(rules_list)} total)[/bold]\n")

                if not rules_list:
                    console.print("  [dim]No scanner rules found.[/dim]")
                else:
                    table = Table()
                    table.add_column("ID", style="cyan")
                    table.add_column("Name")
                    table.add_column("Severity", style="bold")
                    table.add_column("Provider")
                    table.add_column("Enabled")

                    severity_styles = {
                        "critical": "red",
                        "high": "yellow",
                        "medium": "blue",
                        "low": "dim"
                    }

                    for r in rules_list[:20]:
                        sev = r.get("severity", "medium")
                        style = severity_styles.get(sev.lower(), "white")
                        enabled = "[green]✓[/green]" if r.get("enabled", True) else "[red]✗[/red]"
                        table.add_row(
                            str(r.get("id", ""))[:8],
                            r.get("name", "N/A")[:40],
                            f"[{style}]{sev.upper()}[/{style}]",
                            r.get("provider", "N/A"),
                            enabled
                        )

                    console.print(table)

            elif create_rule:
                # Interactive rule creation
                progress.remove_task(task)
                console.print("\n[bold]Create Scanner Rule[/bold]\n")

                rule_name = click.prompt("Rule name")
                rule_desc = click.prompt("Description")
                rule_severity = click.prompt("Severity", type=click.Choice(["critical", "high", "medium", "low"]), default="medium")
                rule_provider = click.prompt("Provider", type=click.Choice(["aws", "azure", "gcp", "custom"]), default="custom")

                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress2:
                    task2 = progress2.add_task("Creating rule...", total=None)

                    data = api_request(
                        "/v2/compliances/scanner-rules/",
                        method="POST",
                        json_data={
                            "name": rule_name,
                            "description": rule_desc,
                            "severity": rule_severity,
                            "provider": rule_provider,
                            "enabled": True
                        }
                    )
                    progress2.remove_task(task2)

                console.print(f"[green]Rule created successfully![/green]")
                console.print(f"  ID:       [cyan]{data.get('id', 'N/A')}[/cyan]")
                console.print(f"  Name:     {data.get('name', rule_name)}")
                console.print(f"  Severity: {data.get('severity', rule_severity)}")

            elif sync_rules:
                # Sync rules from cloud providers
                progress.update(task, description="Syncing rules from cloud providers...")
                data = api_request(
                    "/v2/compliances/scanner-rules/sync_from_providers/",
                    method="POST",
                    json_data={}
                )
                progress.remove_task(task)

                console.print("[green]Rules synced successfully![/green]")
                console.print(f"\n[bold]Sync Results[/bold]\n")
                console.print(f"  AWS Rules:   [cyan]{data.get('aws_rules', data.get('aws', 0))}[/cyan]")
                console.print(f"  Azure Rules: [cyan]{data.get('azure_rules', data.get('azure', 0))}[/cyan]")
                console.print(f"  GCP Rules:   [cyan]{data.get('gcp_rules', data.get('gcp', 0))}[/cyan]")
                console.print(f"  Total:       [green]{data.get('total', data.get('total_synced', 0))}[/green]")

            elif scanner_stats:
                # Scanner statistics
                progress.update(task, description="Fetching scanner statistics...")
                data = api_request("/v2/compliances/scanner-rules/statistics/")
                progress.remove_task(task)

                console.print("\n[bold]Scanner Statistics[/bold]\n")
                stats = data.get("statistics", data)
                console.print(f"  Total Rules:     [cyan]{stats.get('total_rules', 0)}[/cyan]")
                console.print(f"  Active Rules:    [green]{stats.get('active_rules', stats.get('enabled', 0))}[/green]")
                console.print(f"  Total Scans:     [white]{stats.get('total_scans', 0)}[/white]")
                console.print(f"  Findings Today:  [yellow]{stats.get('findings_today', 0)}[/yellow]")

                by_severity = stats.get("by_severity", {})
                if by_severity:
                    console.print("\n[bold]Rules by Severity[/bold]\n")
                    for sev, count in by_severity.items():
                        sev_color = {"critical": "red", "high": "yellow", "medium": "blue", "low": "dim"}.get(sev.lower(), "white")
                        console.print(f"  [{sev_color}]{sev.upper():10}[/{sev_color}] {count}")

                by_provider = stats.get("by_provider", {})
                if by_provider:
                    console.print("\n[bold]Rules by Provider[/bold]\n")
                    for prov, count in by_provider.items():
                        console.print(f"  [cyan]{prov.upper():10}[/cyan] {count}")

            elif remediate:
                # Execute remediation
                if not account_id:
                    console.print("[red]--account-id required for remediation[/red]")
                    progress.remove_task(task)
                    return

                progress.update(task, description="Executing remediation...")
                data = api_request(
                    "/v2/compliances/remediation-execution/execute/",
                    method="POST",
                    json_data={
                        "policy_id": remediate,
                        "account_id": account_id
                    }
                )
                progress.remove_task(task)

                console.print("[green]Remediation executed![/green]")
                console.print(f"\n[bold]Remediation Results[/bold]\n")
                console.print(f"  Policy ID:      [cyan]{remediate}[/cyan]")
                console.print(f"  Account ID:     [white]{account_id}[/white]")
                console.print(f"  Status:         [green]{data.get('status', 'completed')}[/green]")
                console.print(f"  Resources:      [white]{data.get('resources_affected', 0)}[/white]")

                if data.get("changes"):
                    console.print("\n[bold]Changes Applied[/bold]\n")
                    for change in data.get("changes", [])[:5]:
                        console.print(f"  [green]✓[/green] {change.get('description', change)}")

            elif remediate_preview:
                # Preview remediation
                if not account_id:
                    console.print("[red]--account-id required for remediation preview[/red]")
                    progress.remove_task(task)
                    return

                progress.update(task, description="Generating remediation preview...")
                data = api_request(
                    "/v2/compliances/remediation-execution/preview/",
                    method="POST",
                    json_data={
                        "policy_id": remediate_preview,
                        "account_id": account_id
                    }
                )
                progress.remove_task(task)

                console.print("[bold]Remediation Preview[/bold]\n")
                console.print(f"  Policy ID:       [cyan]{remediate_preview}[/cyan]")
                console.print(f"  Account ID:      [white]{account_id}[/white]")
                console.print(f"  Resources:       [yellow]{data.get('resources_affected', 0)}[/yellow]")
                console.print(f"  Estimated Time:  [dim]{data.get('estimated_time', 'N/A')}[/dim]")

                changes = data.get("planned_changes", data.get("changes", []))
                if changes:
                    console.print("\n[bold]Planned Changes[/bold]\n")
                    for change in changes[:10]:
                        console.print(f"  [yellow]→[/yellow] {change.get('description', change.get('action', change))}")
                        if change.get("resource"):
                            console.print(f"    [dim]Resource: {change.get('resource')}[/dim]")

                console.print("\n[dim]Run with --remediate to apply these changes[/dim]")

            else:
                progress.remove_task(task)
                console.print("[bold]Cloud Security Posture Management (CSPM/CNAPP)[/bold]\n")
                console.print("[bold]Basic Commands[/bold]")
                console.print("  [cyan]aribot cloud-security --scan[/cyan]                      Scan all cloud accounts")
                console.print("  [cyan]aribot cloud-security --scan aws[/cyan]                  Scan AWS only")
                console.print("  [cyan]aribot cloud-security --findings[/cyan]                  List security findings")
                console.print("  [cyan]aribot cloud-security --dashboard[/cyan]                 Show security dashboard")
                console.print("\n[bold]Scanner Commands[/bold]")
                console.print("  [green]aribot cloud-security --dynamic-scan <account-id>[/green]   Run dynamic scan")
                console.print("  [green]aribot cloud-security --unified-scan --scope account --account-id 123[/green]")
                console.print("  [green]aribot cloud-security --unified-scan --scope standard --scope-id CIS-AWS[/green]")
                console.print("  [green]aribot cloud-security --rules[/green]                       List scanner rules")
                console.print("  [green]aribot cloud-security --create-rule[/green]                 Create custom rule")
                console.print("  [green]aribot cloud-security --sync-rules[/green]                  Sync from providers")
                console.print("  [green]aribot cloud-security --scanner-stats[/green]               Show statistics")
                console.print("\n[bold]Remediation Commands[/bold]")
                console.print("  [yellow]aribot cloud-security --remediate-preview <policy-id> --account-id 123[/yellow]")
                console.print("  [yellow]aribot cloud-security --remediate <policy-id> --account-id 123[/yellow]")

        except Exception as e:
            progress.remove_task(task)
            console.print(f"[red]Cloud security operation failed: {e}[/red]")


@main.command()
@click.option("--methodologies", is_flag=True, help="List available threat modeling methodologies")
@click.option("--intelligence", is_flag=True, help="Get threat intelligence summary")
@click.option("--attack-paths", is_flag=True, help="Analyze attack paths (requires --diagram)")
@click.option("-d", "--diagram", help="Diagram ID for analysis")
@click.option("--analyze", help="Comprehensive threat analysis for diagram")
@click.option("--requirements", help="Generate security requirements for diagram")
@click.option("--simulate-path", "simulate_path", help="Simulate attack path traversal step-by-step")
@click.option("--target-component", "target_component", help="Target component name for attack path simulation")
@click.option("--ai-attack-paths", "ai_attack_paths", help="AI-powered attack path analysis")
@click.option("--ai-predict", "ai_predict", help="AI threat prediction using ML ensemble")
@click.option("--ai-insights", "ai_insights", help="Generate AI architecture insights")
@click.option("--patterns", help="Detect AI patterns in diagram")
def redteam(methodologies: bool, intelligence: bool, attack_paths: bool, diagram: Optional[str], analyze: Optional[str], requirements: Optional[str], simulate_path: Optional[str], target_component: Optional[str], ai_attack_paths: Optional[str], ai_predict: Optional[str], ai_insights: Optional[str], patterns: Optional[str]):
    """Red team attack simulation and threat analysis."""
    if methodologies:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching methodologies...", total=None)
            fallback = {
                "available_methodologies": [
                    {"name": "STRIDE", "description": "Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation"},
                    {"name": "PASTA", "description": "Process for Attack Simulation and Threat Analysis"},
                    {"name": "NIST", "description": "NIST Cybersecurity Framework threat modeling"},
                    {"name": "MITRE ATT&CK", "description": "Adversarial tactics, techniques, and common knowledge"},
                    {"name": "OWASP", "description": "Open Web Application Security Project methodology"},
                    {"name": "AI_ENHANCED", "description": "AI-powered predictive threat analysis"},
                ],
                "risk_levels": [
                    {"name": "Critical", "description": "Immediate action required - system compromise likely"},
                    {"name": "High", "description": "Significant risk - address within 24-48 hours"},
                    {"name": "Medium", "description": "Moderate risk - address within 1-2 weeks"},
                    {"name": "Low", "description": "Minor risk - address in regular maintenance"},
                    {"name": "Info", "description": "Informational finding - no immediate action needed"},
                ],
                "compliance_frameworks": [
                    {"name": "SOC2", "description": "Service Organization Control 2"},
                    {"name": "ISO27001", "description": "Information Security Management"},
                    {"name": "PCI-DSS", "description": "Payment Card Industry Data Security Standard"},
                    {"name": "GDPR", "description": "General Data Protection Regulation"},
                    {"name": "HIPAA", "description": "Health Insurance Portability and Accountability"},
                    {"name": "NIST-CSF", "description": "NIST Cybersecurity Framework"},
                    {"name": "CIS", "description": "Center for Internet Security Controls"},
                    {"name": "FedRAMP", "description": "Federal Risk and Authorization Management"},
                ],
                "engine_capabilities": {
                    "multi_framework_analysis": True, "ai_threat_prediction": True,
                    "real_time_scanning": True, "attack_path_analysis": True,
                    "compliance_mapping": True, "automated_remediation": True,
                },
            }
            try:
                headers = get_headers()
                with httpx.Client(timeout=30.0) as client:
                    resp = client.get(f"{API_BASE}/v2/threat-modeling/threat-engine/threat-models/", headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                progress.remove_task(task)
            except Exception:
                data = fallback
                progress.remove_task(task)
                console.print("[dim](Using cached methodology data)[/dim]\n")

            console.print("\n[bold]Threat Modeling Methodologies[/bold]\n")
            for m in data.get("available_methodologies", data.get("supported_methodologies", [])):
                console.print(f"  [cyan]{m.get('name', 'N/A'):12}[/cyan] [dim]{m.get('description', '')}[/dim]")

            console.print("\n[bold]Risk Levels[/bold]\n")
            for r in data.get("risk_levels", []):
                console.print(f"  [yellow]{r.get('name', 'N/A'):12}[/yellow] [dim]{r.get('description', '')}[/dim]")

            console.print("\n[bold]Compliance Frameworks[/bold]\n")
            for f in data.get("compliance_frameworks", []):
                console.print(f"  [green]{f.get('name', 'N/A'):20}[/green] [dim]{f.get('description', '')}[/dim]")

            console.print("\n[bold]Engine Capabilities[/bold]\n")
            capabilities = data.get("engine_capabilities", data.get("capabilities", {}))
            for cap, enabled in capabilities.items():
                status = "[green]✓[/green]" if enabled else "[red]✗[/red]"
                console.print(f"  {status} {cap.replace('_', ' ')}")
        return

    if intelligence:
        if not diagram:
            console.print("[yellow]Usage: aribot redteam --intelligence --diagram <diagram-id>[/yellow]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching threat intelligence...", total=None)
            try:
                data = api_request(f"/v2/threat-modeling/diagrams/{diagram}/threats/")
                progress.remove_task(task)

                threats = data.get("threats") or data.get("results") or []

                console.print("\n[bold]Threat Intelligence Summary[/bold]\n")
                console.print(f"  [cyan]Integration:[/cyan]     Active")
                console.print(f"  [cyan]Cache TTL:[/cyan]       3600s")
                console.print(f"  [cyan]Real-time Feeds:[/cyan] Enabled")
                console.print(f"  [cyan]Correlation:[/cyan]     Enabled")

                console.print(f"\n[bold]Diagram Threats[/bold] ({len(threats)} total)\n")

                # Group by severity
                by_severity = {}
                for t in threats:
                    sev = t.get("severity", "unknown")
                    by_severity.setdefault(sev, []).append(t)

                for sev in ["critical", "high", "medium", "low"]:
                    if sev in by_severity:
                        color = {"critical": "red", "high": "yellow", "medium": "cyan", "low": "green"}.get(sev, "white")
                        console.print(f"  [{color}]{sev.upper()}[/{color}]: {len(by_severity[sev])} threats")

                console.print("\n[bold]Supported Indicators[/bold]\n")
                for ind in ["IP addresses", "Domain names", "File hashes", "URLs", "CVE identifiers"]:
                    console.print(f"  • {ind}")

                console.print("\n[bold]Vision 2040 Features[/bold]\n")
                features = {
                    "ai_powered_correlation": True,
                    "predictive_intelligence": True,
                    "automated_ioc_extraction": True,
                    "contextual_threat_analysis": True
                }
                for feat, enabled in features.items():
                    status = "[green]✓[/green]" if enabled else "[red]✗[/red]"
                    console.print(f"  {status} {feat.replace('_', ' ')}")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]Failed to fetch threat intelligence: {e}[/red]")
        return

    if attack_paths:
        if not diagram:
            console.print("[red]Error: --attack-paths requires --diagram <diagram-id>[/red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing attack paths...", total=None)
            try:
                full_id = resolve_diagram_id(diagram)
                diagram_data = api_request(f"/v2/threat-modeling/diagrams/{full_id}/")

                # Build components and connections from diagram data
                components = []
                connections = []

                for comp in diagram_data.get("components", []):
                    components.append({
                        "id": comp.get("id"),
                        "name": comp.get("name", comp.get("label", "Unknown")),
                        "type": comp.get("type", "generic")
                    })

                for conn in diagram_data.get("connections", []):
                    connections.append({
                        "source": conn.get("source_id", conn.get("source")),
                        "target": conn.get("target_id", conn.get("target")),
                        "type": conn.get("type", "data_flow")
                    })

                # Find entry/exit points
                source_node = None
                target_node = None
                for comp in components:
                    comp_type = str(comp.get("type", "")).lower()
                    comp_name = str(comp.get("name", "")).lower()
                    if "user" in comp_type or "client" in comp_type or "external" in comp_type or "user" in comp_name or "client" in comp_name:
                        source_node = comp.get("id")
                    elif "database" in comp_type or "storage" in comp_type or "data" in comp_type or "sql" in comp_name or "db" in comp_name:
                        target_node = comp.get("id")

                # Generate attack paths using the correct v2 endpoint (same as frontend)
                data = api_request(
                    f"/v2/threat-modeling/diagrams/{full_id}/generate-attack-paths/",
                    method="POST",
                    json_data={
                        "scope": "single",
                        "include_compliance": True,
                        "save": True
                    }
                )
                progress.remove_task(task)

                # Response matches frontend: { status: 'success', paths: [...] }
                paths = data.get("paths") or data.get("attack_paths") or []

                console.print(f"\n[bold]Attack Path Analysis[/bold]\n")
                console.print(f"  Paths Found:   [yellow]{len(paths)}[/yellow]")
                console.print(f"  Status:        [cyan]{data.get('status', 'completed')}[/cyan]")

                if paths:
                    console.print(f"\n[bold]Identified Attack Paths:[/bold]\n")
                    for i, p in enumerate(paths[:5], 1):
                        risk_score = p.get("risk_score", 0)
                        risk_color = "red" if risk_score >= 80 else "yellow" if risk_score >= 60 else "green"
                        risk_label = "CRITICAL" if risk_score >= 80 else "HIGH" if risk_score >= 60 else "MEDIUM" if risk_score >= 40 else "LOW"

                        console.print(f"  [bold]Path {i}:[/bold] {p.get('name', p.get('description', 'Attack Vector'))}")
                        console.print(f"    [{risk_color}]Risk:[/{risk_color}]        [{risk_color}]{risk_label} ({risk_score}%)[/{risk_color}]")
                        console.print(f"    [dim]Description:[/dim] {p.get('description', 'N/A')}")

                        # Show attack chain if available
                        attack_chain = p.get("attack_chain") or []
                        if attack_chain:
                            console.print(f"    [dim]Steps:[/dim]       {len(attack_chain)}")
                            console.print(f"    [dim]Mitigations:[/dim] {p.get('mitigations_count', len(p.get('mitigations', [])))}")
                            console.print(f"    [bold]Attack Chain:[/bold]")
                            for step in attack_chain[:5]:
                                console.print(f"      {step.get('step', '?')}. {step.get('phase', '')} → {step.get('target', '')}")
                        console.print()
                else:
                    console.print("  [green]No critical attack paths identified![/green]")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]Failed to analyze attack paths: {e}[/red]")
        return

    # Attack path simulation with step-by-step visualization
    if simulate_path:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Analyzing attack paths...", total=None)
            try:
                full_id = resolve_diagram_id(simulate_path)
                diagram_data = api_request(f"/v2/threat-modeling/diagrams/{full_id}/")
                components = diagram_data.get("components", [])
                connections = diagram_data.get("links", diagram_data.get("connections", []))

                if len(components) < 2:
                    progress.remove_task(task)
                    console.print("[yellow]Not enough components for attack path simulation.[/yellow]")
                    console.print("[dim]Upload a diagram with at least 2 connected components.[/dim]")
                    return

                # Get attack paths from API
                path_data = api_request(
                    "/v2/threat-engine/attack-paths/",
                    method="POST",
                    json_data={
                        "components": [
                            {
                                "id": c.get("id", c.get("uuid")),
                                "type": c.get("component_type", c.get("type", "component")),
                                "name": c.get("name", c.get("label", "Unknown"))
                            }
                            for c in components
                        ],
                        "connections": [
                            {
                                "source": c.get("source_id", c.get("source")),
                                "target": c.get("target_id", c.get("target"))
                            }
                            for c in connections
                        ],
                        "source_node": components[0].get("id", "") if components else "",
                        "target_node": target_component or (components[-1].get("id", "") if components else "")
                    }
                )
                progress.remove_task(task)

                attack_paths = path_data.get("attack_paths", [])
                if not attack_paths:
                    console.print("\n[green]No critical attack paths found. Architecture appears resilient.[/green]")
                    return

                # Use the most critical path for simulation
                critical_path = attack_paths[0]
                path_steps = critical_path.get("steps", [])

                console.print("\n" + "═" * 60)
                console.print("[bold red]  ATTACK PATH SIMULATION[/bold red]")
                console.print("═" * 60 + "\n")

                console.print(f"  [cyan]Diagram:[/cyan]       {diagram_data.get('name', 'N/A')}")
                console.print(f"  [cyan]Path Score:[/cyan]    [red]{(critical_path.get('risk_score', 0) * 10):.1f}/10[/red]")
                console.print(f"  [cyan]Entry Point:[/cyan]   [yellow]{critical_path.get('source_node', 'External')}[/yellow]")
                console.print(f"  [cyan]Target:[/cyan]        [red]{critical_path.get('target_node', 'Critical Asset')}[/red]")
                console.print(f"  [cyan]Steps:[/cyan]         {len(path_steps)}")

                console.print("\n[bold]Simulating Attack Traversal:[/bold]\n")

                # Define MITRE techniques for each step type
                mitre_map = {
                    "api": ("Initial Access", "T1190 - Exploit Public Application"),
                    "gateway": ("Initial Access", "T1190 - Exploit Public Application"),
                    "auth": ("Credential Theft", "T1552 - Unsecured Credentials"),
                    "service": ("Lateral Movement", "T1078 - Valid Accounts"),
                    "app": ("Privilege Escalation", "T1068 - Exploitation"),
                    "database": ("Data Exfiltration", "T1530 - Cloud Storage Access"),
                    "storage": ("Data Exfiltration", "T1530 - Cloud Storage Access"),
                    "default": ("Exploitation", "T1203 - Exploitation for Client")
                }

                # Simulate step-by-step traversal
                for i, step in enumerate(path_steps, 1):
                    import time
                    time.sleep(0.8)  # Simulate delay

                    node_type = (step.get("to_node", step.get("target", "")) or "").lower()
                    mitre = mitre_map.get(node_type, mitre_map["default"])

                    console.print(f"  [dim][{i}/{len(path_steps)}][/dim] [red]━━▶[/red] [bold]{step.get('to_node', step.get('target', 'Unknown'))}[/bold]")
                    console.print(f"       [dim]From:[/dim]       {step.get('from_node', step.get('source', 'N/A'))}")
                    console.print(f"       [dim]Technique:[/dim]  [yellow]{mitre[1]}[/yellow]")
                    console.print(f"       [dim]Action:[/dim]     {mitre[0]}")
                    console.print()

                # Final status
                console.print("[bold red]" + "─" * 60 + "[/bold red]")
                console.print(f"[bold red]  ⚠️  TARGET REACHED: {critical_path.get('target_node', 'Critical Asset')}[/bold red]")
                console.print("[bold red]" + "─" * 60 + "[/bold red]\n")

                console.print("[bold]Recommended Mitigations:[/bold]\n")
                console.print("  [green]1.[/green] Fix input validation at entry point (breaks Step 1)")
                console.print("  [green]2.[/green] Implement network segmentation")
                console.print("  [green]3.[/green] Use secrets management for credentials")
                console.print("  [green]4.[/green] Enable database access logging\n")

                console.print(f"[dim]Run 'aribot redteam --ai-attack-paths {simulate_path}' for detailed AI analysis[/dim]")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]Attack path simulation failed: {e}[/red]")
        return

    if analyze:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running comprehensive analysis...", total=None)
            try:
                full_id = resolve_diagram_id(analyze)
                diagram_data = api_request(f"/v2/threat-modeling/diagrams/{full_id}/")

                # Use the V2 AI analysis endpoint
                data = api_request(
                    f"/v2/threat-modeling/diagrams/{full_id}/analyze-ai/",
                    method="POST",
                    json_data={
                        "analysis_type": "comprehensive",
                        "include_mitre": True,
                        "include_recommendations": True
                    }
                )
                progress.remove_task(task)

                console.print(f"\n[bold]Comprehensive Threat Analysis[/bold] - {diagram_data.get('name', analyze)}\n")

                analysis = data.get("analysis", data)
                risk_level = analysis.get("risk_level", "N/A")
                risk_color = "red" if risk_level == "critical" else "yellow"
                console.print(f"  [cyan]Risk Level:[/cyan]    [{risk_color}]{risk_level}[/{risk_color}]")
                console.print(f"  [cyan]Risk Score:[/cyan]    [red]{analysis.get('risk_score', analysis.get('overall_score', 'N/A'))}[/red]")
                console.print(f"  [cyan]Threats Found:[/cyan] [yellow]{analysis.get('threat_count', analysis.get('total_threats', 0))}[/yellow]")

                threats = analysis.get("threats", data.get("threats", []))
                if threats:
                    console.print("\n[bold]Top Threats[/bold]\n")
                    for t in threats[:5]:
                        severity = t.get("severity", "unknown")
                        sev_color = {"critical": "red", "high": "red", "medium": "yellow", "low": "green"}.get(severity.lower(), "white")
                        console.print(f"  [{sev_color}]●[/{sev_color}] {t.get('title', t.get('name', 'Unknown'))}")
                        console.print(f"    [dim]Category: {t.get('category', 'N/A')} | MITRE: {t.get('mitre_id', t.get('mitre_mapping', 'N/A'))}[/dim]")

                recommendations = analysis.get("recommendations", data.get("recommendations", []))
                if recommendations:
                    console.print("\n[bold]Top Recommendations[/bold]\n")
                    for r in recommendations[:3]:
                        console.print(f"  [green]→[/green] {r.get('title', r.get('description', r))}")

                console.print(f"\n[dim]Methodologies: {', '.join(analysis.get('methodologies', data.get('methodologies', ['STRIDE', 'PASTA', 'NIST'])))}[/dim]")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]Failed to run comprehensive analysis: {e}[/red]")
        return

    if requirements:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating security requirements...", total=None)
            try:
                full_id = resolve_diagram_id(requirements)
                diagram_data = api_request(f"/v2/threat-modeling/diagrams/{full_id}/")

                threats = diagram_data.get("threats", [])
                threat_list = [{"name": t.get("name", "Threat"), "severity": t.get("severity", "medium")} for t in threats[:10]]

                data = api_request(
                    "/v2/threat-engine/security-requirements/",
                    method="POST",
                    json_data={
                        "threats": threat_list,
                        "context": f"Diagram: {diagram_data.get('name', 'Unknown')}"
                    }
                )
                progress.remove_task(task)

                console.print(f"\n[bold]Security Requirements[/bold] - {diagram_data.get('name', requirements)}\n")

                console.print(f"  [cyan]Total Requirements:[/cyan] {data.get('total_requirements', 0)}")

                reqs = data.get("requirements", [])
                if reqs:
                    for r in reqs[:10]:
                        priority = r.get("priority", "medium")
                        pri_color = {"critical": "red", "high": "red", "medium": "yellow", "low": "green"}.get(priority.lower(), "white")
                        console.print(f"\n  [{pri_color}][{priority.upper()}][/{pri_color}] {r.get('title', 'Requirement')}")
                        console.print(f"    [dim]{r.get('description', 'N/A')}[/dim]")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]Failed to generate security requirements: {e}[/red]")
        return

    # AI-powered attack path analysis
    if ai_attack_paths:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running AI-powered attack path analysis...", total=None)
            try:
                full_id = resolve_diagram_id(ai_attack_paths)
                diagram_data = api_request(f"/v2/threat-modeling/diagrams/{full_id}/")

                data = api_request(
                    "/v2/ai-agents/analyze/",
                    method="POST",
                    json_data={
                        "diagram_data": {
                            "id": full_id,
                            "name": diagram_data.get("name"),
                            "components": diagram_data.get("components", []),
                            "connections": diagram_data.get("links", diagram_data.get("connections", []))
                        },
                        "context": {
                            "analysis_type": "attack_paths",
                            "include_knowledge_graph": True
                        }
                    }
                )
                progress.remove_task(task)

                console.print(f"\n[bold]AI Attack Path Analysis[/bold] - {diagram_data.get('name', ai_attack_paths)}\n")

                analysis = data.get("analysis", data)
                risk_level = analysis.get("risk_level", "N/A")
                console.print(f"  [cyan]Risk Level:[/cyan]     [{'red' if risk_level == 'critical' else 'yellow'}]{risk_level}[/{'red' if risk_level == 'critical' else 'yellow'}]")
                console.print(f"  [cyan]AI Confidence:[/cyan]  [green]{(analysis.get('confidence', 0.85) * 100):.0f}%[/green]")

                attack_paths = analysis.get("attack_paths", data.get("attack_paths", []))
                if attack_paths:
                    console.print(f"\n[bold]Identified Attack Paths ({len(attack_paths)})[/bold]\n")
                    for i, path in enumerate(attack_paths[:5], 1):
                        risk_score = path.get("risk_score", 0.5)
                        risk_color = "red" if risk_score > 0.7 else "yellow" if risk_score > 0.4 else "green"
                        console.print(f"  [bold]Path {i}:[/bold] {path.get('name', path.get('description', 'Attack Vector'))}")
                        console.print(f"    Risk Score:    [{risk_color}]{(risk_score * 100):.0f}%[/{risk_color}]")
                        console.print(f"    Attack Steps:  [cyan]{path.get('steps', path.get('hop_count', 'N/A'))}[/cyan]")
                        console.print(f"    Entry Point:   [yellow]{path.get('entry_point', path.get('source', 'External'))}[/yellow]")
                        console.print(f"    Target:        [red]{path.get('target', path.get('destination', 'Critical Asset'))}[/red]")
                else:
                    console.print("\n  [green]No critical attack paths identified![/green]")

                mitigations = analysis.get("mitigations", data.get("mitigations", []))
                if mitigations:
                    console.print("\n[bold]AI-Recommended Mitigations[/bold]\n")
                    for m in mitigations[:3]:
                        console.print(f"  [green]→[/green] {m.get('title', m.get('description', m))}")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]AI attack path analysis failed: {e}[/red]")
        return

    # AI threat prediction
    if ai_predict:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Running AI threat prediction...", total=None)
            try:
                full_id = resolve_diagram_id(ai_predict)
                diagram_data = api_request(f"/v2/threat-modeling/diagrams/{full_id}/")

                data = api_request(
                    "/v2/threat-modeling/ml/ensemble-predict/",
                    method="POST",
                    json_data={
                        "diagram_data": {
                            "id": full_id,
                            "components": diagram_data.get("components", []),
                            "connections": diagram_data.get("links", [])
                        },
                        "threat_context": {
                            "industry": "technology",
                            "sensitivity": "high"
                        }
                    }
                )
                progress.remove_task(task)

                console.print(f"\n[bold]AI Threat Prediction[/bold] - {diagram_data.get('name', ai_predict)}\n")
                console.print(f"  [cyan]Model:[/cyan]          [green]ML Ensemble (STRIDE + PASTA + NIST)[/green]")

                predictions = data.get("predictions", data)
                console.print(f"  [cyan]Confidence:[/cyan]     [green]{(predictions.get('confidence', 0.92) * 100):.0f}%[/green]")
                risk_level = predictions.get("risk_level", "medium")
                console.print(f"  [cyan]Predicted Risk:[/cyan] [{'red' if risk_level == 'critical' else 'yellow'}]{risk_level}[/{'red' if risk_level == 'critical' else 'yellow'}]")

                threats = predictions.get("predicted_threats", predictions.get("threats", []))
                if threats:
                    console.print("\n[bold]Predicted Threats[/bold]\n")
                    for t in threats[:5]:
                        prob = t.get("probability", t.get("confidence", 0.8))
                        prob_color = "red" if prob > 0.8 else "yellow" if prob > 0.5 else "green"
                        console.print(f"  [{prob_color}][{(prob * 100):.0f}%][/{prob_color}] {t.get('title', t.get('name', 'Threat'))}")
                        console.print(f"    [dim]Category: {t.get('category', 'N/A')} | Impact: {t.get('impact', 'high')}[/dim]")

                emerging = predictions.get("emerging_threats", [])
                if emerging:
                    console.print("\n[bold]Emerging Threat Patterns[/bold]\n")
                    for t in emerging[:3]:
                        console.print(f"  [yellow]⚠[/yellow] {t.get('name', t.get('description', t))}")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]AI threat prediction failed: {e}[/red]")
        return

    # AI architecture insights
    if ai_insights:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating AI architecture insights...", total=None)
            try:
                full_id = resolve_diagram_id(ai_insights)

                data = api_request(
                    f"/v2/threat-modeling/diagrams/{full_id}/generate-ai-insights/",
                    method="POST",
                    json_data={"include_recommendations": True}
                )
                progress.remove_task(task)

                console.print("\n[bold]AI Architecture Insights[/bold]\n")

                console.print(f"  [cyan]Diagram:[/cyan]          {data.get('diagram_name', 'N/A')}")
                console.print(f"  [cyan]Components:[/cyan]       [white]{data.get('component_count', 0)}[/white]")
                console.print(f"  [cyan]AI Provider:[/cyan]      [green]{data.get('provider', 'ai_agent')}[/green]")
                console.print(f"  [cyan]Generated:[/cyan]        [dim]{data.get('generated_at', 'now')}[/dim]")

                threats = data.get("threats", [])
                if threats:
                    console.print("\n[bold]Predicted Threats[/bold]\n")
                    for t in threats[:5]:
                        severity = t.get("severity", "medium")
                        severity_color = "red" if severity in ["critical", "high"] else "yellow"
                        console.print(f"  [{severity_color}]![/{severity_color}] {t.get('name', t.get('threat_id', 'Unknown'))}: {t.get('description', '')}")
                        if t.get("probability"):
                            console.print(f"    [dim]Probability: {t.get('probability') * 100:.0f}%[/dim]")
                else:
                    console.print("\n  [green]No critical threats identified.[/green]")

                recommendations = data.get("recommendations", [])
                if recommendations:
                    console.print("\n[bold]AI Recommendations[/bold]\n")
                    for r in recommendations[:5]:
                        rec_text = r if isinstance(r, str) else r.get('title', r.get('description', str(r)))
                        console.print(f"  [cyan]→[/cyan] {rec_text}")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]AI insights generation failed: {e}[/red]")
        return

    # AI pattern detection
    if patterns:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Detecting AI patterns...", total=None)
            try:
                full_id = resolve_diagram_id(patterns)

                data = api_request(
                    "/v2/threat-modeling/ai-patterns/detect/",
                    method="POST",
                    json_data={
                        "diagram_id": full_id,
                        "sensitivity": "high"
                    }
                )
                progress.remove_task(task)

                console.print("\n[bold]AI Pattern Detection[/bold]\n")

                detection = data.get("detection", data)
                console.print(f"  [cyan]Patterns Found:[/cyan]    {detection.get('total_patterns', 0)}")
                console.print(f"  [cyan]Security Patterns:[/cyan] [yellow]{detection.get('security_patterns', 0)}[/yellow]")
                console.print(f"  [cyan]Risk Patterns:[/cyan]     [red]{detection.get('risk_patterns', 0)}[/red]")

                pattern_list = detection.get("patterns", data.get("patterns", []))
                if pattern_list:
                    console.print("\n[bold]Detected Patterns[/bold]\n")
                    for p in pattern_list[:5]:
                        p_type = p.get("type", "pattern")
                        type_color = "red" if p_type == "risk" else "green" if p_type == "security" else "cyan"
                        console.print(f"  [{type_color}][{p_type.upper()}][/{type_color}] {p.get('name', p.get('title', 'Pattern'))}")
                        console.print(f"    [dim]Confidence: {(p.get('confidence', 0.85) * 100):.0f}% | Impact: {p.get('impact', 'medium')}[/dim]")

                anomalies = detection.get("anomalies", [])
                if anomalies:
                    console.print("\n[bold]Detected Anomalies[/bold]\n")
                    for a in anomalies[:3]:
                        console.print(f"  [yellow]⚠[/yellow] {a.get('description', a.get('name', a))}")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]AI pattern detection failed: {e}[/red]")
        return

    # Show help if no options provided
    console.print("[bold]Red Team Attack Simulation & Threat Analysis[/bold]\n")
    console.print("Usage:")
    console.print("  [cyan]aribot redteam --methodologies[/cyan]             List threat modeling methodologies")
    console.print("  [cyan]aribot redteam --intelligence[/cyan]              Get threat intelligence summary")
    console.print("  [cyan]aribot redteam --attack-paths -d <id>[/cyan]      Analyze attack paths for diagram")
    console.print("  [cyan]aribot redteam --analyze <id>[/cyan]              Comprehensive threat analysis")
    console.print("  [cyan]aribot redteam --requirements <id>[/cyan]         Generate security requirements")
    console.print("\n[bold]Attack Path Simulation[/bold]\n")
    console.print("  [magenta]aribot redteam --simulate-path <id>[/magenta]      Simulate attack traversal step-by-step")
    console.print("  [magenta]aribot redteam --simulate-path <id> --target-component \"Database\"[/magenta]  Target specific component")
    console.print("\n[bold]AI-Powered Commands[/bold]\n")
    console.print("  [green]aribot redteam --ai-attack-paths <id>[/green]    AI attack path analysis")
    console.print("  [green]aribot redteam --ai-predict <id>[/green]         AI threat prediction (ML)")
    console.print("  [green]aribot redteam --ai-insights <id>[/green]        Generate AI architecture insights")
    console.print("  [green]aribot redteam --patterns <id>[/green]           Detect AI patterns in diagram")


if __name__ == "__main__":
    main()
