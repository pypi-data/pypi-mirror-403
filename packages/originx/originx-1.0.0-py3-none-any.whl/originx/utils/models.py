"""
Data models for OriginX
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class IPCandidate:
    """Represents a potential origin IP address"""
    ip: str
    source: str
    confidence: int = 0
    port: Optional[int] = None
    service: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class VerificationResult:
    """Results from origin IP verification"""
    ip: str
    is_origin: bool
    confidence_score: int
    response_code: Optional[int] = None
    response_time: Optional[float] = None
    cert_match: bool = False
    content_similarity: float = 0.0
    waf_detected: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class WAFInfo:
    """WAF detection information"""
    detected: bool
    provider: Optional[str] = None
    confidence: int = 0
    evidence: List[str] = None
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []

@dataclass
class ScanResult:
    """Complete scan results for a target"""
    target: str
    waf_info: WAFInfo
    candidates: List[IPCandidate]
    verified_origins: List[VerificationResult]
    scan_duration: float
    timestamp: datetime
    sources_used: List[str]
    
    def get_high_confidence_origins(self, threshold: int = 80) -> List[VerificationResult]:
        """Get origins with confidence above threshold"""
        return [
            result for result in self.verified_origins 
            if result.confidence_score >= threshold and result.is_origin
        ]
    
    def get_likely_origins(self) -> List[VerificationResult]:
        """Get most likely origin servers"""
        return sorted(
            [r for r in self.verified_origins if r.is_origin],
            key=lambda x: x.confidence_score,
            reverse=True
        )[:5]