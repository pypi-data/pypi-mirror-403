"""
Favicon hash reconnaissance module for OriginX
"""

import asyncio
from typing import List, Optional
from .base import BaseReconModule
from .shodan import ShodanRecon
from .censys import CensysRecon
from ..utils.models import IPCandidate
from ..utils.helpers import calculate_favicon_hash

class FaviconRecon(BaseReconModule):
    """Favicon hash-based reconnaissance"""
    
    def __init__(self, config, timeout=30):
        super().__init__(config, timeout)
        self.shodan_recon = ShodanRecon(config, timeout)
        self.censys_recon = CensysRecon(config, timeout)
    
    def is_available(self) -> bool:
        """Favicon recon is always available but more effective with API keys"""
        return True
    
    async def search(self, domain: str) -> List[IPCandidate]:
        """Search for IPs using favicon hash correlation"""
        candidates = []
        
        # Get favicon hash
        favicon_hash = await self._get_favicon_hash(domain)
        if not favicon_hash:
            return candidates
        
        # Search using the hash
        hash_results = await self._search_by_hash(favicon_hash)
        candidates.extend(hash_results)
        
        return candidates
    
    async def _get_favicon_hash(self, domain: str) -> Optional[str]:
        """Get favicon and calculate its hash"""
        if not self.session:
            return None
        
        favicon_urls = [
            f"https://{domain}/favicon.ico",
            f"http://{domain}/favicon.ico",
            f"https://www.{domain}/favicon.ico",
            f"http://www.{domain}/favicon.ico"
        ]
        
        for url in favicon_urls:
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        favicon_data = await response.read()
                        if len(favicon_data) > 0:
                            return calculate_favicon_hash(favicon_data)
            except Exception:
                continue
        
        return None
    
    async def _search_by_hash(self, favicon_hash: str) -> List[IPCandidate]:
        """Search for IPs using favicon hash"""
        candidates = []
        
        # Use Shodan if available
        if self.shodan_recon.is_available():
            async with self.shodan_recon:
                shodan_results = await self.shodan_recon.search_by_favicon_hash(favicon_hash)
                for result in shodan_results:
                    result.source = 'favicon_shodan'
                    result.confidence = min(result.confidence, 90)
                candidates.extend(shodan_results)
        
        # Use Censys if available (limited support)
        if self.censys_recon.is_available():
            async with self.censys_recon:
                censys_results = await self.censys_recon.search_by_favicon_hash(favicon_hash)
                for result in censys_results:
                    result.source = 'favicon_censys'
                candidates.extend(censys_results)
        
        # Add favicon hash to metadata
        for candidate in candidates:
            if candidate.metadata is None:
                candidate.metadata = {}
            candidate.metadata['favicon_hash'] = favicon_hash
        
        return candidates