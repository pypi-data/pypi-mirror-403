"""
Censys reconnaissance module for OriginX
"""

import base64
from typing import List
from .base import BaseReconModule
from ..utils.models import IPCandidate
from ..utils.helpers import is_valid_ip, is_private_ip

class CensysRecon(BaseReconModule):
    """Censys-based reconnaissance"""
    
    def is_available(self) -> bool:
        """Check if Censys API credentials are available"""
        return bool(self.config.censys_id and self.config.censys_secret)
    
    def get_headers(self) -> dict:
        """Get headers with Censys authentication"""
        headers = super().get_headers()
        
        if self.config.censys_id and self.config.censys_secret:
            credentials = f"{self.config.censys_id}:{self.config.censys_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers['Authorization'] = f'Basic {encoded_credentials}'
        
        return headers
    
    async def search(self, domain: str) -> List[IPCandidate]:
        """Search Censys for domain-related IPs"""
        if not self.session or not self.is_available():
            return []
        
        candidates = []
        
        # Search by hostname
        hostname_results = await self._search_by_hostname(domain)
        candidates.extend(hostname_results)
        
        # Search by certificate
        cert_results = await self._search_by_certificate(domain)
        candidates.extend(cert_results)
        
        return candidates
    
    async def _search_by_hostname(self, domain: str) -> List[IPCandidate]:
        """Search Censys by hostname"""
        candidates = []
        
        try:
            url = "https://search.censys.io/api/v2/hosts/search"
            params = {
                'q': f'services.http.request.get.headers.host: {domain}',
                'per_page': 100
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for result in data.get('result', {}).get('hits', []):
                        ip = result.get('ip')
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            services = result.get('services', [])
                            
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=75,
                                metadata={
                                    'search_type': 'hostname',
                                    'services': [s.get('service_name') for s in services],
                                    'ports': [s.get('port') for s in services],
                                    'autonomous_system': result.get('autonomous_system', {})
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates
    
    async def _search_by_certificate(self, domain: str) -> List[IPCandidate]:
        """Search Censys by SSL certificate"""
        candidates = []
        
        try:
            url = "https://search.censys.io/api/v2/hosts/search"
            params = {
                'q': f'services.tls.certificates.leaf_data.subject.common_name: {domain}',
                'per_page': 100
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for result in data.get('result', {}).get('hits', []):
                        ip = result.get('ip')
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=80,
                                metadata={
                                    'search_type': 'certificate',
                                    'autonomous_system': result.get('autonomous_system', {}),
                                    'location': result.get('location', {})
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates
    
    async def search_by_favicon_hash(self, favicon_hash: str) -> List[IPCandidate]:
        """Search Censys by favicon hash (if supported)"""
        # Censys doesn't have direct favicon hash search like Shodan
        # This is a placeholder for potential future functionality
        return []