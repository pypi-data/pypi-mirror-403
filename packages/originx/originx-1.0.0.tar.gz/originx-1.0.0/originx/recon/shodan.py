"""
Shodan reconnaissance module for OriginX
"""

import json
from typing import List, Dict, Any
from .base import BaseReconModule
from ..utils.models import IPCandidate
from ..utils.helpers import is_valid_ip, is_private_ip

class ShodanRecon(BaseReconModule):
    """Shodan-based reconnaissance"""
    
    def is_available(self) -> bool:
        """Check if Shodan API key is available"""
        return bool(self.config.shodan_key)
    
    async def search(self, domain: str) -> List[IPCandidate]:
        """Search Shodan for domain-related IPs"""
        if not self.session or not self.config.shodan_key:
            return []
        
        candidates = []
        
        # Search by hostname
        hostname_results = await self._search_by_hostname(domain)
        candidates.extend(hostname_results)
        
        # Search by SSL certificate
        ssl_results = await self._search_by_ssl(domain)
        candidates.extend(ssl_results)
        
        # Search by HTTP title/content
        http_results = await self._search_by_http(domain)
        candidates.extend(http_results)
        
        return candidates
    
    async def _search_by_hostname(self, domain: str) -> List[IPCandidate]:
        """Search Shodan by hostname"""
        candidates = []
        
        try:
            url = f"https://api.shodan.io/shodan/host/search"
            params = {
                'key': self.config.shodan_key,
                'query': f'hostname:{domain}',
                'facets': 'ip:100'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for match in data.get('matches', []):
                        ip = match.get('ip_str')
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=80,
                                port=match.get('port'),
                                service=match.get('product'),
                                metadata={
                                    'search_type': 'hostname',
                                    'hostnames': match.get('hostnames', []),
                                    'org': match.get('org'),
                                    'isp': match.get('isp'),
                                    'country': match.get('location', {}).get('country_name')
                                }
                            ))
        
        except Exception as e:
            pass
        
        return candidates
    
    async def _search_by_ssl(self, domain: str) -> List[IPCandidate]:
        """Search Shodan by SSL certificate"""
        candidates = []
        
        try:
            url = f"https://api.shodan.io/shodan/host/search"
            params = {
                'key': self.config.shodan_key,
                'query': f'ssl.cert.subject.cn:{domain}',
                'facets': 'ip:100'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for match in data.get('matches', []):
                        ip = match.get('ip_str')
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            ssl_info = match.get('ssl', {})
                            cert_info = ssl_info.get('cert', {})
                            
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=85,
                                port=match.get('port'),
                                service=match.get('product'),
                                metadata={
                                    'search_type': 'ssl_cert',
                                    'cert_subject': cert_info.get('subject', {}),
                                    'cert_issuer': cert_info.get('issuer', {}),
                                    'org': match.get('org'),
                                    'isp': match.get('isp')
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates
    
    async def _search_by_http(self, domain: str) -> List[IPCandidate]:
        """Search Shodan by HTTP content"""
        candidates = []
        
        try:
            # Search by HTTP title
            url = f"https://api.shodan.io/shodan/host/search"
            params = {
                'key': self.config.shodan_key,
                'query': f'http.title:"{domain}"',
                'facets': 'ip:50'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for match in data.get('matches', []):
                        ip = match.get('ip_str')
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            http_info = match.get('http', {})
                            
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=60,
                                port=match.get('port'),
                                service=match.get('product'),
                                metadata={
                                    'search_type': 'http_title',
                                    'http_title': http_info.get('title'),
                                    'server': http_info.get('server'),
                                    'org': match.get('org')
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates
    
    async def search_by_favicon_hash(self, favicon_hash: str) -> List[IPCandidate]:
        """Search Shodan by favicon hash"""
        candidates = []
        
        if not self.session or not self.config.shodan_key:
            return candidates
        
        try:
            url = f"https://api.shodan.io/shodan/host/search"
            params = {
                'key': self.config.shodan_key,
                'query': f'http.favicon.hash:{favicon_hash}',
                'facets': 'ip:100'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for match in data.get('matches', []):
                        ip = match.get('ip_str')
                        if ip and is_valid_ip(ip) and not is_private_ip(ip):
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=90,
                                port=match.get('port'),
                                service=match.get('product'),
                                metadata={
                                    'search_type': 'favicon_hash',
                                    'favicon_hash': favicon_hash,
                                    'org': match.get('org'),
                                    'hostnames': match.get('hostnames', [])
                                }
                            ))
        
        except Exception:
            pass
        
        return candidates