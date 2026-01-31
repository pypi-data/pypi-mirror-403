"""
SecurityTrails reconnaissance module for OriginX
"""

from typing import List
from .base import BaseReconModule
from ..utils.models import IPCandidate
from ..utils.helpers import is_valid_ip, is_private_ip

class SecurityTrailsRecon(BaseReconModule):
    """SecurityTrails-based reconnaissance"""
    
    def is_available(self) -> bool:
        """Check if SecurityTrails API key is available"""
        return bool(self.config.securitytrails_key)
    
    def get_headers(self) -> dict:
        """Get headers with SecurityTrails API key"""
        headers = super().get_headers()
        if self.config.securitytrails_key:
            headers['APIKEY'] = self.config.securitytrails_key
        return headers
    
    async def search(self, domain: str) -> List[IPCandidate]:
        """Search SecurityTrails for domain-related IPs"""
        if not self.session or not self.config.securitytrails_key:
            return []
        
        candidates = []
        
        # Get current DNS records
        current_dns = await self._get_current_dns(domain)
        candidates.extend(current_dns)
        
        # Get historical DNS data
        historical_dns = await self._get_historical_dns(domain)
        candidates.extend(historical_dns)
        
        # Get subdomains
        subdomains = await self._get_subdomains(domain)
        candidates.extend(subdomains)
        
        return candidates
    
    async def _get_current_dns(self, domain: str) -> List[IPCandidate]:
        """Get current DNS records from SecurityTrails"""
        candidates = []
        
        try:
            url = f"https://api.securitytrails.com/v1/domain/{domain}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # A records
                    a_records = data.get('current_dns', {}).get('a', {}).get('values', [])
                    for record in a_records:
                        ip = record.get('ip')
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=75,
                                metadata={
                                    'search_type': 'current_dns',
                                    'record_type': 'A',
                                    'first_seen': record.get('first_seen'),
                                    'source': 'securitytrails'
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates
    
    async def _get_historical_dns(self, domain: str) -> List[IPCandidate]:
        """Get historical DNS data from SecurityTrails"""
        candidates = []
        
        try:
            url = f"https://api.securitytrails.com/v1/history/{domain}/dns/a"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    records = data.get('records', [])
                    for record in records[:30]:  # Limit to 30 most recent
                        values = record.get('values', [])
                        for value in values:
                            ip = value.get('ip')
                            if ip and is_valid_ip(ip) and not is_private_ip(ip):
                                candidates.append(self.create_candidate(
                                    ip=ip,
                                    confidence=60,
                                    metadata={
                                        'search_type': 'historical_dns',
                                        'first_seen': record.get('first_seen'),
                                        'last_seen': record.get('last_seen'),
                                        'source': 'securitytrails'
                                    }
                                ))
        
        except Exception:
            pass
        
        return candidates
    
    async def _get_subdomains(self, domain: str) -> List[IPCandidate]:
        """Get subdomain IPs from SecurityTrails"""
        candidates = []
        
        try:
            url = f"https://api.securitytrails.com/v1/domain/{domain}/subdomains"
            params = {'children_only': 'false'}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    subdomains = data.get('subdomains', [])[:50]  # Limit to 50
                    
                    for subdomain in subdomains:
                        full_domain = f"{subdomain}.{domain}"
                        
                        # Get DNS records for each subdomain
                        subdomain_ips = await self._get_subdomain_ips(full_domain)
                        candidates.extend(subdomain_ips)
        
        except Exception:
            pass
        
        return candidates
    
    async def _get_subdomain_ips(self, subdomain: str) -> List[IPCandidate]:
        """Get IPs for a specific subdomain"""
        candidates = []
        
        try:
            url = f"https://api.securitytrails.com/v1/domain/{subdomain}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    a_records = data.get('current_dns', {}).get('a', {}).get('values', [])
                    for record in a_records:
                        ip = record.get('ip')
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=50,
                                metadata={
                                    'search_type': 'subdomain',
                                    'subdomain': subdomain,
                                    'source': 'securitytrails'
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates