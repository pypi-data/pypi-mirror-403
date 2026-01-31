"""
DNS reconnaissance module for OriginX
"""

import dns.resolver
import dns.reversename
import re
from typing import List, Set
from .base import BaseReconModule
from ..utils.models import IPCandidate
from ..utils.helpers import is_valid_ip, is_private_ip, extract_ips_from_text

class DNSRecon(BaseReconModule):
    """DNS-based reconnaissance"""
    
    def is_available(self) -> bool:
        """DNS is always available"""
        return True
    
    async def search(self, domain: str) -> List[IPCandidate]:
        """Search for IPs using DNS techniques"""
        candidates = []
        
        # A records
        a_records = await self._get_a_records(domain)
        candidates.extend(a_records)
        
        # SPF records
        spf_ips = await self._get_spf_ips(domain)
        candidates.extend(spf_ips)
        
        # Subdomain enumeration
        subdomain_ips = await self._enumerate_subdomains(domain)
        candidates.extend(subdomain_ips)
        
        return candidates
    
    async def _get_a_records(self, domain: str) -> List[IPCandidate]:
        """Get A records for domain"""
        candidates = []
        
        try:
            answers = dns.resolver.resolve(domain, 'A')
            for answer in answers:
                ip = str(answer)
                if is_valid_ip(ip) and not is_private_ip(ip):
                    candidates.append(self.create_candidate(
                        ip=ip,
                        confidence=60,
                        metadata={'record_type': 'A', 'domain': domain}
                    ))
        except Exception:
            pass
        
        return candidates
    
    async def _get_spf_ips(self, domain: str) -> List[IPCandidate]:
        """Extract IPs from SPF records"""
        candidates = []
        
        try:
            answers = dns.resolver.resolve(domain, 'TXT')
            for answer in answers:
                txt_record = str(answer).strip('"')
                
                if txt_record.startswith('v=spf1'):
                    # Extract ip4 mechanisms
                    ip4_pattern = r'ip4:([0-9.]+(?:/\d+)?)'
                    matches = re.findall(ip4_pattern, txt_record)
                    
                    for match in matches:
                        ip = match.split('/')[0]  # Remove CIDR notation
                        if is_valid_ip(ip) and not is_private_ip(ip):
                            candidates.append(self.create_candidate(
                                ip=ip,
                                confidence=70,
                                metadata={'record_type': 'SPF', 'spf_record': txt_record}
                            ))
                    
                    # Extract include mechanisms and resolve them
                    include_pattern = r'include:([^\s]+)'
                    includes = re.findall(include_pattern, txt_record)
                    
                    for include_domain in includes:
                        try:
                            include_answers = dns.resolver.resolve(include_domain, 'A')
                            for include_answer in include_answers:
                                ip = str(include_answer)
                                if is_valid_ip(ip) and not is_private_ip(ip):
                                    candidates.append(self.create_candidate(
                                        ip=ip,
                                        confidence=50,
                                        metadata={
                                            'record_type': 'SPF_INCLUDE',
                                            'include_domain': include_domain
                                        }
                                    ))
                        except Exception:
                            continue
        
        except Exception:
            pass
        
        return candidates
    
    async def _enumerate_subdomains(self, domain: str) -> List[IPCandidate]:
        """Enumerate common subdomains and get their IPs"""
        candidates = []
        
        # Common subdomains that might reveal origin
        subdomains = [
            'origin', 'direct', 'backend', 'api', 'admin', 'staging',
            'dev', 'test', 'mail', 'ftp', 'cpanel', 'whm', 'server',
            'host', 'ns1', 'ns2', 'mx', 'www'
        ]
        
        for subdomain in subdomains:
            full_domain = f"{subdomain}.{domain}"
            try:
                answers = dns.resolver.resolve(full_domain, 'A')
                for answer in answers:
                    ip = str(answer)
                    if is_valid_ip(ip) and not is_private_ip(ip):
                        candidates.append(self.create_candidate(
                            ip=ip,
                            confidence=40,
                            metadata={
                                'record_type': 'SUBDOMAIN',
                                'subdomain': full_domain
                            }
                        ))
            except Exception:
                continue
        
        return candidates