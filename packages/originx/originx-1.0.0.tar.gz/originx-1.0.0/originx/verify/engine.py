"""
Origin verification engine for OriginX
"""

import asyncio
import aiohttp
import ssl
import time
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlparse
import socket

from ..utils.models import VerificationResult, IPCandidate
from ..utils.helpers import calculate_similarity, is_valid_ip

class OriginVerifier:
    """Engine for verifying potential origin servers"""
    
    def __init__(self, timeout: int = 15, max_concurrent: int = 10):
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=20,
            limit_per_host=10,
            ssl=False  # Disable SSL verification for testing
        )
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def verify_candidates(
        self, 
        domain: str, 
        candidates: List[IPCandidate],
        reference_response: Optional[str] = None
    ) -> List[VerificationResult]:
        """Verify multiple IP candidates"""
        
        if not self.session:
            return []
        
        # Get reference response if not provided
        if reference_response is None:
            reference_response = await self._get_reference_response(domain)
        
        # Verify candidates concurrently
        tasks = []
        for candidate in candidates:
            task = self._verify_single_candidate(domain, candidate, reference_response)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        verified_results = []
        for result in results:
            if isinstance(result, VerificationResult):
                verified_results.append(result)
        
        return verified_results
    
    async def _verify_single_candidate(
        self, 
        domain: str, 
        candidate: IPCandidate,
        reference_response: Optional[str]
    ) -> VerificationResult:
        """Verify a single IP candidate"""
        
        async with self.semaphore:
            start_time = time.time()
            
            result = VerificationResult(
                ip=candidate.ip,
                is_origin=False,
                confidence_score=0
            )
            
            try:
                # Test direct IP connection
                direct_test = await self._test_direct_connection(candidate.ip, domain)
                result.response_code = direct_test.get('status_code')
                result.response_time = time.time() - start_time
                
                if not direct_test.get('success'):
                    result.error = direct_test.get('error', 'Connection failed')
                    return result
                
                # Test with Host header override
                host_test = await self._test_host_header_override(candidate.ip, domain)
                
                # Test SSL certificate match
                cert_match = await self._test_certificate_match(candidate.ip, domain)
                result.cert_match = cert_match
                
                # Calculate content similarity
                if reference_response and host_test.get('content'):
                    similarity = calculate_similarity(reference_response, host_test['content'])
                    result.content_similarity = similarity
                
                # Check for WAF detection
                waf_detected = self._detect_waf_response(host_test.get('content', ''))
                result.waf_detected = waf_detected
                
                # Calculate confidence score
                confidence = self._calculate_confidence(
                    direct_test=direct_test,
                    host_test=host_test,
                    cert_match=cert_match,
                    content_similarity=result.content_similarity,
                    waf_detected=waf_detected,
                    candidate=candidate
                )
                
                result.confidence_score = confidence
                result.is_origin = confidence >= 70  # Threshold for considering as origin
                
                # Add metadata
                result.metadata = {
                    'direct_connection': direct_test.get('success', False),
                    'host_header_works': host_test.get('success', False),
                    'server_header': host_test.get('headers', {}).get('server'),
                    'candidate_source': candidate.source,
                    'candidate_confidence': candidate.confidence
                }
                
            except Exception as e:
                result.error = str(e)
            
            return result
    
    async def _get_reference_response(self, domain: str) -> Optional[str]:
        """Get reference response from the original domain"""
        try:
            url = f"https://{domain}/"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
        except Exception:
            try:
                url = f"http://{domain}/"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
            except Exception:
                pass
        
        return None
    
    async def _test_direct_connection(self, ip: str, domain: str) -> Dict[str, Any]:
        """Test direct connection to IP"""
        result = {'success': False}
        
        for scheme in ['https', 'http']:
            try:
                url = f"{scheme}://{ip}/"
                async with self.session.get(url) as response:
                    result.update({
                        'success': True,
                        'status_code': response.status,
                        'headers': dict(response.headers),
                        'content': await response.text()
                    })
                    return result
            except Exception as e:
                result['error'] = str(e)
                continue
        
        return result
    
    async def _test_host_header_override(self, ip: str, domain: str) -> Dict[str, Any]:
        """Test connection with Host header override"""
        result = {'success': False}
        
        headers = {'Host': domain}
        
        for scheme in ['https', 'http']:
            try:
                url = f"{scheme}://{ip}/"
                async with self.session.get(url, headers=headers) as response:
                    result.update({
                        'success': True,
                        'status_code': response.status,
                        'headers': dict(response.headers),
                        'content': await response.text()
                    })
                    return result
            except Exception as e:
                result['error'] = str(e)
                continue
        
        return result
    
    async def _test_certificate_match(self, ip: str, domain: str) -> bool:
        """Test if SSL certificate matches the domain"""
        try:
            # Create SSL context that doesn't verify certificates
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((ip, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    if cert:
                        # Check subject common name
                        subject = dict(x[0] for x in cert.get('subject', []))
                        common_name = subject.get('commonName', '')
                        
                        if domain in common_name or common_name in domain:
                            return True
                        
                        # Check subject alternative names
                        san_list = cert.get('subjectAltName', [])
                        for san_type, san_value in san_list:
                            if san_type == 'DNS' and (domain in san_value or san_value in domain):
                                return True
        
        except Exception:
            pass
        
        return False
    
    def _detect_waf_response(self, content: str) -> bool:
        """Detect WAF in response content"""
        waf_signatures = [
            'cloudflare',
            'incapsula',
            'sucuri',
            'blocked by administrator',
            'access denied',
            'security policy',
            'firewall',
            'mod_security'
        ]
        
        content_lower = content.lower()
        return any(sig in content_lower for sig in waf_signatures)
    
    def _calculate_confidence(
        self,
        direct_test: Dict[str, Any],
        host_test: Dict[str, Any],
        cert_match: bool,
        content_similarity: float,
        waf_detected: bool,
        candidate: IPCandidate
    ) -> int:
        """Calculate confidence score for origin verification"""
        
        confidence = 0
        
        # Base confidence from candidate source
        confidence += min(candidate.confidence, 40)
        
        # Direct connection bonus
        if direct_test.get('success'):
            confidence += 20
        
        # Host header override bonus
        if host_test.get('success'):
            confidence += 25
        
        # Certificate match bonus
        if cert_match:
            confidence += 30
        
        # Content similarity bonus
        if content_similarity > 0.8:
            confidence += 20
        elif content_similarity > 0.6:
            confidence += 15
        elif content_similarity > 0.4:
            confidence += 10
        
        # WAF detection penalty
        if waf_detected:
            confidence -= 15
        
        # HTTP status code bonus
        if host_test.get('status_code') == 200:
            confidence += 10
        elif host_test.get('status_code') in [301, 302, 403]:
            confidence += 5
        
        # Server header consistency
        direct_server = direct_test.get('headers', {}).get('server', '')
        host_server = host_test.get('headers', {}).get('server', '')
        if direct_server and host_server and direct_server == host_server:
            confidence += 10
        
        return min(max(confidence, 0), 100)  # Clamp between 0-100