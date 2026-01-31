"""
Core scanning engine for OriginX
"""

import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from .waf import WAFDetector
from .verify.engine import OriginVerifier
from .utils.config import APIConfig, ScanConfig
from .utils.models import ScanResult, IPCandidate, WAFInfo
from .utils.helpers import normalize_domain

# Import all recon modules
from .recon.dns import DNSRecon
from .recon.shodan import ShodanRecon
from .recon.censys import CensysRecon
from .recon.virustotal import VirusTotalRecon
from .recon.securitytrails import SecurityTrailsRecon
from .recon.favicon import FaviconRecon
from .recon.viewdns import ViewDNSRecon
from .recon.otx import OTXRecon

class OriginScanner:
    """Main scanning engine that orchestrates all reconnaissance modules"""
    
    def __init__(self, api_config: APIConfig, scan_config: Optional[ScanConfig] = None):
        self.api_config = api_config
        self.scan_config = scan_config or ScanConfig()
        
        # Initialize components
        self.waf_detector = WAFDetector(timeout=self.scan_config.timeout)
        self.verifier = OriginVerifier(
            timeout=self.scan_config.timeout,
            max_concurrent=self.scan_config.max_concurrent
        )
        
        # Initialize recon modules
        self.recon_modules = self._initialize_recon_modules()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass
    
    def _initialize_recon_modules(self) -> Dict[str, Any]:
        """Initialize all reconnaissance modules"""
        modules = {
            'dns': DNSRecon(self.api_config, self.scan_config.timeout),
            'viewdns': ViewDNSRecon(self.api_config, self.scan_config.timeout),
            'otx': OTXRecon(self.api_config, self.scan_config.timeout),
            'favicon': FaviconRecon(self.api_config, self.scan_config.timeout)
        }
        
        # Add API-dependent modules if available
        if self.api_config.shodan_key:
            modules['shodan'] = ShodanRecon(self.api_config, self.scan_config.timeout)
        
        if self.api_config.censys_id and self.api_config.censys_secret:
            modules['censys'] = CensysRecon(self.api_config, self.scan_config.timeout)
        
        if self.api_config.virustotal_key:
            modules['virustotal'] = VirusTotalRecon(self.api_config, self.scan_config.timeout)
        
        if self.api_config.securitytrails_key:
            modules['securitytrails'] = SecurityTrailsRecon(self.api_config, self.scan_config.timeout)
        
        return modules
    
    async def scan(self, domain: str) -> ScanResult:
        """Perform complete origin IP discovery scan"""
        start_time = time.time()
        domain = normalize_domain(domain)
        
        # Step 1: WAF Detection
        waf_info = WAFInfo(detected=False)
        if self.scan_config.detect_waf:
            async with self.waf_detector:
                waf_info = await self.waf_detector.detect_waf(domain)
        
        # Step 2: Passive Reconnaissance
        candidates = await self._run_reconnaissance(domain)
        
        # Step 3: Origin Verification (if not passive-only)
        verified_origins = []
        if not self.scan_config.passive_only and self.scan_config.verify_origins:
            async with self.verifier:
                verified_origins = await self.verifier.verify_candidates(domain, candidates)
        
        # Step 4: Filter by confidence threshold
        high_confidence_candidates = [
            c for c in candidates 
            if c.confidence >= self.scan_config.confidence_threshold
        ]
        
        scan_duration = time.time() - start_time
        sources_used = list(self.recon_modules.keys())
        
        return ScanResult(
            target=domain,
            waf_info=waf_info,
            candidates=high_confidence_candidates,
            verified_origins=verified_origins,
            scan_duration=scan_duration,
            timestamp=datetime.now(),
            sources_used=sources_used
        )
    
    async def _run_reconnaissance(self, domain: str) -> List[IPCandidate]:
        """Run all available reconnaissance modules"""
        all_candidates = []
        
        # Determine which modules to run
        modules_to_run = self._select_modules_for_scan()
        
        # Run modules concurrently
        tasks = []
        for module_name, module in modules_to_run.items():
            task = self._run_single_module(module_name, module, domain)
            tasks.append(task)
        
        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, list):
                all_candidates.extend(result)
            elif isinstance(result, Exception):
                # Log error but continue
                continue
        
        # Deduplicate candidates
        unique_candidates = self._deduplicate_candidates(all_candidates)
        
        return unique_candidates
    
    def _select_modules_for_scan(self) -> Dict[str, Any]:
        """Select which modules to run based on scan configuration"""
        modules_to_run = {}
        
        # Always include DNS and free sources
        always_include = ['dns', 'viewdns', 'otx']
        for module_name in always_include:
            if module_name in self.recon_modules:
                modules_to_run[module_name] = self.recon_modules[module_name]
        
        # Include API-based modules if available and not in fast mode
        if not self.scan_config.fast_mode:
            api_modules = ['shodan', 'censys', 'virustotal', 'securitytrails']
            for module_name in api_modules:
                if module_name in self.recon_modules:
                    modules_to_run[module_name] = self.recon_modules[module_name]
        
        # Always include favicon for deep scans
        if self.scan_config.deep_scan and 'favicon' in self.recon_modules:
            modules_to_run['favicon'] = self.recon_modules['favicon']
        
        return modules_to_run
    
    async def _run_single_module(self, module_name: str, module: Any, domain: str) -> List[IPCandidate]:
        """Run a single reconnaissance module"""
        try:
            if not module.is_available():
                return []
            
            async with module:
                candidates = await module.search(domain)
                return candidates
        
        except Exception as e:
            # Log error and return empty list
            return []
    
    def _deduplicate_candidates(self, candidates: List[IPCandidate]) -> List[IPCandidate]:
        """Remove duplicate IP candidates, keeping the one with highest confidence"""
        ip_to_candidate = {}
        
        for candidate in candidates:
            ip = candidate.ip
            
            if ip not in ip_to_candidate:
                ip_to_candidate[ip] = candidate
            else:
                # Keep the one with higher confidence
                existing = ip_to_candidate[ip]
                if candidate.confidence > existing.confidence:
                    ip_to_candidate[ip] = candidate
                elif candidate.confidence == existing.confidence:
                    # Merge sources if same confidence
                    existing.metadata = existing.metadata or {}
                    candidate.metadata = candidate.metadata or {}
                    
                    sources = existing.metadata.get('sources', [existing.source])
                    if candidate.source not in sources:
                        sources.append(candidate.source)
                    
                    existing.metadata['sources'] = sources
                    existing.source = f"{existing.source}+{candidate.source}"
        
        return list(ip_to_candidate.values())
    
    async def quick_scan(self, domain: str) -> ScanResult:
        """Perform a quick scan with minimal modules"""
        original_config = self.scan_config
        self.scan_config = ScanConfig(
            fast_mode=True,
            confidence_threshold=70,
            verify_origins=True,
            timeout=15
        )
        
        try:
            result = await self.scan(domain)
            return result
        finally:
            self.scan_config = original_config
    
    async def deep_scan(self, domain: str) -> ScanResult:
        """Perform a comprehensive deep scan"""
        original_config = self.scan_config
        self.scan_config = ScanConfig(
            deep_scan=True,
            confidence_threshold=50,
            verify_origins=True,
            timeout=45,
            max_concurrent=15
        )
        
        try:
            result = await self.scan(domain)
            return result
        finally:
            self.scan_config = original_config
    
    async def passive_only_scan(self, domain: str) -> ScanResult:
        """Perform passive reconnaissance only"""
        original_config = self.scan_config
        self.scan_config = ScanConfig(
            passive_only=True,
            verify_origins=False,
            confidence_threshold=40
        )
        
        try:
            result = await self.scan(domain)
            return result
        finally:
            self.scan_config = original_config