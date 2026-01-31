#!/usr/bin/env python3
"""
Ayurak Visual Theme for Aribot CLI

Apple Glass-inspired design with orange, gold, black, and white.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich.box import ROUNDED, DOUBLE, HEAVY, SIMPLE
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.theme import Theme

# =============================================================================
# AYURAK COLOR PALETTE - Apple Glass Inspired
# =============================================================================

AYURAK_ORANGE = "#FF6B35"      # Primary brand
AYURAK_GOLD = "#D4A03C"        # Accent/highlight
AYURAK_BLACK = "#1d1d1f"       # Dark text
AYURAK_WHITE = "#fafafa"       # Light backgrounds
AYURAK_DARK_GRAY = "#3d3d3f"   # Secondary text
AYURAK_LIGHT_GRAY = "#8e8e93"  # Muted text
AYURAK_SUCCESS = "#34c759"     # Success green
AYURAK_ERROR = "#ff3b30"       # Error red
AYURAK_WARNING = "#ff9500"     # Warning amber

# Rich Theme
AYURAK_THEME = Theme({
    "info": "white",
    "warning": f"bold {AYURAK_WARNING}",
    "error": f"bold {AYURAK_ERROR}",
    "success": f"bold {AYURAK_SUCCESS}",
    "primary": f"bold {AYURAK_ORANGE}",
    "accent": f"{AYURAK_GOLD}",
    "muted": AYURAK_LIGHT_GRAY,
    "brand": f"bold {AYURAK_ORANGE}",
    "critical": f"bold white on {AYURAK_ERROR}",
    "high": f"bold {AYURAK_ERROR}",
    "medium": f"bold {AYURAK_WARNING}",
    "low": f"bold {AYURAK_GOLD}",
})

# Create themed console
console = Console(theme=AYURAK_THEME)

# =============================================================================
# ASCII ART LOGO - Clean & Minimal
# =============================================================================

ARIBOT_LOGO = f"""[bold {AYURAK_ORANGE}]
   ╭──────────────────────────────────────────────────────────────╮
   │                                                              │
   │      █████╗ ██████╗ ██╗██████╗  ██████╗ ████████╗           │
   │     ██╔══██╗██╔══██╗██║██╔══██╗██╔═══██╗╚══██╔══╝           │
   │     ███████║██████╔╝██║██████╔╝██║   ██║   ██║              │
   │     ██╔══██║██╔══██╗██║██╔══██╗██║   ██║   ██║              │
   │     ██║  ██║██║  ██║██║██████╔╝╚██████╔╝   ██║              │
   │     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═════╝  ╚═════╝    ╚═╝              │
   │                                                              │
   │              [{AYURAK_GOLD}]Security Intelligence Platform[/{AYURAK_GOLD}]                │
   │                                                              │
   ╰──────────────────────────────────────────────────────────────╯
[/bold {AYURAK_ORANGE}]"""

ARIBOT_LOGO_SMALL = f"""[bold {AYURAK_ORANGE}]
   ▄▀▄ █▀▄ █ █▀▄ █▀█ ▀█▀   [{AYURAK_GOLD}]Security Intelligence[/{AYURAK_GOLD}]
   █▀█ █▀▄ █ █▀▄ █▄█  █
