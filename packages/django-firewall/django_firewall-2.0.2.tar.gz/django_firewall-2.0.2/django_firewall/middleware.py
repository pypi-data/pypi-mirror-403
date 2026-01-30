import ipaddress
import logging
import os
import re
import socket
import subprocess
from http import HTTPStatus
from typing import Callable, List, Optional

import requests
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden

from django_firewall import conf
from django_firewall.helpers import get_client_ip
from django_firewall.models import FirewallAPILog, FirewallPathRule

logger = logging.getLogger(__name__)

# Cache timeout for firewall rules (seconds)
FIREWALL_RULES_CACHE_TIMEOUT = 300  # 5 minutes


def _is_valid_ip(ip_address: str) -> bool:
    """
    Validate that ip_address is a valid IPv4 or IPv6 address.

    This function is critical for SSRF prevention - it ensures that only
    valid IP addresses are passed to external firewall services.

    Args:
        ip_address: The IP address string to validate.

    Returns:
        bool: True if the IP address is valid, False otherwise.
    """
    if not ip_address:
        return False
    try:
        ipaddress.ip_address(ip_address.strip())
        return True
    except ValueError:
        return False


def block_ip(ip_address: str) -> bool:
    """
    Block an IP address by calling the external firewall service.

    Args:
        ip_address: The IP address to block.

    Returns:
        bool: True if the IP was blocked successfully, False otherwise.
    """
    # SECURITY: Validate IP address format to prevent SSRF
    if not _is_valid_ip(ip_address):
        logger.warning(f"{__name__}: Invalid IP address format for block: {ip_address}")
        return False

    # Check the firewall URL is configured
    if not conf.URL:
        logger.warning(f"{__name__}: DJANGO_FIREWALL_URL is not configured.")
        return False

    # Call host firewall service to block the IP
    try:
        logger.debug(f"{__name__}: Blocking IP address: {ip_address}...")
        url = f"{conf.URL}/block?ip={ip_address}"
        logger.debug(f"{__name__}: Calling URL: {url}")
        result = requests.get(url, timeout=conf.REQUEST_TIMEOUT)

        # Check if the request was successful
        if result.status_code != HTTPStatus.OK:
            logger.error(f"{__name__}: Failed to block IP {ip_address}: {result.text}")
            return False

        logger.info(f"{__name__}: Blocked IP: {ip_address}")
        return True
    except requests.exceptions.Timeout:
        logger.error(f"{__name__}: Timeout blocking IP {ip_address}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"{__name__}: Failed to block IP {ip_address}: {e}")
        return False
    except Exception as e:
        logger.error(f"{__name__}: Unexpected error blocking IP {ip_address}: {e}")
        return False


def allow_ip(ip_address: str) -> bool:
    """
    Allow an IP address by calling the external firewall service.

    Args:
        ip_address: The IP address to allow.

    Returns:
        bool: True if the IP was allowed successfully, False otherwise.
    """
    # SECURITY: Validate IP address format to prevent SSRF
    if not _is_valid_ip(ip_address):
        logger.warning(f"{__name__}: Invalid IP address format: {ip_address}")
        return False

    # Check the firewall URL is configured
    if not conf.URL:
        logger.warning(f"{__name__}: DJANGO_FIREWALL_URL is not configured.")
        return False

    # Call host firewall service to allow the IP
    try:
        logger.debug(f"{__name__}: Allowing IP address: {ip_address}...")
        url = f"{conf.URL}/allow?ip={ip_address}"
        logger.debug(f"{__name__}: Calling URL: {url}")
        result = requests.get(url, timeout=conf.REQUEST_TIMEOUT)

        # Check if the request was successful
        if result.status_code != HTTPStatus.OK:
            logger.error(f"{__name__}: Failed to allow IP {ip_address}: {result.text}")
            return False

        logger.info(f"{__name__}: Allowed IP: {ip_address}")
        return True
    except requests.exceptions.Timeout:
        logger.error(f"{__name__}: Timeout allowing IP {ip_address}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"{__name__}: Failed to allow IP {ip_address}: {e}")
        return False
    except Exception as e:
        logger.error(f"{__name__}: Unexpected error allowing IP {ip_address}: {e}")
        return False


def get_firewall_rules(rule_type: str = "blacklist") -> List[str]:
    """
    Get firewall rules from database with caching.

    This function loads firewall path rules from the database with a 5-minute cache.
    If the database is empty or unavailable, it falls back to hardcoded settings.

    Args:
        rule_type: 'blacklist' or 'whitelist'

    Returns:
        List of path patterns
    """
    cache_key = f"firewall_{rule_type}_rules"
    rules = cache.get(cache_key)

    if rules is None:
        try:
            # Get enabled rules from database, ordered by priority
            db_rules = FirewallPathRule.objects.filter(
                rule_type=rule_type, enabled=True
            ).order_by("priority", "path_pattern").values_list("path_pattern", flat=True)

            rules = list(db_rules)

            # Fallback to hardcoded rules if database is empty
            if not rules:
                if rule_type == "blacklist":
                    rules = conf.URLS_LIST
                elif rule_type == "whitelist":
                    rules = conf.URL_WHITE_LIST

            # Cache the rules
            cache.set(cache_key, rules, FIREWALL_RULES_CACHE_TIMEOUT)
            logger.debug(
                f"{__name__}: Loaded {len(rules)} {rule_type} rules from database"
            )
        except Exception as e:
            logger.error(
                f"{__name__}: Failed to load {rule_type} rules from database: {e}"
            )
            # Fallback to settings if database query fails
            if rule_type == "blacklist":
                rules = conf.URLS_LIST
            elif rule_type == "whitelist":
                rules = conf.URL_WHITE_LIST
            else:
                rules = []

    return rules


class FirewallMiddleware:
    """
    Django middleware for monitoring and blocking suspicious IP addresses.

    This middleware intercepts requests and checks if the requested URL
    matches any patterns in the monitored URL list. If a match is found,
    the IP address is blocked via the external firewall service and the
    request is denied.

    Configuration is read from Django settings with the DJANGO_FIREWALL_ prefix.

    Example settings.py configuration:
        DJANGO_FIREWALL_ENABLED = True
        DJANGO_FIREWALL_URL = "http://firewall-host:8080"
        DJANGO_FIREWALL_URLS_LIST = ["/admin/.env.*", "/.git/.*"]
        DJANGO_FIREWALL_URL_WHITE_LIST = ["/api/.*"]
    """

    # Class-level flag to track if firewall URL was obtained
    _firewall_initialized: bool = False

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        """
        Initialize the middleware.

        Args:
            get_response: The next middleware or view in the chain.
        """
        self.get_response = get_response

        logger.debug(f"{__name__}: Initializing...")
        logger.debug(f"{__name__}: URLS: {conf.URLS_LIST}")
        logger.debug(f"{__name__}: WHITE_URLS: {conf.URL_WHITE_LIST}")

        # Check if the firewall is enabled
        if not conf.ENABLED:
            logger.debug(f"{__name__}: Firewall is disabled. Skipping initialization.")
            return

        # Check if the firewall URL is already set
        if conf.URL:
            logger.debug(f"{__name__}: Firewall URL is set: {conf.URL}")
            self._firewall_initialized = True
            return

        # Try to obtain the firewall URL via script
        self._initialize_firewall_url()

    def _initialize_firewall_url(self) -> None:
        """
        Initialize the firewall URL by running the host detection script.

        This is useful in Docker environments where the host IP needs to be
        dynamically determined.
        """
        if not conf.GET_HOST_SCRIPT:
            logger.warning(f"{__name__}: No host detection script configured.")
            return

        # Check if script exists
        if not os.path.exists(conf.GET_HOST_SCRIPT):
            logger.warning(
                f"{__name__}: Script not found: {conf.GET_HOST_SCRIPT}. "
                "Ensure the script exists and is executable."
            )
            return

        # Try to obtain the firewall URL via script
        try:
            logger.debug(f"{__name__}: Running host detection script: {conf.GET_HOST_SCRIPT}")
            result = subprocess.run(
                [conf.GET_HOST_SCRIPT],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )

            # Set the firewall URL from the script output
            host_ip = result.stdout.strip()
            if host_ip and _is_valid_ip(host_ip):
                conf.URL = f"http://{host_ip}:{conf.PORT}"
                self._firewall_initialized = True
                logger.debug(f"{__name__}: Firewall URL: {conf.URL}")
                logger.info(f"{__name__}: Initialized successfully.")
            else:
                logger.warning(f"{__name__}: Invalid host IP from script: {host_ip}")

        except FileNotFoundError:
            logger.warning(
                f"{__name__}: Script not found: {conf.GET_HOST_SCRIPT}. "
                "Ensure the script exists and is executable."
            )
        except subprocess.TimeoutExpired:
            logger.warning(f"{__name__}: Script timed out: {conf.GET_HOST_SCRIPT}")
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() if e.stderr else e.stdout.strip()
            logger.warning(f"{__name__}: Script failed: {conf.GET_HOST_SCRIPT}: {err}")
        except Exception as e:
            logger.error(f"{__name__}: Error running script: {conf.GET_HOST_SCRIPT}: {e}")

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Process the request through the firewall middleware.

        Args:
            request: The incoming HTTP request.

        Returns:
            HttpResponse: Either the normal response or HttpResponseForbidden.
        """
        # Check if the firewall is enabled
        if not conf.ENABLED:
            logger.debug(f"{__name__}: Firewall is disabled. Skipping check.")
            return self.get_response(request)

        # Get parameters from the request
        ip_address = get_client_ip(request)
        path = request.get_full_path()
        logger.debug(f"{__name__}: Request from {ip_address}: {path}")

        # Get firewall rules from database (with caching)
        whitelist_rules = get_firewall_rules("whitelist")
        blacklist_rules = get_firewall_rules("blacklist")

        # Check if the path is in the white list URLs (checked first, priority)
        if any(re.match(url, path) for url in whitelist_rules):
            logger.debug(f"{__name__}: Path is whitelisted: {path}")
            return self.get_response(request)

        # Check if the path is in the monitored URLs (blacklist)
        if not any(re.match(url, path) for url in blacklist_rules):
            logger.debug(f"{__name__}: Path not monitored: {path}")
            return self.get_response(request)

        logger.debug(f"{__name__}: Path matches monitored pattern: {path}")

        # Check if the IP address is already in the database
        ip_log = FirewallAPILog.objects.filter(remote_address=ip_address).first()

        # Try to block the IP via external firewall (optional - logs are saved regardless)
        external_block_success = False
        if not ip_log or not ip_log.blocked:
            external_block_success = block_ip(ip_address)
            if not external_block_success:
                logger.debug(
                    f"{__name__}: External firewall block failed for IP: {ip_address} (will still log and block)"
                )

        # Update or create log record (always save the log, even if external firewall fails)
        try:
            if not ip_log:
                logger.debug(f"{__name__}: Creating log for IP: {ip_address}")
                FirewallAPILog.objects.get_or_create(
                    remote_address=ip_address,
                    url=path,
                    defaults={
                        "server_hostname": socket.gethostname(),
                        "blocked": True,
                    },
                )
            else:
                logger.debug(f"{__name__}: Updating log for IP: {ip_address}")
                ip_log.url = path
                ip_log.blocked = True
                ip_log.save(update_fields=["url", "blocked", "updated_at"])

            logger.info(f"{__name__}: Blocked request from {ip_address} to {path}")
        except Exception as e:
            logger.error(f"{__name__}: Failed to log blocked IP: {e}")

        return HttpResponseForbidden("")
