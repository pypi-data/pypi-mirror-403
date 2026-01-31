"""
ViewDNS reconnaissance module for OriginX
"""

import re
from typing import List
from .base import BaseReconModule
from ..utils.models import IPCandidate
from ..utils.helpers import is_valid_ip, is_private_ip, extract_ips_from_text

class ViewDNSRecon(BaseReconModule):
    """ViewDNS-based reconnaissance (web scraping)"""
    
    def is_available(self) -> bool:
        """ViewDNS is always available (no API key required)"""
        return True
    
    async def search(self, domain: str) -> List[IPCandidate]:
        """Search ViewDNS for domain-related IPs"""
        if not self.session:
            return []
        
        candidates = []
        
        # IP History
        ip_history = await self._get_ip_history(domain)
        candidates.extend(ip_history)
        
        # Reverse IP lookup on current IPs
        reverse_ip = await self._get_reverse_ip(domain)
        candidates.extend(reverse_ip)
        
        return candidates
    
    async def _get_ip_history(self, domain: str) -> List[IPCandidate]:
        """Get IP history from ViewDNS"""
        candidates = []
        
        try:
            url = "https://viewdns.info/iphistory/"
            params = {'domain': domain}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Parse the HTML response for IP addresses
                    # Look for table rows with IP addresses
                    ip_pattern = r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>'
                    matches = re.findall(ip_pattern, content)
                    
                    for ip in matches:
                        if is_valid_ip(ip) and not is_private_ip(ip):
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=55,
                                metadata={
                                    'search_type': 'ip_history',
                                    'source': 'viewdns'
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates
    
    async def _get_reverse_ip(self, domain: str) -> List[IPCandidate]:
        """Get reverse IP information from ViewDNS"""
        candidates = []
        
        try:
            # First resolve domain to get current IP
            import socket
            try:
                current_ip = socket.gethostbyname(domain)
                if is_valid_ip(current_ip) and not is_private_ip(current_ip):
                    # Now do reverse IP lookup
                    url = "https://viewdns.info/reverseip/"
                    params = {'host': current_ip, 't': '1'}
                    
                    async with self.session.get(url, params=params) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Extract domains from the response
                            domain_pattern = r'<td>([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})</td>'
                            domains = re.findall(domain_pattern, content)
                            
                            # The current IP hosts these domains
                            if domains:
                                candidates.append(self.create_candidate(
                                    ip=current_ip,
                                    confidence=70,
                                    metadata={
                                        'search_type': 'reverse_ip',
                                        'hosted_domains': domains[:10],  # Limit to 10
                                        'source': 'viewdns'
                                    }
                                ))
            except socket.gaierror:
                pass
        
        except Exception:
            pass
        
        return candidates