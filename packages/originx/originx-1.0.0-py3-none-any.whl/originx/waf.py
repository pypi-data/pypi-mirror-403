"""
WAF Detection Engine for OriginX
"""

import asyncio
import aiohttp
import re
from typing import Optional, List, Dict, Any
import io
import sys
from contextlib import redirect_stdout, redirect_stderr

from .utils.models import WAFInfo
from .utils.helpers import normalize_domain

class WAFDetector:
    """WAF detection using multiple techniques"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5, ssl=False)
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
    
    async def detect_waf(self, domain: str) -> WAFInfo:
        """Detect WAF using multiple methods"""
        domain = normalize_domain(domain)
        
        # Try wafw00f first
        wafw00f_result = await self._detect_with_wafw00f(domain)
        if wafw00f_result.detected:
            return wafw00f_result
        
        # Fallback to manual detection
        manual_result = await self._detect_manual(domain)
        
        return manual_result
    
    async def _detect_with_wafw00f(self, domain: str) -> WAFInfo:
        """Use wafw00f for WAF detection"""
        try:
            # Try to import wafw00f dynamically
            try:
                from wafw00f.manager import load_plugins
                # wafw00f is available but complex to integrate
                # For now, return not detected and rely on manual detection
                return WAFInfo(detected=False)
            except ImportError:
                # wafw00f not available
                return WAFInfo(detected=False)
                    
        except Exception as e:
            return WAFInfo(detected=False)
    
    async def _detect_manual(self, domain: str) -> WAFInfo:
        """Manual WAF detection using HTTP headers and responses"""
        if not self.session:
            return WAFInfo(detected=False)
        
        evidence = []
        detected_waf = None
        confidence = 0
        
        try:
            # Test multiple URLs
            test_paths = [
                '/',
                '/?test=<script>alert(1)</script>',
                '/admin',
                '/.env'
            ]
            
            for path in test_paths:
                url = f"https://{domain}{path}"
                try:
                    async with self.session.get(url, allow_redirects=False) as response:
                        headers = dict(response.headers)
                        content = await response.text()
                        
                        # Check headers for WAF signatures
                        waf_info = self._analyze_headers(headers)
                        if waf_info:
                            detected_waf = waf_info['provider']
                            evidence.extend(waf_info['evidence'])
                            confidence = max(confidence, waf_info['confidence'])
                        
                        # Check response content
                        content_info = self._analyze_content(content)
                        if content_info:
                            detected_waf = detected_waf or content_info['provider']
                            evidence.extend(content_info['evidence'])
                            confidence = max(confidence, content_info['confidence'])
                        
                        if detected_waf:
                            break
                            
                except Exception:
                    continue
            
            # Try HTTP as fallback
            if not detected_waf:
                try:
                    url = f"http://{domain}/"
                    async with self.session.get(url, allow_redirects=False) as response:
                        headers = dict(response.headers)
                        waf_info = self._analyze_headers(headers)
                        if waf_info:
                            detected_waf = waf_info['provider']
                            evidence.extend(waf_info['evidence'])
                            confidence = waf_info['confidence']
                except Exception:
                    pass
        
        except Exception:
            pass
        
        return WAFInfo(
            detected=bool(detected_waf),
            provider=detected_waf,
            confidence=confidence,
            evidence=list(set(evidence))
        )
    
    def _analyze_headers(self, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Analyze HTTP headers for WAF signatures"""
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        # Cloudflare
        if any(key in headers_lower for key in ['cf-ray', 'cf-cache-status', '__cfduid']):
            return {
                'provider': 'Cloudflare',
                'confidence': 95,
                'evidence': ['CF-Ray header', 'Cloudflare headers detected']
            }
        
        # AWS CloudFront
        if 'x-amz-cf-id' in headers_lower or 'x-amz-cf-pop' in headers_lower:
            return {
                'provider': 'AWS CloudFront',
                'confidence': 90,
                'evidence': ['X-Amz-Cf-Id header']
            }
        
        # Akamai
        if any(key.startswith('x-akamai') for key in headers_lower.keys()):
            return {
                'provider': 'Akamai',
                'confidence': 90,
                'evidence': ['Akamai headers detected']
            }
        
        # Fastly
        if 'fastly-debug-digest' in headers_lower or 'x-served-by' in headers_lower:
            if 'fastly' in headers_lower.get('x-served-by', '').lower():
                return {
                    'provider': 'Fastly',
                    'confidence': 85,
                    'evidence': ['Fastly headers detected']
                }
        
        # Incapsula
        if 'x-iinfo' in headers_lower or 'incap_ses' in str(headers_lower.get('set-cookie', '')):
            return {
                'provider': 'Incapsula',
                'confidence': 90,
                'evidence': ['Incapsula headers detected']
            }
        
        # Sucuri
        if 'x-sucuri-id' in headers_lower:
            return {
                'provider': 'Sucuri',
                'confidence': 95,
                'evidence': ['X-Sucuri-ID header']
            }
        
        # ModSecurity
        if 'mod_security' in headers_lower.get('server', '').lower():
            return {
                'provider': 'ModSecurity',
                'confidence': 80,
                'evidence': ['ModSecurity in Server header']
            }
        
        return None
    
    def _analyze_content(self, content: str) -> Optional[Dict[str, Any]]:
        """Analyze response content for WAF signatures"""
        content_lower = content.lower()
        
        # Cloudflare
        if any(phrase in content_lower for phrase in [
            'cloudflare ray id',
            'cloudflare',
            'attention required! | cloudflare'
        ]):
            return {
                'provider': 'Cloudflare',
                'confidence': 85,
                'evidence': ['Cloudflare error page detected']
            }
        
        # Incapsula
        if 'incapsula' in content_lower or 'incap_ses' in content_lower:
            return {
                'provider': 'Incapsula',
                'confidence': 80,
                'evidence': ['Incapsula content detected']
            }
        
        # Sucuri
        if 'sucuri' in content_lower:
            return {
                'provider': 'Sucuri',
                'confidence': 75,
                'evidence': ['Sucuri content detected']
            }
        
        return None