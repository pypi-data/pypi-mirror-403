"""
Command-line interface for OriginX
"""

import asyncio
import json
import sys
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from .banner import show_banner
from .menu import InteractiveMenu
from .core import OriginScanner
from .utils.config import APIConfig, ScanConfig
from .utils.models import ScanResult
from .utils.helpers import normalize_domain, format_duration, sanitize_filename

app = typer.Typer(
    name="originx",
    help="Professional WAF Origin IP Discovery Tool",
    add_completion=False
)
console = Console()

def main_scan(
    target: str = typer.Argument(..., help="Target domain to scan"),
    fast: bool = typer.Option(False, "--fast", "--quick", help="Fast scan mode (limited sources)"),
    passive: bool = typer.Option(False, "--passive", "--passive-only", help="Passive reconnaissance only"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip origin verification"),
    no_waf: bool = typer.Option(False, "--no-waf", help="Skip WAF detection"),
    confidence: int = typer.Option(70, "--confidence", help="Confidence threshold (0-100)"),
    output: str = typer.Option("table", "--output", "-o", help="Output format: table, json, txt"),
    save: Optional[str] = typer.Option(None, "--save", "-s", help="Save results to file"),
    timeout: int = typer.Option(30, "--timeout", help="Request timeout in seconds"),
    concurrent: int = typer.Option(10, "--concurrent", help="Maximum concurrent requests")
):
    """
    Scan a domain for origin IP addresses behind WAF/CDN.
    
    By default, performs a comprehensive deep scan using all available sources.
    Use --fast for quick results with limited sources.
    """
    
    show_banner()
    
    
    # Validate domain
    target = normalize_domain(target)
    if not target:
        console.print("[bold red][-] Invalid domain format[/bold red]")
        raise typer.Exit(1)
    
    # Validate confidence threshold
    if not 0 <= confidence <= 100:
        console.print("[bold red][-] Confidence threshold must be between 0 and 100[/bold red]")
        raise typer.Exit(1)
    
    # Create configuration
    api_config = APIConfig.from_env()
    
    # Configure scan based on mode
    if fast:
        scan_config = ScanConfig(
            fast_mode=True,
            confidence_threshold=confidence,
            verify_origins=not no_verify,
            detect_waf=not no_waf,
            timeout=timeout,
            max_concurrent=concurrent,
            output_format=output,
            output_file=save
        )
        console.print(f"[bold yellow][*] Fast scan mode enabled[/bold yellow]")
    elif passive:
        scan_config = ScanConfig(
            passive_only=True,
            verify_origins=False,
            detect_waf=not no_waf,
            confidence_threshold=max(confidence - 20, 30),  # Lower threshold for passive
            timeout=timeout,
            max_concurrent=concurrent,
            output_format=output,
            output_file=save
        )
        console.print(f"[bold blue][*] Passive reconnaissance mode enabled[/bold blue]")
    else:
        # Default: Deep comprehensive scan
        scan_config = ScanConfig(
            deep_scan=True,
            confidence_threshold=confidence,
            verify_origins=not no_verify,
            detect_waf=not no_waf,
            timeout=timeout,
            max_concurrent=concurrent,
            output_format=output,
            output_file=save
        )
        console.print(f"[bold green][*] Deep scan mode enabled (comprehensive)[/bold green]")
    
    # Check API availability
    available_sources = api_config.get_available_sources()
    if len(available_sources) < 4:
        console.print(f"[bold yellow][!] Only {len(available_sources)} sources available. Configure API keys for better results.[/bold yellow]")
    else:
        console.print(f"[bold green][+] {len(available_sources)} reconnaissance sources available[/bold green]")
    
    # Run scan
    try:
        result = asyncio.run(_run_scan(target, api_config, scan_config))
        
        # Display results
        _display_results(result, output)
        
        # Save to file if requested
        if save:
            if save.endswith('.json') or output == 'json':
                _save_json_results(result, save)
            else:
                _save_text_results(result, save)
            console.print(f"[bold green][+] Results saved to {save}[/bold green]")
    
    except KeyboardInterrupt:
        console.print("\n[bold red][-] Scan interrupted by user[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red][-] Scan failed: {e}[/bold red]")
        raise typer.Exit(1)

# Make the main scan command the default
app.command()(main_scan)

@app.command()
def menu():
    """Launch interactive menu mode"""
    try:
        menu_system = InteractiveMenu()
        asyncio.run(menu_system.run())
    except KeyboardInterrupt:
        console.print("\n[bold red][-] Interrupted by user[/bold red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red][-] Menu failed: {e}[/bold red]")
        raise typer.Exit(1)

@app.command()
def config():
    """Show API configuration status"""
    show_banner()
    
    api_config = APIConfig.from_env()
    available_sources = api_config.get_available_sources()
    
    config_table = Table(title="OriginX Configuration Status")
    config_table.add_column("Service", style="cyan")
    config_table.add_column("Status", style="white")
    config_table.add_column("Environment Variable", style="dim")
    
    services = [
        ("Shodan", bool(api_config.shodan_key), "SHODAN_API_KEY"),
        ("Censys", bool(api_config.censys_id and api_config.censys_secret), "CENSYS_API_ID, CENSYS_API_SECRET"),
        ("VirusTotal", bool(api_config.virustotal_key), "VIRUSTOTAL_API_KEY"),
        ("SecurityTrails", bool(api_config.securitytrails_key), "SECURITYTRAILS_API_KEY"),
        ("DNS", True, "Built-in"),
        ("ViewDNS", True, "Built-in"),
        ("AlienVault OTX", True, "Built-in"),
        ("Favicon Hash", True, "Built-in")
    ]
    
    for service, available, env_var in services:
        status = "[bold green][+] Configured[/bold green]" if available else "[bold red][-] Not configured[/bold red]"
        config_table.add_row(service, status, env_var)
    
    console.print(config_table)
    console.print(f"\n[bold cyan]Total available sources: {len(available_sources)}[/bold cyan]")
    
    if len(available_sources) < 6:
        console.print("\n[bold yellow][*] Tip: Configure API keys for better results![/bold yellow]")
        console.print("Set environment variables for the services you want to use.")

@app.command()
def version():
    """Show version information"""
    from . import __version__, __author__
    
    version_panel = Panel(
        f"[bold cyan]OriginX v{__version__}[/bold cyan]\n"
        f"Author: [bold green]{__author__}[/bold green]\n"
        f"License: [bold white]MIT[/bold white]\n"
        f"Purpose: [bold yellow]Bug bounty & defensive security research[/bold yellow]",
        title="Version Information",
        border_style="cyan"
    )
    
    console.print(version_panel)

async def _run_scan(target: str, api_config: APIConfig, scan_config: ScanConfig) -> ScanResult:
    """Run the actual scan with progress display"""
    
    console.print(f"[bold yellow][*] Starting scan for {target}...[/bold yellow]")
    
    async with OriginScanner(api_config, scan_config) as scanner:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Scanning...", total=None)
            
            result = await scanner.scan(target)
            
            progress.update(task, description="Scan completed")
    
    return result

def _display_results(result: ScanResult, output_format: str):
    """Display scan results in the specified format"""
    
    if output_format == "json":
        _display_json_results(result)
    elif output_format == "txt":
        _display_text_results(result)
    else:
        _display_table_results(result)

def _display_table_results(result: ScanResult):
    """Display results in table format"""
    console.print(f"\n[bold green][>>] SCAN RESULTS FOR {result.target.upper()}[/bold green]")
    console.print(f"[dim]Duration: {format_duration(result.scan_duration)} | Sources: {', '.join(result.sources_used)}[/dim]\n")
    
    # WAF Detection
    if result.waf_info.detected:
        waf_panel = Panel(
            f"[bold red][!] WAF DETECTED: {result.waf_info.provider}[/bold red]\n"
            f"Confidence: {result.waf_info.confidence}%",
            title="WAF Detection",
            border_style="red"
        )
        console.print(waf_panel)
    else:
        console.print("[bold green][+] No WAF detected[/bold green]\n")
    
    # High confidence origins
    high_confidence = result.get_high_confidence_origins(80)
    if high_confidence:
        console.print("[bold red][>>] LIKELY ORIGIN SERVERS (80%+ confidence):[/bold red]")
        for origin in high_confidence:
            console.print(f"  * [bold cyan]{origin.ip}[/bold cyan] (Confidence: [bold yellow]{origin.confidence_score}%[/bold yellow])")
        console.print()
    
    # All candidates table
    if result.candidates:
        candidates_table = Table(title="IP Candidates")
        candidates_table.add_column("IP Address", style="cyan")
        candidates_table.add_column("Source", style="white")
        candidates_table.add_column("Confidence", style="yellow")
        candidates_table.add_column("Port", style="dim")
        
        for candidate in result.candidates[:20]:  # Limit display
            candidates_table.add_row(
                candidate.ip,
                candidate.source,
                f"{candidate.confidence}%",
                str(candidate.port) if candidate.port else "-"
            )
        
        console.print(candidates_table)
    
    # Verification results
    if result.verified_origins:
        verification_table = Table(title="Origin Verification")
        verification_table.add_column("IP Address", style="cyan")
        verification_table.add_column("Status", style="white")
        verification_table.add_column("Confidence", style="yellow")
        verification_table.add_column("Response", style="dim")
        verification_table.add_column("Cert Match", style="dim")
        
        for verify_result in result.verified_origins:
            status = "[bold green][+] ORIGIN[/bold green]" if verify_result.is_origin else "[bold red][-] Not Origin[/bold red]"
            cert_status = "[+]" if verify_result.cert_match else "[-]"
            response = f"{verify_result.response_code}" if verify_result.response_code else "Failed"
            
            verification_table.add_row(
                verify_result.ip,
                status,
                f"{verify_result.confidence_score}%",
                response,
                cert_status
            )
        
        console.print(verification_table)

def _display_json_results(result: ScanResult):
    """Display results in JSON format"""
    data = _convert_result_to_dict(result)
    console.print(json.dumps(data, indent=2))

def _display_text_results(result: ScanResult):
    """Display results in plain text format"""
    console.print(f"OriginX Scan Report")
    console.print(f"==================")
    console.print(f"Target: {result.target}")
    console.print(f"Duration: {format_duration(result.scan_duration)}")
    console.print(f"Sources: {', '.join(result.sources_used)}")
    console.print()
    
    if result.waf_info.detected:
        console.print(f"WAF Detected: {result.waf_info.provider} ({result.waf_info.confidence}%)")
        console.print()
    
    high_confidence = result.get_high_confidence_origins(80)
    if high_confidence:
        console.print("LIKELY ORIGIN SERVERS (80%+ confidence):")
        for origin in high_confidence:
            console.print(f"  - {origin.ip} ({origin.confidence_score}%)")
        console.print()
    
    console.print("IP CANDIDATES:")
    for candidate in result.candidates:
        console.print(f"  - {candidate.ip} ({candidate.source}, {candidate.confidence}%)")
    console.print()
    
    if result.verified_origins:
        console.print("VERIFICATION RESULTS:")
        for verify_result in result.verified_origins:
            status = "ORIGIN" if verify_result.is_origin else "Not Origin"
            console.print(f"  - {verify_result.ip}: {status} ({verify_result.confidence_score}%)")

def _save_json_results(result: ScanResult, filename: str):
    """Save results to JSON file"""
    data = _convert_result_to_dict(result)
    
    # Sanitize filename
    filename = sanitize_filename(filename)
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def _save_text_results(result: ScanResult, filename: str):
    """Save results to text file"""
    filename = sanitize_filename(filename)
    
    with open(filename, 'w') as f:
        f.write(f"OriginX Scan Report\n")
        f.write(f"==================\n\n")
        f.write(f"Target: {result.target}\n")
        f.write(f"Duration: {format_duration(result.scan_duration)}\n")
        f.write(f"Sources: {', '.join(result.sources_used)}\n\n")
        
        # WAF Info
        if result.waf_info.detected:
            f.write(f"WAF Detected: {result.waf_info.provider}\n")
            f.write(f"WAF Confidence: {result.waf_info.confidence}%\n\n")
        
        # High confidence origins
        high_confidence = result.get_high_confidence_origins(80)
        if high_confidence:
            f.write("LIKELY ORIGIN SERVERS (80%+ confidence):\n")
            for origin in high_confidence:
                f.write(f"  - {origin.ip} ({origin.confidence_score}%)\n")
            f.write("\n")
        
        # All candidates
        f.write("IP CANDIDATES:\n")
        for candidate in result.candidates:
            f.write(f"  - {candidate.ip} ({candidate.source}, {candidate.confidence}%)\n")
        f.write("\n")
        
        # Verification results
        if result.verified_origins:
            f.write("VERIFICATION RESULTS:\n")
            for result_item in result.verified_origins:
                status = "ORIGIN" if result_item.is_origin else "Not Origin"
                f.write(f"  - {result_item.ip}: {status} ({result_item.confidence_score}%)\n")

def _convert_result_to_dict(result: ScanResult) -> dict:
    """Convert ScanResult to dictionary for JSON serialization"""
    return {
        'target': result.target,
        'timestamp': result.timestamp.isoformat(),
        'scan_duration': result.scan_duration,
        'sources_used': result.sources_used,
        'waf_info': {
            'detected': result.waf_info.detected,
            'provider': result.waf_info.provider,
            'confidence': result.waf_info.confidence,
            'evidence': result.waf_info.evidence
        },
        'candidates': [
            {
                'ip': c.ip,
                'source': c.source,
                'confidence': c.confidence,
                'port': c.port,
                'service': c.service,
                'metadata': c.metadata
            }
            for c in result.candidates
        ],
        'verified_origins': [
            {
                'ip': v.ip,
                'is_origin': v.is_origin,
                'confidence_score': v.confidence_score,
                'response_code': v.response_code,
                'response_time': v.response_time,
                'cert_match': v.cert_match,
                'content_similarity': v.content_similarity,
                'waf_detected': v.waf_detected,
                'error': v.error,
                'metadata': v.metadata
            }
            for v in result.verified_origins
        ]
    }

def main():
    """Main entry point"""
    # If no arguments provided, launch interactive menu
    if len(sys.argv) == 1:
        try:
            menu_system = InteractiveMenu()
            asyncio.run(menu_system.run())
        except KeyboardInterrupt:
            console.print("\n[bold red][-] Interrupted by user[/bold red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[bold red][-] Error: {e}[/bold red]")
            sys.exit(1)
    else:
        # Run CLI with arguments
        app()

if __name__ == "__main__":
    main()