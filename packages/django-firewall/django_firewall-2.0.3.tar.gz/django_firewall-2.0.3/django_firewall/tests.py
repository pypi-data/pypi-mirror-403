"""
Comprehensive tests for the Django Firewall app including:
- IP validation for SSRF prevention
- block_ip and allow_ip functions
- FirewallMiddleware path monitoring
- Configuration handling
"""
import os
import unittest
from unittest.mock import MagicMock, patch

from django.http import HttpResponse, HttpResponseForbidden
from django.test import RequestFactory, TestCase, override_settings


# Check if firewall is enabled for testing
USE_FIREWALL = os.getenv("DJANGO_FIREWALL_ENABLED", "false").lower() in ["true", "1", "t", "y", "yes"]
if not USE_FIREWALL:
    USE_FIREWALL = os.getenv("USE_FIREWALL", "false").lower() in ["true", "1", "t", "y", "yes"]


class IPValidationTest(TestCase):
    """Tests for IP address validation (SSRF prevention)."""

    def test_valid_ipv4_address(self):
        """Test that valid IPv4 addresses are accepted."""
        from django_firewall.middleware import _is_valid_ip

        self.assertTrue(_is_valid_ip("192.168.1.1"))
        self.assertTrue(_is_valid_ip("8.8.8.8"))
        self.assertTrue(_is_valid_ip("10.0.0.1"))
        self.assertTrue(_is_valid_ip("255.255.255.255"))
        self.assertTrue(_is_valid_ip("0.0.0.0"))

    def test_valid_ipv6_address(self):
        """Test that valid IPv6 addresses are accepted."""
        from django_firewall.middleware import _is_valid_ip

        self.assertTrue(_is_valid_ip("2001:4860:4860::8888"))
        self.assertTrue(_is_valid_ip("::1"))
        self.assertTrue(_is_valid_ip("fe80::1"))

    def test_invalid_ip_addresses(self):
        """Test that invalid IP addresses are rejected (SSRF prevention)."""
        from django_firewall.middleware import _is_valid_ip

        self.assertFalse(_is_valid_ip("not-an-ip"))
        self.assertFalse(_is_valid_ip("localhost"))
        self.assertFalse(_is_valid_ip("example.com"))
        self.assertFalse(_is_valid_ip("http://192.168.1.1"))
        self.assertFalse(_is_valid_ip("192.168.1.1:8080"))

    def test_cidr_not_allowed(self):
        """Test that CIDR notation is not allowed (prevents range attacks)."""
        from django_firewall.middleware import _is_valid_ip

        self.assertFalse(_is_valid_ip("192.168.1.0/24"))
        self.assertFalse(_is_valid_ip("10.0.0.0/8"))

    def test_empty_and_none_values(self):
        """Test that empty and None values are rejected."""
        from django_firewall.middleware import _is_valid_ip

        self.assertFalse(_is_valid_ip(""))
        self.assertFalse(_is_valid_ip(None))
        self.assertFalse(_is_valid_ip("   "))

    def test_whitespace_trimmed(self):
        """Test that whitespace around IP is trimmed."""
        from django_firewall.middleware import _is_valid_ip

        self.assertTrue(_is_valid_ip("  8.8.8.8  "))
        self.assertTrue(_is_valid_ip("\t192.168.1.1\n"))


class HelpersTest(TestCase):
    """Tests for helper functions."""

    def test_get_client_ip_cloudflare(self):
        """Test CloudFlare IP detection."""
        from django_firewall.helpers import get_client_ip

        request = MagicMock()
        request.META = {
            "HTTP_CF_CONNECTING_IP": "1.2.3.4",
            "HTTP_X_FORWARDED_FOR": "5.6.7.8, 9.10.11.12",
            "HTTP_X_REAL_IP": "13.14.15.16",
            "REMOTE_ADDR": "17.18.19.20",
        }

        self.assertEqual(get_client_ip(request), "1.2.3.4")

    def test_get_client_ip_x_forwarded_for(self):
        """Test X-Forwarded-For IP detection."""
        from django_firewall.helpers import get_client_ip

        request = MagicMock()
        request.META = {
            "HTTP_X_FORWARDED_FOR": "1.2.3.4, 5.6.7.8",
            "HTTP_X_REAL_IP": "9.10.11.12",
            "REMOTE_ADDR": "13.14.15.16",
        }

        self.assertEqual(get_client_ip(request), "1.2.3.4")

    def test_get_client_ip_x_real_ip(self):
        """Test X-Real-IP IP detection."""
        from django_firewall.helpers import get_client_ip

        request = MagicMock()
        request.META = {
            "HTTP_X_REAL_IP": "1.2.3.4",
            "REMOTE_ADDR": "5.6.7.8",
        }

        self.assertEqual(get_client_ip(request), "1.2.3.4")

    def test_get_client_ip_remote_addr(self):
        """Test REMOTE_ADDR fallback."""
        from django_firewall.helpers import get_client_ip

        request = MagicMock()
        request.META = {
            "REMOTE_ADDR": "1.2.3.4",
        }

        self.assertEqual(get_client_ip(request), "1.2.3.4")


