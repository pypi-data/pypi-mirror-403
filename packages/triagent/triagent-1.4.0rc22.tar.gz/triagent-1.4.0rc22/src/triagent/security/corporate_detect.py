"""Detect corporate device environment.

This module provides platform-specific detection of corporate environments
using DNS domains, Kerberos realms, Azure AD tenant IDs, and MDM enrollment.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CorporateInfo:
    """Information about detected corporate environment."""

    type: str  # "DNS", "Kerberos", "AzureAD", "MDM"
    identifier: str  # The detected value
    platform: str  # sys.platform value


# Non-corporate domain suffixes to reject
NON_CORPORATE_SUFFIXES = [
    "local",
    "home",
    "lan",
    "localdomain",
    "workgroup",
    "mshome.net",
    "internal",
    "compute.internal",
]


def detect_corporate_environment() -> CorporateInfo | None:
    """Detect corporate environment using platform-specific methods.

    Returns CorporateInfo if corporate device detected, None otherwise.
    Priority order:
        1. DNS domain (cross-platform, most reliable)
        2. Kerberos realm (cross-platform)
        3. Azure AD tenant (Windows only)
        4. MDM server domain (Mac only)
    """
    platform = sys.platform

    # Try DNS domain first (most reliable cross-platform)
    dns_domain = _get_dns_domain()
    if dns_domain and _is_corporate_domain(dns_domain):
        return CorporateInfo("DNS", dns_domain.lower(), platform)

    # Try Kerberos realm
    kerberos_realm = _get_kerberos_realm()
    if kerberos_realm:
        return CorporateInfo("Kerberos", kerberos_realm.upper(), platform)

    # Platform-specific fallbacks
    if platform == "win32":
        azure_tenant = _get_azure_ad_tenant()
        if azure_tenant:
            return CorporateInfo("AzureAD", azure_tenant, platform)

    elif platform == "darwin":
        mdm_domain = _get_mdm_server_domain()
        if mdm_domain and _is_corporate_domain(mdm_domain):
            return CorporateInfo("MDM", mdm_domain.lower(), platform)

    return None


def _get_dns_domain() -> str | None:
    """Get DNS search domain."""
    if sys.platform == "win32":
        return _get_dns_domain_windows()
    else:
        return _get_dns_domain_unix()


def _get_dns_domain_windows() -> str | None:
    """Get DNS domain on Windows from USERDNSDOMAIN environment variable."""
    domain = os.environ.get("USERDNSDOMAIN")
    if domain and domain.upper() != "WORKGROUP":
        return domain
    return None


def _get_dns_domain_unix() -> str | None:
    """Get DNS domain on Unix/Mac from /etc/resolv.conf."""
    resolv_conf = Path("/etc/resolv.conf")
    if not resolv_conf.exists():
        return None

    try:
        content = resolv_conf.read_text()
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("search "):
                domains = line.split()[1:]
                if domains:
                    return domains[0]
            elif line.startswith("domain "):
                parts = line.split()
                if len(parts) > 1:
                    return parts[1]
    except (OSError, IndexError):
        pass
    return None


def _get_kerberos_realm() -> str | None:
    """Get Kerberos realm from current tickets."""
    try:
        result = subprocess.run(
            ["klist"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        # Try to find principal in output
        match = re.search(r"Principal:\s*\S+@(\S+)", result.stdout, re.IGNORECASE)
        if match:
            return match.group(1)

        # Alternative: look for krbtgt ticket
        match = re.search(r"krbtgt/([^@\s]+)@", result.stdout)
        if match:
            return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _get_azure_ad_tenant() -> str | None:
    """Get Azure AD tenant ID (Windows only)."""
    if sys.platform != "win32":
        return None

    try:
        result = subprocess.run(
            ["dsregcmd", "/status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        match = re.search(
            r"TenantId\s*:\s*([a-f0-9-]+)", result.stdout, re.IGNORECASE
        )
        if match:
            return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _get_mdm_server_domain() -> str | None:
    """Get MDM server domain (Mac only)."""
    if sys.platform != "darwin":
        return None

    try:
        result = subprocess.run(
            ["profiles", "status", "-type", "enrollment"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None

        match = re.search(r"MDM server:\s*https?://([^/\s]+)", result.stdout)
        if match:
            return match.group(1)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def _is_corporate_domain(domain: str) -> bool:
    """Check if domain appears to be corporate (not personal).

    Args:
        domain: Domain name to check

    Returns:
        True if domain appears to be corporate, False otherwise
    """
    domain_lower = domain.lower()

    # Reject known non-corporate suffixes
    for suffix in NON_CORPORATE_SUFFIXES:
        if domain_lower == suffix or domain_lower.endswith(f".{suffix}"):
            return False

    # Require at least one dot (real domain)
    if "." not in domain:
        return False

    return True
