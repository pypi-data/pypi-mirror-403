"""
Configuration management for OriginX
"""

import os
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class APIConfig:
    """API configuration for external services"""
    shodan_key: Optional[str] = None
    censys_id: Optional[str] = None
    censys_secret: Optional[str] = None
    virustotal_key: Optional[str] = None
    securitytrails_key: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        """Load configuration from environment variables"""
        return cls(
            shodan_key=os.getenv('SHODAN_API_KEY'),
            censys_id=os.getenv('CENSYS_API_ID'),
            censys_secret=os.getenv('CENSYS_API_SECRET'),
            virustotal_key=os.getenv('VIRUSTOTAL_API_KEY'),
            securitytrails_key=os.getenv('SECURITYTRAILS_API_KEY')
        )
    
    def get_available_sources(self) -> list:
        """Get list of available API sources based on configured keys"""
        sources = []
        if self.shodan_key:
            sources.append('shodan')
        if self.censys_id and self.censys_secret:
            sources.append('censys')
        if self.virustotal_key:
            sources.append('virustotal')
        if self.securitytrails_key:
            sources.append('securitytrails')
        
        # Always available (no API key required)
        sources.extend(['dns', 'favicon', 'viewdns'])
        
        return sources

@dataclass
class ScanConfig:
    """Scan configuration options"""
    passive_only: bool = False
    fast_mode: bool = False
    deep_scan: bool = False
    verify_origins: bool = True
    detect_waf: bool = True
    confidence_threshold: int = 70
    timeout: int = 30
    max_concurrent: int = 10
    output_format: str = 'table'  # table, json, txt
    output_file: Optional[str] = None