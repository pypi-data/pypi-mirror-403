"""
Helper utilities for OriginX
"""

import re
import socket
import ipaddress
from typing import List, Optional, Tuple
from urllib.parse import urlparse
import hashlib
import mmh3
import base64

def is_valid_domain(domain: str) -> bool:
    """Validate domain name format"""
    pattern = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    )
    return bool(pattern.match(domain)) and len(domain) <= 253

def is_valid_ip(ip: str) -> bool:
    """Validate IP address format"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def is_private_ip(ip: str) -> bool:
    """Check if IP is in private range"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj.is_private
    except ValueError:
        return False

def normalize_domain(domain: str) -> str:
    """Normalize domain name (remove protocol, www, etc.)"""
    if '://' in domain:
        domain = urlparse(domain).netloc
    
    # Remove port if present
    if ':' in domain:
        domain = domain.split(':')[0]
    
    # Remove www prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    
    return domain.lower().strip()

def calculate_favicon_hash(favicon_data: bytes) -> str:
    """Calculate MurmurHash3 for favicon (Shodan format)"""
    # Base64 encode the favicon data
    b64_data = base64.b64encode(favicon_data).decode()
    
    # Calculate MurmurHash3
    hash_value = mmh3.hash(b64_data)
    
    return str(hash_value)

def extract_ips_from_text(text: str) -> List[str]:
    """Extract IP addresses from text using regex"""
    ip_pattern = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    )
    
    ips = ip_pattern.findall(text)
    return [ip for ip in ips if is_valid_ip(ip) and not is_private_ip(ip)]

def resolve_domain(domain: str) -> List[str]:
    """Resolve domain to IP addresses"""
    try:
        result = socket.getaddrinfo(domain, None)
        ips = list(set([addr[4][0] for addr in result]))
        return [ip for ip in ips if not is_private_ip(ip)]
    except socket.gaierror:
        return []

def get_domain_from_url(url: str) -> str:
    """Extract domain from URL"""
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    parsed = urlparse(url)
    return parsed.netloc.split(':')[0]

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple text similarity score"""
    if not text1 or not text2:
        return 0.0
    
    # Simple Jaccard similarity on words
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def format_duration(seconds: float) -> str:
    """Format duration in human readable format"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename.strip()