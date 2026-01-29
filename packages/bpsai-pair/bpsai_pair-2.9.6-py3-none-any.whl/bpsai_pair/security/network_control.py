"""
Network control for Docker sandbox containers.

This module provides functions for managing network access in
sandbox containers using iptables rules.

Functions:
    setup_network_allowlist: Configure iptables rules to restrict network access

Extracted from sandbox.py as part of EPIC-005 module decomposition.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


def setup_network_allowlist(
    container: "Any",
    allowed_domains: list[str],
) -> None:
    """Set up iptables rules to restrict network to allowed domains.

    This function configures the container's iptables to:
    1. Allow localhost connections
    2. Allow DNS lookups (port 53)
    3. Allow established connections
    4. Allow connections to specified domains
    5. Block all other outbound traffic

    Args:
        container: Docker container to configure
        allowed_domains: List of domains to allow network access to
    """
    # Build iptables commands
    iptables_cmds = []

    # Allow localhost
    iptables_cmds.append("iptables -A OUTPUT -d 127.0.0.0/8 -j ACCEPT")
    iptables_cmds.append("iptables -A OUTPUT -o lo -j ACCEPT")

    # Allow DNS (needed to resolve domains)
    iptables_cmds.append("iptables -A OUTPUT -p udp --dport 53 -j ACCEPT")
    iptables_cmds.append("iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT")

    # Allow established connections
    iptables_cmds.append("iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")

    # Resolve and allow each domain
    for domain in allowed_domains:
        # Use dig to resolve domain to IPs
        resolve_cmd = (
            f"dig +short {domain} | grep -E '^[0-9]+\\.' | "
            f"while read ip; do iptables -A OUTPUT -d $ip -j ACCEPT; done"
        )
        iptables_cmds.append(resolve_cmd)

    # Block all other outbound traffic
    iptables_cmds.append("iptables -A OUTPUT -j REJECT")

    # Execute all commands
    script = " && ".join(iptables_cmds)
    container.exec_run(
        cmd=["sh", "-c", script],
        user="root",
    )

    logger.debug(f"Configured network allowlist for {len(allowed_domains)} domain(s)")
