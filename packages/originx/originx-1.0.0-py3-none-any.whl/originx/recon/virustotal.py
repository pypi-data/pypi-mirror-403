"""
VirusTotal reconnaissance module for OriginX
"""

from typing import List
from .base import BaseReconModule
from ..utils.models import IPCandidate
from ..utils.helpers import is_valid_ip, is_private_ip

class VirusTotalRecon(BaseReconModule):
    """VirusTotal-based reconnaissance"""
    
    def is_available(self) -> bool:
        """Check if VirusTotal API key is available"""
        return bool(self.config.virustotal_key)
    
    def get_headers(self) -> dict:
        """Get headers with VirusTotal API key"""
        headers = super().get_headers()
        if self.config.virustotal_key:
            headers['x-apikey'] = self.config.virustotal_key
        return headers
    
    async def search(self, domain: str) -> List[IPCandidate]:
        """Search VirusTotal for domain-related IPs"""
        if not self.session or not self.config.virustotal_key:
            return []
        
        candidates = []
        
        # Get domain information
        domain_info = await self._get_domain_info(domain)
        candidates.extend(domain_info)
        
        # Get passive DNS data
        passive_dns = await self._get_passive_dns(domain)
        candidates.extend(passive_dns)
        
        return candidates
    
    async def _get_domain_info(self, domain: str) -> List[IPCandidate]:
        """Get domain information from VirusTotal"""
        candidates = []
        
        try:
            url = f"https://www.virustotal.com/vtapi/v2/domain/report"
            params = {
                'apikey': self.config.virustotal_key,
                'domain': domain
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Current resolutions
                    resolutions = data.get('resolutions', [])
                    for resolution in resolutions[:20]:  # Limit to recent 20
                        ip = resolution.get('ip_address')
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=70,
                                metadata={
                                    'search_type': 'domain_resolution',
                                    'last_resolved': resolution.get('last_resolved'),
                                    'source': 'virustotal'
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates
    
    async def _get_passive_dns(self, domain: str) -> List[IPCandidate]:
        """Get passive DNS data from VirusTotal"""
        candidates = []
        
        try:
            # Using v3 API for passive DNS
            url = f"https://www.virustotal.com/api/v3/domains/{domain}/resolutions"
            params = {
                'limit': 40
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for resolution in data.get('data', []):
                        attributes = resolution.get('attributes', {})
                        ip = attributes.get('ip_address')
                        
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=65,
                                metadata={
                                    'search_type': 'passive_dns',
                                    'date': attributes.get('date'),
                                    'resolver': attributes.get('resolver'),
                                    'source': 'virustotal_v3'
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates