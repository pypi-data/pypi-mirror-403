"""
AlienVault OTX reconnaissance module for OriginX
"""

from typing import List
from .base import BaseReconModule
from ..utils.models import IPCandidate
from ..utils.helpers import is_valid_ip, is_private_ip

class OTXRecon(BaseReconModule):
    """AlienVault OTX-based reconnaissance"""
    
    def is_available(self) -> bool:
        """OTX is available without API key (with rate limits)"""
        return True
    
    async def search(self, domain: str) -> List[IPCandidate]:
        """Search OTX for domain-related IPs"""
        if not self.session:
            return []
        
        candidates = []
        
        # Get passive DNS data
        passive_dns = await self._get_passive_dns(domain)
        candidates.extend(passive_dns)
        
        return candidates
    
    async def _get_passive_dns(self, domain: str) -> List[IPCandidate]:
        """Get passive DNS data from OTX"""
        candidates = []
        
        try:
            url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    passive_dns_records = data.get('passive_dns', [])
                    for record in passive_dns_records[:50]:  # Limit to 50 records
                        ip = record.get('address')
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=60,
                                metadata={
                                    'search_type': 'passive_dns',
                                    'first_seen': record.get('first'),
                                    'last_seen': record.get('last'),
                                    'hostname': record.get('hostname'),
                                    'source': 'otx'
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates