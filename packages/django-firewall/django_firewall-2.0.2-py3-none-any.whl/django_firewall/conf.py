"""
Django Firewall Configuration Module.

This module handles all settings for the Django Firewall app.
Settings can be configured in your Django settings.py file with the DJANGO_FIREWALL_ prefix.

Example settings.py configuration:
    DJANGO_FIREWALL_ENABLED = True
    DJANGO_FIREWALL_URL = "http://firewall-host:8080"
    DJANGO_FIREWALL_PORT = 8080
    DJANGO_FIREWALL_REQUEST_TIMEOUT = 5
    DJANGO_FIREWALL_URLS_LIST = ["/admin/.env.*", "/.git/.*"]
    DJANGO_FIREWALL_URL_WHITE_LIST = ["/api/.*"]
"""
import logging
import os
from pathlib import Path
from typing import List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

###############################################################################
# Helper functions to get settings from Django settings or environment
###############################################################################


def __get_bool_setting(name: str, default: bool) -> bool:
    """Get boolean setting from Django settings or environment."""
    # First check Django settings
    django_value = getattr(settings, name, None)
    if django_value is not None:
        if isinstance(django_value, bool):
            return django_value
        if isinstance(django_value, str):
            return django_value.lower() in ("true", "1", "t", "y", "yes")
        return bool(django_value)

    # Then check environment variable
    env_value = os.getenv(name)
    if env_value is not None:
        return env_value.lower() in ("true", "1", "t", "y", "yes")

    # If not found, return the default value
    return default


def __get_str_setting(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get string setting from Django settings or environment."""
    # First check Django settings
    value = getattr(settings, name, None)
    if value is not None:
        return str(value)

    # Then check environment variable
    env_value = os.getenv(name)
    if env_value is not None:
        return env_value

    # If not found, return the default value
    return default


def __get_int_setting(name: str, default: int) -> int:
    """Get integer setting from Django settings or environment."""
    # First check Django settings
    value = getattr(settings, name, None)
    if value is not None:
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.warning(f"{name} must be an integer. Using default: {default}")
            return default

    # Then check environment variable
    env_value = os.getenv(name)
    if env_value is not None:
        try:
            return int(env_value)
        except ValueError:
            logger.warning(f"{name} must be an integer. Using default: {default}")
            return default

    # If not found, return the default value
    return default


def __get_list_setting(name: str, default: Optional[List[str]] = None) -> List[str]:
    """Get list setting from Django settings or environment."""
    # If default is not set, set it to an empty list
    if default is None:
        default = []

    # First check Django settings
    value = getattr(settings, name, None)
    if value is not None:
        if isinstance(value, (list, tuple)):
            return list(value)
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]

    # Then check environment variable
    env_value = os.getenv(name)
    if env_value is not None:
        return [item.strip() for item in env_value.split(",") if item.strip()]

    # If not found, return the default value
    return default


# =============================================================================
# Default Configuration Values
# =============================================================================
# -----------------------------------------------------------------------------
# Default app directory for locating bundled scripts
APP_DIR = Path(__file__).resolve().parent

# Whether the firewall is enabled
ENABLED: bool = __get_bool_setting("DJANGO_FIREWALL_ENABLED", False)

# Also check USE_FIREWALL for backwards compatibility
if not ENABLED:
    ENABLED = __get_bool_setting("USE_FIREWALL", False)

# -----------------------------------------------------------------------------
# URL of the external firewall service
URL: Optional[str] = __get_str_setting("DJANGO_FIREWALL_URL")
if not URL:
    # Backwards compatibility
    URL = __get_str_setting("FIREWALL_URL")
# Ensure the firewall URL does not have a trailing slash
if URL and URL != "":
    URL = URL.rstrip("/")

# -----------------------------------------------------------------------------
# Port for the external firewall service
DEFAULT_PORT: int = 8080
PORT: int = __get_int_setting("DJANGO_FIREWALL_PORT", DEFAULT_PORT)
if PORT == DEFAULT_PORT:
    PORT = __get_int_setting("FIREWALL_PORT", DEFAULT_PORT)

# -----------------------------------------------------------------------------
# Timeout for firewall API requests (seconds)
DEFAULT_REQUEST_TIMEOUT: int = 5
REQUEST_TIMEOUT: int = __get_int_setting("DJANGO_FIREWALL_REQUEST_TIMEOUT", DEFAULT_REQUEST_TIMEOUT)
if REQUEST_TIMEOUT == DEFAULT_REQUEST_TIMEOUT:
    REQUEST_TIMEOUT = __get_int_setting("FIREWALL_REQUEST_TIMEOUT", DEFAULT_REQUEST_TIMEOUT)

# -----------------------------------------------------------------------------
# Script to get the firewall host IP (useful in Docker environments)
GET_HOST_SCRIPT: Optional[str] = __get_str_setting("DJANGO_FIREWALL_GET_HOST_SCRIPT")
if not GET_HOST_SCRIPT:
    GET_HOST_SCRIPT = __get_str_setting("FIREWALL_GET_HOST_SCRIPT")
if not GET_HOST_SCRIPT:
    # Use bundled script as default
    bundled_script = APP_DIR / "bin" / "get_firewall_host.sh"
    if bundled_script.exists():
        GET_HOST_SCRIPT = str(bundled_script)

# -----------------------------------------------------------------------------
# Import default URL lists from endpoint_list
try:
    from django_firewall.endpoint_list import FirewallURLsList, FirewallURLWhiteList
    DEFAULT_URLS_LIST = list(FirewallURLsList)
    DEFAULT_WHITE_LIST = list(FirewallURLWhiteList)
except ImportError:
    DEFAULT_URLS_LIST = []
    DEFAULT_WHITE_LIST = []

# -----------------------------------------------------------------------------
# List of URL patterns to monitor (will trigger blocking)
URLS_LIST: List[str] = __get_list_setting("DJANGO_FIREWALL_URLS_LIST", [])
if not URLS_LIST:
    URLS_LIST = __get_list_setting("FIREWALL_URLS_LIST", [])
# Extend with default malicious URLs
URLS_LIST.extend(url for url in DEFAULT_URLS_LIST if url not in URLS_LIST)

# -----------------------------------------------------------------------------
# List of URL patterns to whitelist (will NOT trigger blocking)
URL_WHITE_LIST: List[str] = __get_list_setting("DJANGO_FIREWALL_URL_WHITE_LIST", [])
if not URL_WHITE_LIST:
    URL_WHITE_LIST = __get_list_setting("FIREWALL_URL_WHITE_LIST", [])
# Extend with default white list
URL_WHITE_LIST.extend(url for url in DEFAULT_WHITE_LIST if url not in URL_WHITE_LIST)


# =============================================================================
# Settings Validation
# =============================================================================

def __validate_settings():
    """Validate firewall settings and log warnings for misconfigurations."""
    if not URL and not GET_HOST_SCRIPT:
        logger.warning(
            "Django Firewall is enabled but neither DJANGO_FIREWALL_URL nor "
            "DJANGO_FIREWALL_GET_HOST_SCRIPT is configured. "
            "The firewall will attempt to auto-detect the host."
        )

    if not URLS_LIST:
        logger.warning(
            "Django Firewall is enabled but DJANGO_FIREWALL_URLS_LIST is empty. "
            "No URLs will be monitored for blocking."
        )


# Validate on import
if ENABLED:
    __validate_settings()
