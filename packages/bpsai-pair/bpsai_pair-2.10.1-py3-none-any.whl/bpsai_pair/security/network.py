"""Network allowlist guard for containment mode.

This module provides network access control for contained autonomy mode,
restricting network access to only allowed domains.
"""

from __future__ import annotations

from urllib.parse import urlparse
from typing import Set


class NetworkRestrictionError(Exception):
    """Raised when network access to blocked domain is attempted.

    This exception indicates that a network request was attempted to a domain
    that is not in the allowlist during containment mode.
    """

    pass


class NetworkGuard:
    """Guard for restricting network access to allowed domains only.

    This class validates URLs against an allowlist of domains. Only URLs
    to allowed domains (or their subdomains) will pass validation.

    Localhost addresses (localhost, 127.0.0.1, ::1) are always allowed
    regardless of the allowlist configuration.

    Attributes:
        allowed: Set of allowed domains (including localhost variants).
    """

    # Localhost addresses that are always allowed
    LOCALHOST_ADDRESSES = {"localhost", "127.0.0.1", "::1"}

    def __init__(self, allowed_domains: list) -> None:
        """Initialize the network guard.

        Args:
            allowed_domains: List of domains to allow (without protocol prefix).
                           Subdomains of allowed domains are also permitted.
        """
        # Store allowed domains as lowercase for case-insensitive matching
        self.allowed: Set[str] = {d.lower().rstrip(".") for d in allowed_domains}
        # Always allow localhost variants
        self.allowed.update(self.LOCALHOST_ADDRESSES)

    def check_url(self, url: str) -> None:
        """Check if a URL is allowed.

        Args:
            url: The URL to check.

        Raises:
            NetworkRestrictionError: If the URL's domain is not in the allowlist.
            ValueError: If the URL cannot be parsed.
        """
        if not url:
            raise ValueError("Empty URL provided")

        parsed = urlparse(url)
        netloc = parsed.netloc

        if not netloc:
            raise ValueError(f"Invalid URL (no network location): {url}")

        # Extract domain from netloc (remove port, auth, brackets for IPv6)
        domain = self._extract_domain(netloc)

        if not self._is_allowed(domain):
            raise NetworkRestrictionError(
                f"Network access to '{domain}' blocked in containment mode.\n"
                f"Allowed domains: {', '.join(sorted(self.allowed))}"
            )

    def _extract_domain(self, netloc: str) -> str:
        """Extract the domain from a network location string.

        Handles:
        - user:pass@host -> host
        - host:port -> host
        - [ipv6]:port -> ipv6 (without brackets)
        - Trailing dots (FQDN notation)

        Args:
            netloc: The network location string from URL parsing.

        Returns:
            The extracted domain, lowercase.
        """
        # Remove authentication info (user:pass@)
        if "@" in netloc:
            netloc = netloc.rsplit("@", 1)[1]

        # Handle IPv6 addresses in brackets
        if netloc.startswith("["):
            # Find the closing bracket
            bracket_end = netloc.find("]")
            if bracket_end != -1:
                # Return the IPv6 address without brackets
                return netloc[1:bracket_end].lower()

        # Remove port number
        if ":" in netloc:
            # Could be IPv6 without brackets, or host:port
            # For host:port, the last colon separates port
            parts = netloc.rsplit(":", 1)
            # Check if the last part looks like a port number
            if parts[1].isdigit():
                netloc = parts[0]

        # Remove trailing dot (FQDN notation)
        domain = netloc.rstrip(".").lower()

        return domain

    def _is_allowed(self, domain: str) -> bool:
        """Check if a domain is in the allowlist (including subdomains).

        Args:
            domain: The domain to check (already lowercase).

        Returns:
            True if the domain or its parent is in the allowlist.
        """
        # Direct match
        if domain in self.allowed:
            return True

        # Subdomain match: check if domain ends with .allowed_domain
        for allowed in self.allowed:
            if domain.endswith(f".{allowed}"):
                return True

        return False
