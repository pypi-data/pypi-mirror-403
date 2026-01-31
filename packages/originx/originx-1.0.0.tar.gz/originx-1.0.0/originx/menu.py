"""
Interactive menu system for OriginX
"""

import asyncio
import json
from typing import Optional, List
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from .core import OriginScanner
from .utils.config import APIConfig, ScanConfig
from .utils.models import ScanResult
from .utils.helpers import normalize_domain, format_duration
from .banner import show_banner

console = Console()

class InteractiveMenu:
    """Interactive menu system for OriginX"""
    
    def __init__(self):
        self.api_config = APIConfig.from_env()
        self.last_result: Optional[ScanResult] = None
    
    async def run(self):
        """Run the interactive menu"""
        show_banner()
       
        while True:
            choice = self._show_main_menu()
            
            if choice == '0':
                console.print("[bold green]Thanks for using OriginX![/bold green]")
                break
            elif choice == '1':
                await self._quick_scan()
            elif choice == '2':
                await self._deep_scan()
            elif choice == '3':
                await self._passive_scan()
            elif choice == '4':
                await self._favicon_hunt()
            elif choice == '5':
                await self._verify_ips()
            elif choice == '6':
                self._view_last_results()
            elif choice == '7':
                await self._export_report()
            elif choice == '8':
                self.status()
            else:
                console.print("[bold red]Invalid choice. Please try again.[/bold red]")
    
    def _show_main_menu(self) -> str:
        """Display main menu and get user choice"""
        menu_text = Text()
        menu_text.append("ORIGINX MAIN MENU\n\n", style="bold cyan")
        menu_text.append("[1] Quick Scan (Fast reconnaissance)\n", style="white")
        menu_text.append("[2] Deep Scan (Comprehensive analysis)\n", style="white")
        menu_text.append("[3] Passive Recon Only\n", style="white")
        menu_text.append("[4] Favicon Hash Hunt\n", style="white")
        menu_text.append("[5] Verify Candidate IPs\n", style="white")
        menu_text.append("[6] View Last Scan Results\n", style="white")
        menu_text.append("[7] Export Report\n", style="white")
        menu_text.append("[8] API Status\n", style="white")
        menu_text.append("[0] Exit\n", style="bold red")
        
        menu_panel = Panel(menu_text, border_style="cyan")
        console.print(menu_panel)
        
        return Prompt.ask("Select an option", choices=['0', '1', '2', '3', '4', '5', '6', '7', '8'])
    
    async def _quick_scan(self):
        """Perform quick scan"""
        domain = self._get_domain_input()
        if not domain:
            return
        
        config = ScanConfig(
            fast_mode=True,
            confidence_threshold=70,
            verify_origins=True
        )
        
        await self._perform_scan(domain, config, "Quick Scan")
    
    async def _deep_scan(self):
        """Perform deep scan"""
        domain = self._get_domain_input()
        if not domain:
            return
        
        config = ScanConfig(
            deep_scan=True,
            confidence_threshold=60,
            verify_origins=True,
            timeout=45
        )
        
        await self._perform_scan(domain, config, "Deep Scan")
    
    async def _passive_scan(self):
        """Perform passive reconnaissance only"""
        domain = self._get_domain_input()
        if not domain:
            return
        
        config = ScanConfig(
            passive_only=True,
            verify_origins=False,
            confidence_threshold=50
        )
        
        await self._perform_scan(domain, config, "Passive Reconnaissance")
    
    async def _favicon_hunt(self):
        """Perform favicon hash hunt"""
        domain = self._get_domain_input()
        if not domain:
            return
        
        console.print(f"[bold yellow][*] Starting favicon hash hunt for {domain}...[/bold yellow]")
        
        try:
            async with OriginScanner(self.api_config) as scanner:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Hunting favicon hash...", total=None)
                    
                    # Get favicon hash and search
                    from .recon.favicon import FaviconRecon
                    favicon_recon = FaviconRecon(self.api_config)
                    
                    async with favicon_recon:
                        candidates = await favicon_recon.search(domain)
                    
                    progress.update(task, description="Completed favicon hunt")
                
                if candidates:
                    self._display_candidates(candidates, "Favicon Hash Results")
                else:
                    console.print("[bold red][x] No results found via favicon hash[/bold red]")
        
        except Exception as e:
            console.print(f"[bold red][x] Error during favicon hunt: {e}[/bold red]")
    
    async def _verify_ips(self):
        """Verify candidate IPs"""
        domain = self._get_domain_input()
        if not domain:
            return
        
        # Get IPs to verify
        ips_input = Prompt.ask("Enter IP addresses to verify (comma-separated)")
        if not ips_input:
            return
        
        ips = [ip.strip() for ip in ips_input.split(',')]
        
        console.print(f"[bold yellow][*] Verifying {len(ips)} IP addresses...[/bold yellow]")
        
        try:
            async with OriginScanner(self.api_config) as scanner:
                from .utils.models import IPCandidate
                candidates = [IPCandidate(ip=ip, source='manual') for ip in ips]
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Verifying IPs...", total=None)
                    
                    results = await scanner.verifier.verify_candidates(domain, candidates)
                    
                    progress.update(task, description="Verification completed")
                
                self._display_verification_results(results)
        
        except Exception as e:
            console.print(f"[bold red][x] Error during verification: {e}[/bold red]")
    
    def _view_last_results(self):
        """View last scan results"""
        if not self.last_result:
            console.print("[bold red][x] No previous scan results available[/bold red]")
            return
        
        self._display_scan_results(self.last_result)
    
    async def _export_report(self):
        """Export scan report"""
        if not self.last_result:
            console.print("[bold red][x] No scan results to export[/bold red]")
            return
        
        format_choice = Prompt.ask(
            "Export format",
            choices=['json', 'txt'],
            default='json'
        )
        
        filename = Prompt.ask(
            "Output filename",
            default=f"originx_report_{self.last_result.target}.{format_choice}"
        )
        
        try:
            if format_choice == 'json':
                await self._export_json(filename)
            else:
                await self._export_txt(filename)
            
            console.print(f"[bold green][>] Report exported to {filename}[/bold green]")
        
        except Exception as e:
            console.print(f"[bold red][x] Export failed: {e}[/bold red]")
    
    def _show_api_status(self):
        """Show API configuration status"""
        available_sources = self.api_config.get_available_sources()
        
        status_table = Table(title="API Configuration Status")
        status_table.add_column("Service", style="cyan")
        status_table.add_column("Status", style="white")
        status_table.add_column("Notes", style="dim")
        
        services = [
            ("Shodan", bool(self.api_config.shodan_key), "Requires SHODAN_API_KEY"),
            ("Censys", bool(self.api_config.censys_id and self.api_config.censys_secret), "Requires CENSYS_API_ID and CENSYS_API_SECRET"),
            ("VirusTotal", bool(self.api_config.virustotal_key), "Requires VIRUSTOTAL_API_KEY"),
            ("SecurityTrails", bool(self.api_config.securitytrails_key), "Requires SECURITYTRAILS_API_KEY"),
            ("DNS", True, "Always available"),
            ("ViewDNS", True, "Always available"),
            ("OTX", True, "Always available"),
            ("Favicon", True, "Always available")
        ]
        
        for service, available, notes in services:
            status = "[bold green][>] Available[/bold green]" if available else "[bold red][x] Not configured[/bold red]"
            status_table.add_row(service, status, notes)
        
        console.print(status_table)
        console.print(f"\n[bold cyan]Total available sources: {len(available_sources)}[/bold cyan]")
    
    def _get_domain_input(self) -> Optional[str]:
        """Get and validate domain input"""
        domain = Prompt.ask("Enter target domain")
        if not domain:
            return None
        
        domain = normalize_domain(domain)
        
        if not domain:
            console.print("[bold red][x] Invalid domain format[/bold red]")
            return None
        
        return domain
    
    async def _perform_scan(self, domain: str, config: ScanConfig, scan_type: str):
        """Perform scan with progress display"""
        console.print(f"[bold yellow] Starting {scan_type} for {domain}...[/bold yellow]")
        
        try:
            async with OriginScanner(self.api_config, config) as scanner:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console
                ) as progress:
                    task = progress.add_task("Scanning...", total=None)
                    
                    result = await scanner.scan(domain)
                    self.last_result = result
                    
                    progress.update(task, description="Scan completed")
                
                self._display_scan_results(result)
        
        except Exception as e:
            console.print(f"[bold red][x] Scan failed: {e}[/bold red]")
    
    def _display_scan_results(self, result: ScanResult):
        """Display comprehensive scan results"""
        console.print(f"\n[bold green][>] SCAN RESULTS FOR {result.target.upper()}[/bold green]")
        console.print(f"[dim]Scan duration: {format_duration(result.scan_duration)}[/dim]")
        console.print(f"[dim]Sources used: {', '.join(result.sources_used)}[/dim]\n")
        
        # WAF Information
        if result.waf_info.detected:
            waf_panel = Panel(
                f"[bold red][!] WAF DETECTED: {result.waf_info.provider}[/bold red]\n"
                f"Confidence: {result.waf_info.confidence}%\n"
                f"Evidence: {', '.join(result.waf_info.evidence)}",
                title="WAF Detection",
                border_style="red"
            )
            console.print(waf_panel)
        else:
            console.print("[bold green][>] No WAF detected[/bold green]\n")
        
        # High confidence origins
        high_confidence = result.get_high_confidence_origins(80)
        if high_confidence:
            console.print("[bold red][>>] LIKELY ORIGIN SERVERS (80%+ confidence):[/bold red]")
            for origin in high_confidence:
                console.print(f"  * {origin.ip} (Confidence: {origin.confidence_score}%)")
            console.print()
        
        # All candidates
        if result.candidates:
            self._display_candidates(result.candidates, "All IP Candidates")
        
        # Verification results
        if result.verified_origins:
            self._display_verification_results(result.verified_origins)
    
    def _display_candidates(self, candidates: List, title: str):
        """Display IP candidates in a table"""
        if not candidates:
            return
        
        table = Table(title=title)
        table.add_column("IP Address", style="cyan")
        table.add_column("Source", style="white")
        table.add_column("Confidence", style="yellow")
        table.add_column("Port", style="dim")
        table.add_column("Service", style="dim")
        
        for candidate in candidates[:20]:  # Limit display
            table.add_row(
                candidate.ip,
                candidate.source,
                f"{candidate.confidence}%",
                str(candidate.port) if candidate.port else "-",
                candidate.service or "-"
            )
        
        console.print(table)
        console.print()
    
    def _display_verification_results(self, results: List):
        """Display verification results"""
        if not results:
            return
        
        table = Table(title="Origin Verification Results")
        table.add_column("IP Address", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Confidence", style="yellow")
        table.add_column("Response", style="dim")
        table.add_column("Cert Match", style="dim")
        table.add_column("Similarity", style="dim")
        
        for result in results:
            status = "[bold green][>] ORIGIN[/bold green]" if result.is_origin else "[bold red][x] Not Origin[/bold red]"
            cert_status = "[>]" if result.cert_match else "[x]"
            similarity = f"{result.content_similarity:.1%}" if result.content_similarity else "-"
            response = f"{result.response_code}" if result.response_code else "Failed"
            
            table.add_row(
                result.ip,
                status,
                f"{result.confidence_score}%",
                response,
                cert_status,
                similarity
            )
        
        console.print(table)
        console.print()
    
    async def _export_json(self, filename: str):
        """Export results as JSON"""
        if not self.last_result:
            return
        
        # Convert to serializable format
        data = {
            'target': self.last_result.target,
            'timestamp': self.last_result.timestamp.isoformat(),
            'scan_duration': self.last_result.scan_duration,
            'sources_used': self.last_result.sources_used,
            'waf_info': {
                'detected': self.last_result.waf_info.detected,
                'provider': self.last_result.waf_info.provider,
                'confidence': self.last_result.waf_info.confidence,
                'evidence': self.last_result.waf_info.evidence
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
                for c in self.last_result.candidates
            ],
            'verified_origins': [
                {
                    'ip': v.ip,
                    'is_origin': v.is_origin,
                    'confidence_score': v.confidence_score,
                    'response_code': v.response_code,
                    'cert_match': v.cert_match,
                    'content_similarity': v.content_similarity,
                    'waf_detected': v.waf_detected,
                    'error': v.error,
                    'metadata': v.metadata
                }
                for v in self.last_result.verified_origins
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    async def _export_txt(self, filename: str):
        """Export results as text"""
        if not self.last_result:
            return
        
        with open(filename, 'w') as f:
            f.write(f"OriginX Scan Report\n")
            f.write(f"==================\n\n")
            f.write(f"Target: {self.last_result.target}\n")
            f.write(f"Scan Duration: {format_duration(self.last_result.scan_duration)}\n")
            f.write(f"Sources Used: {', '.join(self.last_result.sources_used)}\n\n")
            
            # WAF Info
            if self.last_result.waf_info.detected:
                f.write(f"WAF Detected: {self.last_result.waf_info.provider}\n")
                f.write(f"WAF Confidence: {self.last_result.waf_info.confidence}%\n\n")
            
            # High confidence origins
            high_confidence = self.last_result.get_high_confidence_origins(80)
            if high_confidence:
                f.write("LIKELY ORIGIN SERVERS (80%+ confidence):\n")
                for origin in high_confidence:
                    f.write(f"  - {origin.ip} ({origin.confidence_score}%)\n")
                f.write("\n")
            
            # All candidates
            f.write("IP CANDIDATES:\n")
            for candidate in self.last_result.candidates:
                f.write(f"  - {candidate.ip} ({candidate.source}, {candidate.confidence}%)\n")
            f.write("\n")
            
            # Verification results
            f.write("VERIFICATION RESULTS:\n")
            for result in self.last_result.verified_origins:
                status = "ORIGIN" if result.is_origin else "Not Origin"
                f.write(f"  - {result.ip}: {status} ({result.confidence_score}%)\n")