@unittest.skipUnless(USE_FIREWALL, "Firewall is disabled in settings.")
class BlockIPTest(TestCase):
    """Tests for block_ip function."""

    def test_block_ip_invalid_ip_returns_false(self):
        """Test that invalid IP returns False without making external request."""
        from django_firewall.middleware import block_ip

        result = block_ip("not-an-ip")
        self.assertFalse(result)

    def test_block_ip_localhost_returns_false(self):
        """Test that 'localhost' is rejected."""
        from django_firewall.middleware import block_ip

        result = block_ip("localhost")
        self.assertFalse(result)

    def test_block_ip_empty_returns_false(self):
        """Test that empty string returns False."""
        from django_firewall.middleware import block_ip

        result = block_ip("")
        self.assertFalse(result)

    @patch("django_firewall.middleware.requests.get")
    @patch("django_firewall.conf.URL", "http://localhost:8080")
    def test_block_ip_success(self, mock_get):
        """Test successful IP blocking."""
        from django_firewall.middleware import block_ip

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = block_ip("1.2.3.4")

        self.assertTrue(result)
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        self.assertIn("1.2.3.4", call_url)


@unittest.skipUnless(USE_FIREWALL, "Firewall is disabled in settings.")
class AllowIPTest(TestCase):
    """Tests for allow_ip function."""

    def test_allow_ip_invalid_ip_returns_false(self):
        """Test that invalid IP returns False."""
        from django_firewall.middleware import allow_ip

        result = allow_ip("not-an-ip")
        self.assertFalse(result)

    def test_allow_ip_cidr_returns_false(self):
        """Test that CIDR notation returns False."""
        from django_firewall.middleware import allow_ip

        result = allow_ip("192.168.1.0/24")
        self.assertFalse(result)


class MiddlewareDisabledTest(TestCase):
    """Tests for FirewallMiddleware when disabled."""

    def setUp(self):
        """Set up test environment."""
        self.factory = RequestFactory()

    @override_settings(DJANGO_FIREWALL_ENABLED=False)
    def test_firewall_disabled_passes_through(self):
        """Test that disabled firewall passes requests through."""
        from django_firewall.middleware import FirewallMiddleware

        def dummy_response(request):
            return HttpResponse("OK")

        middleware = FirewallMiddleware(dummy_response)
        request = self.factory.get("/admin/")

        response = middleware(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")


class EndpointListTest(TestCase):
    """Tests for endpoint list functions."""

    def test_firewall_urls_list_not_empty(self):
        """Test that default URL list is not empty."""
        from django_firewall.endpoint_list import FirewallURLsList

        self.assertGreater(len(FirewallURLsList), 0)

    def test_common_attack_patterns_included(self):
        """Test that common attack patterns are included."""
        from django_firewall.endpoint_list import FirewallURLsList

        # Check for common patterns
        patterns_str = " ".join(FirewallURLsList)
        self.assertIn(".env", patterns_str)
        self.assertIn(".git", patterns_str)
        self.assertIn("php", patterns_str)
        self.assertIn("wp-admin", patterns_str)

    def test_build_wildcard_expression(self):
        """Test wildcard expression builder."""
        from django_firewall.endpoint_list import build_wildcard_or_expression

        patterns = ["/admin/.env.*", "/.git/.*"]
        result = build_wildcard_or_expression(patterns)

        self.assertIn("wildcard", result)
        self.assertIn("/admin/.env*", result)
        self.assertIn("/.git/*", result)
