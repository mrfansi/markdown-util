"""Unit tests for domain utilities."""

import pytest
from url2md.utils.domain import (
    extract_domain,
    sanitize_domain_name,
    build_domain_path
)

@pytest.mark.parametrize("url,expected", [
    ("https://example.com", ("", "example", "com")),
    ("http://blog.example.com", ("blog", "example", "com")),
    ("https://sub.sub.example.co.uk", ("sub.sub", "example", "co.uk")),
    ("https://localhost:8080", ("", "localhost", "")),
])
def test_extract_domain(url, expected):
    """Test domain extraction from URLs."""
    result = extract_domain(url)
    assert (result.subdomain, result.domain, result.suffix) == expected

@pytest.mark.parametrize("input_name,expected", [
    ("example.com", "example.com"),
    ("sub.example.com", "sub.example.com"),
    ("invalid!name.com", "invalid_name.com"),
    ("UPPER-CASE.com", "upper-case.com"),
    ("with spaces.com", "with_spaces.com"),
    ("trailing-.com", "trailing-com"),
])
def test_sanitize_domain_name(input_name, expected):
    """Test domain name sanitization."""
    assert sanitize_domain_name(input_name) == expected

@pytest.mark.parametrize("url,include_subdomains,expected", [
    ("https://example.com", True, "example.com"),
    ("https://blog.example.com", True, "blog/example.com"),
    ("https://blog.example.com", False, "example.com"),
    ("https://invalid!name.com", True, "invalid_name.com"),
    ("https://localhost:8080", True, "localhost"),
])
def test_build_domain_path(url, include_subdomains, expected):
    """Test domain path generation."""
    result = build_domain_path(
        url,
        include_subdomains=include_subdomains,
        fallback="unknown_domain"
    )
    assert result == expected