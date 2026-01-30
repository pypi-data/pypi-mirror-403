"""
ASCII Banner and Branded Output for CYBRET Scanner
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from typing import Optional

# ASCII Art Banner
BANNER = r"""
   ______  ______  ____   ____  ______ ______
  / ____/ /_  __/ / __ ) / __ \/ ____//_  __/
 / /       / /   / __  |/ /_/ / __/    / /   
/ /___    / /   / /_/ // _, _/ /___   / /    
\____/   /_/   /_____//_/ |_/_____/  /_/     
                                             
    AI-Powered Logic Vulnerability Scanner
"""

BANNER_COMPACT = r"""
  _____ __ __ ___  ___  ___ _____
 / ___// //_// _ )/ _ \/ __/_  __/
/ /__ / ,<  / _  / , _/ _/  / /   
\___//_/|_|/____/_/|_/___/ /_/    
"""

VERSION = "1.0.0"
TAGLINE = "AI-Powered Logic Vulnerability Scanner"


def print_banner(console: Optional[Console] = None, compact: bool = False) -> None:
    """
    Print the CYBRET branded banner
    
    Args:
        console: Rich console instance (creates new one if None)
        compact: Use compact banner for smaller terminals
    """
    if console is None:
        console = Console()
    
    banner_text = BANNER_COMPACT if compact else BANNER
    
    # Create styled banner
    banner_styled = Text(banner_text, style="bold cyan")
    
    # Print banner
    console.print(banner_styled)
    console.print(f"[dim]Version {VERSION}[/dim]", justify="center")
    console.print()


def print_welcome(console: Optional[Console] = None) -> None:
    """
    Print welcome message with branding
    
    Args:
        console: Rich console instance (creates new one if None)
    """
    if console is None:
        console = Console()
    
    print_banner(console)
    
    welcome_text = Text.assemble(
        ("Welcome to ", "white"),
        ("CYBRET Scanner", "bold cyan"),
        ("\n\n", ""),
        ("Detect logic vulnerabilities with ", "white"),
        ("zero false positives", "bold green"),
        ("\n", ""),
        ("Powered by ", "white"),
        ("AI-driven autonomous remediation", "bold magenta"),
    )
    
    panel = Panel(
        welcome_text,
        border_style="cyan",
        padding=(1, 2),
    )
    
    console.print(panel)
    console.print()


def print_scan_header(
    directory: str,
    language: str,
    llm_enabled: bool = False,
    console: Optional[Console] = None
) -> None:
    """
    Print scan configuration header
    
    Args:
        directory: Directory being scanned
        language: Programming language
        llm_enabled: Whether LLM analysis is enabled
        console: Rich console instance
    """
    if console is None:
        console = Console()
    
    # Create scan info
    info_lines = [
        f"[bold]Target:[/bold] {directory}",
        f"[bold]Language:[/bold] {language}",
    ]
    
    if llm_enabled:
        info_lines.append("[bold]AI Analysis:[/bold] [green]Enabled[/green]")
    else:
        info_lines.append("[bold]AI Analysis:[/bold] [dim]Disabled[/dim]")
    
    info_text = "\n".join(info_lines)
    
    panel = Panel(
        info_text,
        title="[bold cyan]Scan Configuration[/bold cyan]",
        border_style="blue",
        padding=(0, 2),
    )
    
    console.print(panel)
    console.print()


def print_scan_summary(
    vulnerabilities_found: int,
    files_scanned: int,
    scan_time: float,
    high_confidence: int = 0,
    console: Optional[Console] = None
) -> None:
    """
    Print scan completion summary
    
    Args:
        vulnerabilities_found: Number of vulnerabilities found
        files_scanned: Number of files scanned
        scan_time: Scan duration in seconds
        high_confidence: Number of high-confidence findings
        console: Rich console instance
    """
    if console is None:
        console = Console()
    
    console.print()
    console.print("=" * 60)
    console.print("[bold green]Scan Complete![/bold green]")
    console.print("=" * 60)
    console.print()
    
    # Summary stats
    console.print(f"[bold]Files Scanned:[/bold] {files_scanned}")
    console.print(f"[bold]Scan Time:[/bold] {scan_time:.2f}s")
    
    if vulnerabilities_found > 0:
        console.print(f"[bold]Vulnerabilities Found:[/bold] [red]{vulnerabilities_found}[/red]")
        if high_confidence > 0:
            console.print(f"[bold]High Confidence:[/bold] [yellow]{high_confidence}[/yellow]")
    else:
        console.print(f"[bold]Vulnerabilities Found:[/bold] [green]0[/green]")
    
    console.print()


def print_feature_badge(
    feature: str,
    enabled: bool = True,
    console: Optional[Console] = None
) -> None:
    """
    Print a feature badge
    
    Args:
        feature: Feature name
        enabled: Whether feature is enabled
        console: Rich console instance
    """
    if console is None:
        console = Console()
    
    if enabled:
        console.print(f"[green]✓[/green] {feature}", end="  ")
    else:
        console.print(f"[dim]○[/dim] {feature}", end="  ")


def print_cybret_footer(console: Optional[Console] = None) -> None:
    """
    Print CYBRET footer with links
    
    Args:
        console: Rich console instance
    """
    if console is None:
        console = Console()
    
    console.print()
    console.print("[dim]" + "-" * 60 + "[/dim]")
    console.print(
        "[dim]CYBRET AI | https://github.com/cybret/cybret-scanner[/dim]",
        justify="center"
    )
    console.print("[dim]Report issues: https://github.com/cybret/cybret-scanner/issues[/dim]", justify="center")
    console.print()


# Quick access functions
def show_banner(compact: bool = False) -> None:
    """Show banner in default console"""
    print_banner(compact=compact)


def show_welcome() -> None:
    """Show welcome message in default console"""
    print_welcome()


if __name__ == "__main__":
    # Demo the banner
    console = Console()
    print_welcome(console)
    print_scan_header("./my-app", "javascript", llm_enabled=True, console=console)
    print_scan_summary(5, 42, 3.14, high_confidence=2, console=console)
    print_cybret_footer(console)