[/bold {AYURAK_ORANGE}]"""

ARIBOT_LOGO_MINI = f"[bold {AYURAK_ORANGE}]◆[/bold {AYURAK_ORANGE}] [bold white]ARIBOT[/bold white]"

ARIBOT_WORDMARK = f"[bold {AYURAK_ORANGE}]◆[/bold {AYURAK_ORANGE}] [bold white]aribot[/bold white]"

# =============================================================================
# STYLED OUTPUT FUNCTIONS
# =============================================================================

def print_logo(size: str = "small"):
    """Print Aribot logo."""
    if size == "full":
        console.print(ARIBOT_LOGO)
    elif size == "small":
        console.print(ARIBOT_LOGO_SMALL)
    else:
        console.print(ARIBOT_LOGO_MINI)


def print_banner(title: str, subtitle: str = None):
    """Print a styled banner."""
    content = f"[bold white]{title}[/bold white]"
    if subtitle:
        content += f"\n[{AYURAK_LIGHT_GRAY}]{subtitle}[/{AYURAK_LIGHT_GRAY}]"

    panel = Panel(
        content,
        border_style=AYURAK_ORANGE,
        box=ROUNDED,
        padding=(1, 2),
    )
    console.print(panel)


def print_success(message: str):
    """Print success message."""
    console.print(f"[{AYURAK_SUCCESS}]✓[/{AYURAK_SUCCESS}] {message}")


def print_error(message: str):
    """Print error message."""
    console.print(f"[{AYURAK_ERROR}]✗[/{AYURAK_ERROR}] {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[{AYURAK_WARNING}]![/{AYURAK_WARNING}] {message}")


def print_info(message: str):
    """Print info message."""
    console.print(f"[{AYURAK_LIGHT_GRAY}]›[/{AYURAK_LIGHT_GRAY}] {message}")


def print_section(title: str):
    """Print a section header."""
    console.print()
    console.print(f"[bold {AYURAK_GOLD}]{title}[/bold {AYURAK_GOLD}]")
    console.print(f"[{AYURAK_ORANGE}]{'─' * len(title)}[/{AYURAK_ORANGE}]")


def print_key_value(key: str, value: str):
    """Print a key-value pair."""
    console.print(f"  [{AYURAK_LIGHT_GRAY}]{key}[/{AYURAK_LIGHT_GRAY}]  {value}")


def severity_badge(severity: str) -> str:
    """Get styled severity badge."""
    s = severity.lower()
    if s == "critical":
        return f"[bold white on {AYURAK_ERROR}] CRITICAL [/bold white on {AYURAK_ERROR}]"
    elif s == "high":
        return f"[bold {AYURAK_ERROR}]HIGH[/bold {AYURAK_ERROR}]"
    elif s == "medium":
        return f"[bold {AYURAK_WARNING}]MEDIUM[/bold {AYURAK_WARNING}]"
    elif s == "low":
        return f"[{AYURAK_GOLD}]LOW[/{AYURAK_GOLD}]"
    return f"[{AYURAK_LIGHT_GRAY}]{severity.upper()}[/{AYURAK_LIGHT_GRAY}]"


def create_table(title: str = None) -> Table:
    """Create a styled table."""
    table = Table(
        title=f"[bold white]{title}[/bold white]" if title else None,
        box=ROUNDED,
        border_style=AYURAK_ORANGE,
        header_style=f"bold {AYURAK_GOLD}",
        row_styles=["", "dim"],
        padding=(0, 1),
    )
    return table


def create_spinner(message: str) -> Progress:
    """Create a styled spinner."""
    return Progress(
        SpinnerColumn(spinner_name="dots", style=f"bold {AYURAK_ORANGE}"),
        TextColumn(f"[white]{message}[/white]"),
        console=console,
        transient=True,
    )


def create_progress() -> Progress:
    """Create a styled progress bar."""
    return Progress(
        SpinnerColumn(style=f"bold {AYURAK_ORANGE}"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(
            bar_width=40,
            style=AYURAK_DARK_GRAY,
            complete_style=AYURAK_ORANGE,
            finished_style=AYURAK_SUCCESS,
        ),
        TaskProgressColumn(),
        console=console,
    )


# =============================================================================
# WELCOME / AUTH SCREENS
# =============================================================================

def print_welcome():
    """Print welcome screen."""
    console.print()
    console.print(ARIBOT_LOGO)
    console.print()

    features = f"""[bold white]The Security Intelligence Platform[/bold white]

[{AYURAK_GOLD}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{AYURAK_GOLD}]

  [{AYURAK_ORANGE}]◆[/{AYURAK_ORANGE}] AI-Powered Threat Modeling    [{AYURAK_ORANGE}]◆[/{AYURAK_ORANGE}] 100+ Compliance Standards
  [{AYURAK_ORANGE}]◆[/{AYURAK_ORANGE}] Cloud Security (CSPM/CNAPP)   [{AYURAK_ORANGE}]◆[/{AYURAK_ORANGE}] Economic Intelligence
  [{AYURAK_ORANGE}]◆[/{AYURAK_ORANGE}] Red Team Attack Simulation    [{AYURAK_ORANGE}]◆[/{AYURAK_ORANGE}] SBOM & Vulnerability Mgmt

[{AYURAK_GOLD}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/{AYURAK_GOLD}]

  [{AYURAK_LIGHT_GRAY}]Get your API key at:[/{AYURAK_LIGHT_GRAY}] [bold white]https://developer.ayurak.com[/bold white]
