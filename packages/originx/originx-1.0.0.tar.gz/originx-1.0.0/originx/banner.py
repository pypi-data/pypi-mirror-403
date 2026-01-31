"""
Banner display module for OriginX
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

console = Console()

BANNER_ASCII = """
 ██████╗ ██████╗ ██╗ ██████╗ ██╗███╗   ██╗██╗  ██╗
██╔═══██╗██╔══██╗██║██╔════╝ ██║████╗  ██║╚██╗██╔╝
██║   ██║██████╔╝██║██║  ███╗██║██╔██╗ ██║ ╚███╔╝ 
██║   ██║██╔══██╗██║██║   ██║██║██║╚██╗██║ ██╔██╗ 
╚██████╔╝██║  ██║██║╚██████╔╝██║██║ ╚████║██╔╝ ██╗
 ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝
"""

def show_banner():
    """Display the startup banner with ethical use warning"""
    banner_text = Text(BANNER_ASCII, style="bold cyan")
    
    info_text = Text()
    info_text.append("Origin IP Discovery Tool\n", style="bold white")
    info_text.append("Author: ", style="dim white")
    info_text.append("LAKSHMIKANTHAN K (letchupkt)\n", style="bold green")
    info_text.append("[!] Passive Recon | Bug Bounty Friendly", style="bold yellow")
    
    banner_panel = Panel(
        Align.center(banner_text),
        title="[bold red]OriginX v1.0.0[/bold red]",
        border_style="red"
    )
    
    info_panel = Panel(
        Align.center(info_text),
        border_style="yellow"
    )
    
    console.print()
    console.print(banner_panel)
    console.print(info_panel)
    console.print()

