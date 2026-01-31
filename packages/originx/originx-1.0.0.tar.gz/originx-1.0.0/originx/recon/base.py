"""
Base reconnaissance module for OriginX
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..utils.models import IPCandidate
from ..utils.config import APIConfig

class BaseReconModule(ABC):
    """Base class for reconnaissance modules"""
    
    def __init__(self, config: APIConfig, timeout: int = 30):
        self.config = config
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.name = self.__class__.__name__.lower().replace('recon', '')
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5, ssl=False)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.get_headers()
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for requests"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    @abstractmethod
    async def search(self, domain: str) -> List[IPCandidate]:
        """Search for IP candidates for the given domain"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this module can be used (API keys, etc.)"""
        pass
    
    def create_candidate(self, ip: str, **kwargs) -> IPCandidate:
        """Create an IP candidate with this module as source"""
        return IPCandidate(
            ip=ip,
            source=self.name,
            **kwargs
        )