"""
    console.print(features)


def print_auth_success(email: str, company: str, plan: str):
    """Print authentication success."""
    console.print()
    console.print(f"[{AYURAK_SUCCESS}]✓[/{AYURAK_SUCCESS}] [bold white]Authenticated successfully[/bold white]")
    console.print()

    console.print(f"  [{AYURAK_LIGHT_GRAY}]Email[/{AYURAK_LIGHT_GRAY}]    {email}")
    console.print(f"  [{AYURAK_LIGHT_GRAY}]Company[/{AYURAK_LIGHT_GRAY}]  {company}")
    console.print(f"  [{AYURAK_LIGHT_GRAY}]Plan[/{AYURAK_LIGHT_GRAY}]     [bold {AYURAK_GOLD}]{plan}[/bold {AYURAK_GOLD}]")
    console.print()

    print_section("Quick Start")
    console.print(f"  [{AYURAK_ORANGE}]$[/{AYURAK_ORANGE}] aribot analyze diagram.png")
    console.print(f"  [{AYURAK_ORANGE}]$[/{AYURAK_ORANGE}] aribot diagrams")
    console.print(f"  [{AYURAK_ORANGE}]$[/{AYURAK_ORANGE}] aribot compliance SOC2 <id>")
    console.print(f"  [{AYURAK_ORANGE}]$[/{AYURAK_ORANGE}] aribot --help")
    console.print()


def print_status(status: dict, rate_limits: dict = None):
    """Print API status."""
    console.print()
    console.print(ARIBOT_WORDMARK)
    console.print()

    health = status.get("status", "unknown")
    icon = "✓" if health == "healthy" else "✗"
    color = AYURAK_SUCCESS if health == "healthy" else AYURAK_ERROR

    console.print(f"  [{AYURAK_LIGHT_GRAY}]Status[/{AYURAK_LIGHT_GRAY}]    [{color}]{icon} {health.title()}[/{color}]")
    console.print(f"  [{AYURAK_LIGHT_GRAY}]Version[/{AYURAK_LIGHT_GRAY}]   {status.get('version', 'N/A')}")
    console.print(f"  [{AYURAK_LIGHT_GRAY}]Features[/{AYURAK_LIGHT_GRAY}]  {'Enabled' if status.get('features_enabled') else 'Disabled'}")

    if rate_limits:
        console.print()
        console.print(f"  [{AYURAK_GOLD}]Rate Limits[/{AYURAK_GOLD}]")
        console.print(f"  [{AYURAK_LIGHT_GRAY}]Per min[/{AYURAK_LIGHT_GRAY}]   {rate_limits.get('requests_per_minute', 'unlimited')}")
        console.print(f"  [{AYURAK_LIGHT_GRAY}]Per hour[/{AYURAK_LIGHT_GRAY}]  {rate_limits.get('requests_per_hour', 'unlimited')}")

    console.print()


def print_diagrams(diagrams: list, total: int = None):
    """Print diagrams table."""
    console.print()

    table = create_table("Your Diagrams")
    table.add_column("ID", style=f"bold {AYURAK_ORANGE}", width=10)
    table.add_column("Name", style="white", max_width=35)
    table.add_column("", justify="center", width=3)
    table.add_column("Threats", justify="right", style=AYURAK_GOLD, width=8)
    table.add_column("Created", style=AYURAK_LIGHT_GRAY, width=12)

    for d in diagrams:
        stage = d.get("stage", "")
        icon = f"[{AYURAK_SUCCESS}]✓[/{AYURAK_SUCCESS}]" if stage == "complete" else f"[{AYURAK_WARNING}]⋯[/{AYURAK_WARNING}]" if stage == "processing" else f"[{AYURAK_LIGHT_GRAY}]○[/{AYURAK_LIGHT_GRAY}]"

        threats = d.get("threats_count", 0)
        created = d.get("created_at", "")[:10] if d.get("created_at") else "-"

        table.add_row(
            d.get("id", "")[:8],
            d.get("name", "Untitled")[:35],
            icon,
            str(threats),
            created
        )

    console.print(table)
    console.print()
    console.print(f"[{AYURAK_LIGHT_GRAY}]Showing {len(diagrams)}{f' of {total}' if total else ''} diagrams[/{AYURAK_LIGHT_GRAY}]")
    console.print()


def print_threats(threats: list, diagram_name: str = None):
    """Print threats grouped by severity."""
    console.print()

    if diagram_name:
        console.print(f"[bold white]Threats[/bold white] [{AYURAK_LIGHT_GRAY}]{diagram_name}[/{AYURAK_LIGHT_GRAY}]")
        console.print()

    severities = ["critical", "high", "medium", "low"]
    for sev in severities:
        items = [t for t in threats if t.get("severity", "").lower() == sev]
        if not items:
            continue

        console.print(f"  {severity_badge(sev)} [{AYURAK_LIGHT_GRAY}]({len(items)})[/{AYURAK_LIGHT_GRAY}]")

        for t in items[:5]:
            title = t.get("title", "Untitled")[:55]
            console.print(f"    [{AYURAK_LIGHT_GRAY}]›[/{AYURAK_LIGHT_GRAY}] {title}")

        if len(items) > 5:
            console.print(f"    [{AYURAK_LIGHT_GRAY}]  + {len(items) - 5} more[/{AYURAK_LIGHT_GRAY}]")
        console.print()

    # Summary
    total = len(threats)
    crit = len([t for t in threats if t.get("severity", "").lower() == "critical"])
    high = len([t for t in threats if t.get("severity", "").lower() == "high"])

    console.print(f"[{AYURAK_GOLD}]Total:[/{AYURAK_GOLD}] {total} threats  ", end="")
    if crit > 0:
        console.print(f"[{AYURAK_ERROR}]{crit} critical[/{AYURAK_ERROR}]  ", end="")
    if high > 0:
        console.print(f"[{AYURAK_WARNING}]{high} high[/{AYURAK_WARNING}]", end="")
    console.print()
    console.print()


def print_export_success(filename: str, format_type: str):
    """Print export success."""
    console.print()
    console.print(f"[{AYURAK_SUCCESS}]✓[/{AYURAK_SUCCESS}] [bold white]Report exported[/bold white]")
    console.print()
    console.print(f"  [{AYURAK_LIGHT_GRAY}]Format[/{AYURAK_LIGHT_GRAY}]  {format_type.upper()}")
    console.print(f"  [{AYURAK_LIGHT_GRAY}]File[/{AYURAK_LIGHT_GRAY}]    {filename}")
    console.print()


def print_compliance_score(standard: str, score: int, passed: int, failed: int):
    """Print compliance score with visual bar."""
    console.print()
    console.print(f"[bold white]{standard}[/bold white] [bold {AYURAK_GOLD}]Compliance[/bold {AYURAK_GOLD}]")
    console.print()

    # Visual bar
    bar_width = 40
    filled = int((score / 100) * bar_width)
    color = AYURAK_SUCCESS if score >= 80 else AYURAK_WARNING if score >= 60 else AYURAK_ERROR

    bar = f"[{color}]{'█' * filled}[/{color}][{AYURAK_DARK_GRAY}]{'░' * (bar_width - filled)}[/{AYURAK_DARK_GRAY}]"

    console.print(f"  {bar} [{color}]{score}%[/{color}]")
    console.print()
    console.print(f"  [{AYURAK_SUCCESS}]✓ {passed} passed[/{AYURAK_SUCCESS}]   [{AYURAK_ERROR}]✗ {failed} failed[/{AYURAK_ERROR}]")
    console.print()


def print_methodologies(methodologies: list):
    """Print available methodologies."""
    console.print()
    console.print(f"[bold white]Threat Modeling Methodologies[/bold white]")
    console.print()

    for m in methodologies:
        console.print(f"  [{AYURAK_ORANGE}]◆[/{AYURAK_ORANGE}] [bold white]{m.get('name', '')}[/bold white]")
        if m.get('description'):
            console.print(f"    [{AYURAK_LIGHT_GRAY}]{m.get('description')}[/{AYURAK_LIGHT_GRAY}]")

    console.print()


# =============================================================================
# AI INTEGRATION HEADERS
# =============================================================================

def print_integration_header(tool: str):
    """Print AI tool integration header."""
    tools = {
        "claude": "Claude",
        "copilot": "GitHub Copilot",
        "gemini": "Gemini",
        "cursor": "Cursor",
    }

    name = tools.get(tool.lower(), tool)
    console.print()
    console.print(f"[bold {AYURAK_ORANGE}]◆[/bold {AYURAK_ORANGE}] [bold white]ARIBOT[/bold white] [{AYURAK_GOLD}]×[/{AYURAK_GOLD}] [bold white]{name}[/bold white]")
    console.print()
