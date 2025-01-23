"""Domain name processing utilities."""

import re
from typing import Optional
import tldextract

def extract_domain(url: str) -> str:
    """
    Extract domain name from URL using tldextract.
    
    Args:
        url: The URL to process
        
    Returns:
        Tuple of (subdomain, domain, suffix)
    """
    extracted = tldextract.extract(url)
    return extracted

def sanitize_domain_name(name: str) -> str:
    """
    Sanitize domain name for filesystem use.
    
    Args:
        name: Domain name to sanitize
        
    Returns:
        Sanitized domain name safe for filesystem
    """
    # Replace special chars with underscores except internal hyphens
    sanitized = re.sub(r'[^\w\-\.]', '_', name)
    # Remove leading/trailing special chars and dots
    sanitized = sanitized.strip('-_')
    # Remove trailing hyphens after dots
    sanitized = re.sub(r'\.-+$', '.', sanitized)
    # Convert to lowercase
    return sanitized.lower()

def build_domain_path(
    url: str, 
    include_subdomains: bool = True,
    fallback: str = "unknown_domain"
) -> str:
    """
    Build filesystem path from domain components.
    
    Args:
        url: Source URL
        include_subdomains: Whether to include subdomains in path
        fallback: Fallback folder name for invalid domains
        
    Returns:
        Filesystem-safe path based on domain
    """
    extracted = extract_domain(url)
    
    # Handle invalid domains
    if not extracted.domain:
        return fallback
        
    # Build path components
    components = []
    if include_subdomains and extracted.subdomain:
        components.append(sanitize_domain_name(extracted.subdomain))
    
    # Handle localhost case
    if extracted.domain == "localhost":
        return "localhost"
        
    domain_part = f"{extracted.domain}.{extracted.suffix}" if extracted.suffix else extracted.domain
    components.append(sanitize_domain_name(domain_part))
    
    return "/".join(components)