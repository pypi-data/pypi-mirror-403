#!/usr/bin/env python3
"""Branding configuration for white-label integration.

This module provides configurable branding for socialia, allowing parent
packages (e.g., scitex.social) to rebrand and use their own env var prefix.

Environment Variables
---------------------
SOCIALIA_BRAND : str
    Package name shown in docs (default: "socialia")
SOCIALIA_ENV_PREFIX : str
    Environment variable prefix (default: "SOCIALIA")

Usage
-----
Parent package sets env vars before importing:

    # scitex/social/__init__.py
    import os
    os.environ["SOCIALIA_BRAND"] = "scitex.social"
    os.environ["SOCIALIA_ENV_PREFIX"] = "SCITEX"
    from socialia import *

Then env vars like SCITEX_X_CONSUMER_KEY will be used.
"""

import os
from typing import Optional

# Read branding from environment
BRAND_NAME = os.environ.get("SOCIALIA_BRAND", "socialia")
ENV_PREFIX = os.environ.get("SOCIALIA_ENV_PREFIX", "SOCIALIA")

# Original values (for reference/restoration)
_ORIGINAL_NAME = "socialia"
_ORIGINAL_PREFIX = "SOCIALIA"


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with brand prefix priority.

    Lookup order:
    1. {ENV_PREFIX}_{key} (e.g., SCITEX_X_CONSUMER_KEY when branded)
    2. SOCIALIA_{key} (always as fallback)
    3. {key} (unprefixed)
    4. default

    Parameters
    ----------
    key : str
        Environment variable name without prefix (e.g., "X_CONSUMER_KEY")
    default : str, optional
        Default value if not found

    Returns
    -------
    str or None
        Environment variable value or default
    """
    # Branded prefix (may be SCITEX or custom)
    if ENV_PREFIX != _ORIGINAL_PREFIX:
        value = os.environ.get(f"{ENV_PREFIX}_{key}")
        if value:
            return value

    # Always try SOCIALIA_ as fallback
    value = os.environ.get(f"SOCIALIA_{key}")
    if value:
        return value

    # Unprefixed
    value = os.environ.get(key)
    if value:
        return value

    return default


def get_env_var_name(key: str) -> str:
    """Get the branded environment variable name for documentation.

    Parameters
    ----------
    key : str
        Variable name without prefix

    Returns
    -------
    str
        Full variable name with brand prefix
    """
    return f"{ENV_PREFIX}_{key}"


def get_mcp_server_name() -> str:
    """Get the MCP server name based on branding.

    Returns
    -------
    str
        Server name for MCP registration.
    """
    return BRAND_NAME.replace(".", "-")


# EOF
